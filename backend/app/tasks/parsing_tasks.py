"""Celery tasks for court decision parsing."""

import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.parsing_tasks.parse_court_decision")
def parse_court_decision(self, decision_id: int):
    """Parse a single court decision using the hybrid AI pipeline."""
    from app.ai_parser.pipeline import parse_decision_by_id

    return parse_decision_by_id(decision_id)


@celery_app.task(bind=True, name="app.tasks.parsing_tasks.sync_court_decisions")
def sync_court_decisions(self):
    """Nightly sync: fetch new decisions from court registry and parse them."""
    # TODO: Implement court registry API integration
    logger.info("Court decisions sync started (stub)")
    return {"synced": 0, "parsed": 0}
