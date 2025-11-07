from celery import Celery
from celery.schedules import crontab

celery = Celery(
    "background_jobs",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

celery.conf.task_routes = {
    "tasks.*": {"queue": "celery"},
}

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

import tasks


celery.conf.beat_schedule = {
    "run-order-summary-every-30-minutes": {
        "task": "tasks.get_order_summary",
        "schedule": crontab(minute="*/30"),
    },
}
