"""APScheduler configuration for nightly cron jobs."""

from apscheduler.schedulers.asyncio import AsyncIOScheduler


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Europe/Kyiv")

    # Nightly tasks (02:00-04:00)
    # scheduler.add_job(sync_erb_registry, "cron", hour=2, minute=0)
    # scheduler.add_job(check_bankruptcies, "cron", hour=2, minute=30)
    # scheduler.add_job(sync_court_decisions, "cron", hour=3, minute=0)
    # scheduler.add_job(create_backup, "cron", hour=4, minute=0)

    return scheduler
