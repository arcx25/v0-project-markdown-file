"""Celery application configuration."""

from celery import Celery
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "vault_workers",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.payment_monitor",
        "app.workers.cleanup",
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "monitor-payments": {
        "task": "app.workers.payment_monitor.monitor_pending_payments",
        "schedule": 60.0,  # Run every 60 seconds
    },
    "cleanup-expired": {
        "task": "app.workers.cleanup.cleanup_expired_data",
        "schedule": 3600.0,  # Run every hour
    },
}
