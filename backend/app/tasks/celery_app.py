"""Celery application configuration."""

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "courtcrm",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Kyiv",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Autodiscover tasks
celery_app.autodiscover_tasks(["app.tasks"])

# Scheduled tasks (02:00–04:00 Kyiv time)
celery_app.conf.beat_schedule = {
    "daily-bankruptcy-check": {
        "task": "app.tasks.registry_tasks.batch_bankruptcy_check",
        "schedule": crontab(hour=2, minute=0),
    },
    "daily-registry-update": {
        "task": "app.tasks.registry_tasks.batch_registry_update",
        "schedule": crontab(hour=3, minute=0),
    },
    "daily-court-decisions-sync": {
        "task": "app.tasks.parsing_tasks.sync_court_decisions",
        "schedule": crontab(hour=2, minute=30),
    },
}
