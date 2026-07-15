from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from prometheus_client import CONTENT_TYPE_LATEST, Gauge, generate_latest
from sqlalchemy.orm import Session
import os
import socket
from . import crud, models, schemas
from .database import Base, engine, get_db

# For a portfolio/demo project, creating tables on startup keeps things
# simple. In a production app you'd use Alembic migrations instead so
# schema changes are versioned and reversible.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Status Monitor")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

service_up_gauge = Gauge(
    "status_monitor_service_up", "1 if the service's last check was up, else 0", ["service_name"]
)


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/health")
def health():
    """Liveness/readiness probe target for Docker/Kubernetes."""
    return {"status": "ok"}


@app.get("/api/services", response_model=list[schemas.ServiceRead])
def list_services(db: Session = Depends(get_db)):
    return crud.get_services(db)


@app.post("/api/services", response_model=schemas.ServiceRead, status_code=201)
def add_service(service: schemas.ServiceCreate, db: Session = Depends(get_db)):
    return crud.create_service(db, service)


@app.delete("/api/services/{service_id}", status_code=204)
def remove_service(service_id: int, db: Session = Depends(get_db)):
    if not crud.delete_service(db, service_id):
        raise HTTPException(status_code=404, detail="Service not found")


@app.get("/api/services/{service_id}/checks", response_model=list[schemas.CheckRead])
def service_checks(service_id: int, limit: int = 50, db: Session = Depends(get_db)):
    return crud.get_recent_checks(db, service_id, limit)


@app.get("/api/status", response_model=list[schemas.ServiceStatus])
def status_summary(db: Session = Depends(get_db)):
    """Everything the dashboard needs in one call: current status, uptime,
    and a short history strip per service."""
    results = []
    for service in crud.get_services(db):
        latest = crud.get_latest_check(db, service.id)
        recent = crud.get_recent_checks(db, service.id, limit=24)

        results.append(
            schemas.ServiceStatus(
                service=service,
                current_status=latest.status.value if latest else "unknown",
                last_checked_at=latest.checked_at if latest else None,
                response_time_ms=latest.response_time_ms if latest else None,
                uptime_percent_24h=crud.get_uptime_percent(db, service.id),
                recent_history=[c.status.value for c in reversed(recent)],
            )
        )
    return results


@app.get("/metrics")
def metrics(db: Session = Depends(get_db)):
    """Prometheus scrapes this. Gauges are refreshed from the DB on each
    scrape rather than on each check, since the API and worker are
    separate processes with separate in-memory metric registries."""
    for service in crud.get_services(db):
        latest = crud.get_latest_check(db, service.id)
        is_up = 1 if latest and latest.status == models.CheckStatus.up else 0
        service_up_gauge.labels(service_name=service.name).set(is_up)
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/version")
def version():
    return {
        "application": "color-app",
        "version": os.getenv("APP_VERSION", "unknown"),
        "commit": os.getenv("GIT_COMMIT", "unknown"),
        "build_date": os.getenv("BUILD_DATE", "unknown"),
        "hostname": socket.gethostname()
    }

