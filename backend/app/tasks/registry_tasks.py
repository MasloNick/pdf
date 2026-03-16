"""Celery tasks for registry checks and bankruptcy monitoring."""

import logging

from sqlalchemy import select

from app.core.database import SyncSessionLocal
from app.models.debtor import Debtor
from app.models.registry_check import BankruptcyAlert, RegistryCheck
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.registry_tasks.check_debtor_registries")
def check_debtor_registries(self, debtor_id: int, registries: list[str] | None = None):
    """Check a single debtor against specified registries."""
    registries = registries or ["edr", "court_registry", "enforcement", "bankruptcy"]

    with SyncSessionLocal() as db:
        debtor = db.execute(select(Debtor).where(Debtor.id == debtor_id)).scalar_one_or_none()
        if not debtor:
            logger.warning("Debtor %d not found", debtor_id)
            return {"status": "error", "reason": "debtor_not_found"}

        results = {}
        for registry_name in registries:
            check = RegistryCheck(
                debtor_id=debtor_id,
                registry_name=registry_name,
                status="success",
                has_match=False,
                result_summary="Check completed — no match found (stub)",
            )
            # TODO: Implement actual registry API calls per registry type
            db.add(check)
            results[registry_name] = "checked"

        db.commit()
        return {"debtor_id": debtor_id, "results": results}


@celery_app.task(bind=True, name="app.tasks.registry_tasks.batch_bankruptcy_check")
def batch_bankruptcy_check(self):
    """Nightly batch check of all active debtors for bankruptcy status."""
    with SyncSessionLocal() as db:
        debtors = db.execute(
            select(Debtor).where(Debtor.status == "active", Debtor.is_bankrupt.is_(False))
        ).scalars().all()

        checked = 0
        alerts = 0
        for debtor in debtors:
            # TODO: Call real bankruptcy registry API
            check = RegistryCheck(
                debtor_id=debtor.id,
                registry_name="bankruptcy",
                status="success",
                has_match=False,
                result_summary="No bankruptcy found (stub)",
            )
            db.add(check)
            checked += 1

        db.commit()
        logger.info("Bankruptcy check complete: %d checked, %d alerts", checked, alerts)
        return {"checked": checked, "alerts": alerts}


@celery_app.task(bind=True, name="app.tasks.registry_tasks.batch_registry_update")
def batch_registry_update(self):
    """Nightly update of registry data for all active debtors."""
    with SyncSessionLocal() as db:
        debtors = db.execute(select(Debtor).where(Debtor.status == "active")).scalars().all()
        for debtor in debtors:
            check_debtor_registries.delay(debtor.id)
        return {"queued": len(debtors)}
