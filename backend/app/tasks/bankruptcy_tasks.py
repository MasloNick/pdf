"""Celery tasks for bankruptcy checks with alerts."""

import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=120)
def check_bankruptcy(self, debtor_id: str):
    """Check single debtor bankruptcy status."""
    try:
        logger.info("Checking bankruptcy for debtor %s", debtor_id)
        # TODO: Query bankruptcy registry API
        return {"debtor_id": debtor_id, "status": "no_records"}
    except Exception as exc:
        logger.error("Bankruptcy check failed for %s: %s", debtor_id, exc)
        raise self.retry(exc=exc)


@celery_app.task
def batch_bankruptcy_check():
    """Daily task: batch check all active debtors for bankruptcy.

    If bankruptcy found → set alert_sent=False so dashboard shows alert.
    """
    logger.info("Starting daily batch bankruptcy check...")
    # TODO: Get all active debtors, check each, create BankruptcyCheck records
    # Flag new bankruptcies with alert_sent=False
    logger.info("Batch bankruptcy check completed")
    return {"checked": 0, "new_bankruptcies": 0}
