from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from mitonexus.config import get_settings

settings = get_settings()
celery_app = Celery(
    "mitonexus",
    broker=str(settings.redis_url),
    backend=str(settings.redis_url),
    include=["mitonexus.tasks.indexing"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    task_soft_time_limit=3300,
)

celery_app.conf.beat_schedule = {
    "index-biorxiv-daily": {
        "task": "mitonexus.tasks.indexing.index_biorxiv",
        "schedule": crontab(hour=2, minute=0),
    },
    "index-medrxiv-daily": {
        "task": "mitonexus.tasks.indexing.index_medrxiv",
        "schedule": crontab(hour=2, minute=30),
    },
    "index-pubmed-daily": {
        "task": "mitonexus.tasks.indexing.index_pubmed",
        "schedule": crontab(hour=3, minute=0),
    },
    "index-europepmc-weekly": {
        "task": "mitonexus.tasks.indexing.index_europepmc",
        "schedule": crontab(hour=4, minute=0, day_of_week=0),
    },
    "index-clinicaltrials-weekly": {
        "task": "mitonexus.tasks.indexing.index_clinical_trials",
        "schedule": crontab(hour=5, minute=0, day_of_week=1),
    },
    "refresh-mitocarta-monthly": {
        "task": "mitonexus.tasks.indexing.refresh_mitocarta",
        "schedule": crontab(hour=6, minute=0, day_of_month=1),
    },
}
