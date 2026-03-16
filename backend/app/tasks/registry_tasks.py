"""Celery tasks for registry checks."""

import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=120)
def check_debtor_registries(self, debtor_id: str, registry_types: list[str] | None = None):
    """Check a debtor against Ukrainian open registries.

    Registries: EDR, DRORM (real estate), ASVP (enforcement),
    court registry, bankruptcy, wanted, sanctions, debtors.
    """
    try:
        logger.info("Checking registries for debtor %s", debtor_id)
        # TODO: Implement individual registry API calls
        return {"debtor_id": debtor_id, "checked": registry_types or "all"}
    except Exception as exc:
        logger.error("Registry check failed for %s: %s", debtor_id, exc)
        raise self.retry(exc=exc)


@celery_app.task
def batch_registry_update():
    """Daily task: update registry info for all active debtors."""
    logger.info("Starting daily batch registry update...")
    # TODO: Get all active debtors and queue individual checks
    logger.info("Batch registry update completed")
    return {"updated": 0}
