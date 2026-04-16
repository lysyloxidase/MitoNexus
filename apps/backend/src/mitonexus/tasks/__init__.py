"""Task package."""

from mitonexus.tasks.analysis import run_analysis_workflow
from mitonexus.tasks.celery_app import celery_app

app = celery_app

__all__ = ["app", "celery_app", "run_analysis_workflow"]
