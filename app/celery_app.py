from celery import Celery

from .config import settings

celery_app = Celery(
    "status_monitor",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks"],
)

celery_app.conf.beat_schedule = {
    "run-health-checks": {
        "task": "app.tasks.run_health_checks",
        "schedule": settings.health_check_interval_seconds,
    }
}
celery_app.conf.timezone = "UTC"
celery_app.conf.task_default_queue = "status_monitor"
