"""Celery tasks for court decision parsing."""

import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def parse_court_decision(self, decision_id: str):
    """Parse a single court decision through the 3-level hybrid pipeline.

    Level 1: Rule-based parser (fast, ~80% of decisions)
    Level 2: Local LLM (MamayLM) for complex cases
    Level 3: Claude API fallback for NEEDS_REVIEW (confidence < 0.65)
    """
    from app.parsers.decision_parser import DecisionParserPipeline

    try:
        pipeline = DecisionParserPipeline()
        result = pipeline.parse(decision_id)
        logger.info("Parsed decision %s: confidence=%.2f method=%s",
                     decision_id, result["confidence"], result["method"])
        return result
    except Exception as exc:
        logger.error("Failed to parse decision %s: %s", decision_id, exc)
        raise self.retry(exc=exc)


@celery_app.task
def batch_parse_decisions(decision_ids: list[str]):
    """Parse multiple decisions in batch."""
    results = []
    for did in decision_ids:
        result = parse_court_decision.delay(did)
        results.append(result.id)
    return {"queued": len(results), "task_ids": results}


@celery_app.task
def sync_new_decisions():
    """Daily task: fetch new decisions from ЄДРСР for tracked cases."""
    logger.info("Starting daily court decisions sync...")
    # TODO: Implement EDRSR API integration
    # 1. Get all active court cases
    # 2. Query EDRSR for new decisions/rulings
    # 3. Parse any new documents found
    logger.info("Daily sync completed")
    return {"synced": 0}
