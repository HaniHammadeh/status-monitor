from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from . import models, schemas


def get_services(db: Session, active_only: bool = False) -> list[models.Service]:
    query = db.query(models.Service)
    if active_only:
        query = query.filter(models.Service.is_active.is_(True))
    return query.order_by(models.Service.id).all()


def get_service(db: Session, service_id: int) -> Optional[models.Service]:
    return db.query(models.Service).filter(models.Service.id == service_id).first()


def create_service(db: Session, service: schemas.ServiceCreate) -> models.Service:
    db_service = models.Service(**service.model_dump())
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service


def delete_service(db: Session, service_id: int) -> bool:
    db_service = get_service(db, service_id)
    if not db_service:
        return False
    db.delete(db_service)
    db.commit()
    return True


def record_check(
    db: Session,
    service_id: int,
    status: models.CheckStatus,
    status_code: Optional[int],
    response_time_ms: Optional[float],
    error_message: Optional[str] = None,
) -> models.Check:
    check = models.Check(
        service_id=service_id,
        status=status,
        status_code=status_code,
        response_time_ms=response_time_ms,
        error_message=error_message,
    )
    db.add(check)
    db.commit()
    db.refresh(check)
    return check


def get_recent_checks(db: Session, service_id: int, limit: int = 50) -> list[models.Check]:
    return (
        db.query(models.Check)
        .filter(models.Check.service_id == service_id)
        .order_by(models.Check.checked_at.desc())
        .limit(limit)
        .all()
    )


def get_latest_check(db: Session, service_id: int) -> Optional[models.Check]:
    return (
        db.query(models.Check)
        .filter(models.Check.service_id == service_id)
        .order_by(models.Check.checked_at.desc())
        .first()
    )


def get_uptime_percent(db: Session, service_id: int, hours: int = 24) -> float:
    since = datetime.utcnow() - timedelta(hours=hours)
    total = (
        db.query(func.count(models.Check.id))
        .filter(models.Check.service_id == service_id, models.Check.checked_at >= since)
        .scalar()
    )
    if not total:
        return 100.0
    up = (
        db.query(func.count(models.Check.id))
        .filter(
            models.Check.service_id == service_id,
            models.Check.checked_at >= since,
            models.Check.status == models.CheckStatus.up,
        )
        .scalar()
    )
    return round((up / total) * 100, 2)


def get_active_incident(db: Session, service_id: int) -> Optional[models.Incident]:
    return (
        db.query(models.Incident)
        .filter(
            models.Incident.service_id == service_id,
            models.Incident.status == models.IncidentStatus.ongoing,
        )
        .first()
    )


def open_incident(db: Session, service_id: int) -> models.Incident:
    incident = models.Incident(service_id=service_id, status=models.IncidentStatus.ongoing)
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


def resolve_incident(db: Session, incident: models.Incident) -> models.Incident:
    incident.status = models.IncidentStatus.resolved
    incident.resolved_at = datetime.utcnow()
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident
