import time

import httpx
import redis

from . import crud, models
from .celery_app import celery_app
from .config import settings
from .database import SessionLocal

redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)


@celery_app.task(name="app.tasks.run_health_checks")
def run_health_checks():
    """Beat fires this on a schedule. It fans out one task per active service
    so a slow/hanging service can't delay the others."""
    db = SessionLocal()
    try:
        for service in crud.get_services(db, active_only=True):
            check_service.delay(service.id)
    finally:
        db.close()


@celery_app.task(name="app.tasks.check_service", max_retries=0)
def check_service(service_id: int):
    db = SessionLocal()
    try:
        service = crud.get_service(db, service_id)
        if not service:
            return

        status, status_code, response_time_ms, error_message = _probe(service)

        crud.record_check(
            db,
            service_id=service.id,
            status=status,
            status_code=status_code,
            response_time_ms=response_time_ms,
            error_message=error_message,
        )
        _sync_incident(db, service, status)
        _cache_latest_status(service.id, status, response_time_ms)
    finally:
        db.close()


def _probe(service: models.Service):
    """Makes the actual HTTP call. Returns (status, status_code, response_time_ms, error)."""
    start = time.monotonic()
    try:
        response = httpx.request(
            service.method, service.url, timeout=10.0, follow_redirects=True
        )
        response_time_ms = round((time.monotonic() - start) * 1000, 2)
        if response.status_code == service.expected_status:
            return models.CheckStatus.up, response.status_code, response_time_ms, None
        error = f"expected {service.expected_status}, got {response.status_code}"
        return models.CheckStatus.down, response.status_code, response_time_ms, error
    except httpx.RequestError as exc:
        response_time_ms = round((time.monotonic() - start) * 1000, 2)
        return models.CheckStatus.down, None, response_time_ms, str(exc)


def _sync_incident(db, service: models.Service, status: models.CheckStatus):
    active_incident = crud.get_active_incident(db, service.id)
    if status == models.CheckStatus.down and not active_incident:
        crud.open_incident(db, service.id)
    elif status == models.CheckStatus.up and active_incident:
        crud.resolve_incident(db, active_incident)


def _cache_latest_status(service_id: int, status: models.CheckStatus, response_time_ms: float):
    """Redis holds only the latest snapshot per service, so the dashboard's
    frequent polling doesn't have to hit Postgres every time."""
    redis_client.hset(
        f"service:{service_id}:status",
        mapping={"status": status.value, "response_time_ms": response_time_ms or 0},
    )
    redis_client.expire(f"service:{service_id}:status", 300)
