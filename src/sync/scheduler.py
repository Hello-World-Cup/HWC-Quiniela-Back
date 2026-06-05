import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.core.config import settings
from src.core.database import AsyncSessionLocal
from src.sync.client import ApiFootballClient
from src.sync.service import SyncService

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="UTC")


async def _daily_sync_job() -> None:
    if not settings.api_football_key:
        return
    async with AsyncSessionLocal() as db:
        try:
            client = ApiFootballClient(settings.api_football_key)
            summary = await SyncService(db, client).sync_pending_matches()
            logger.info("Sync diario completado: %s", summary)
        except Exception:
            logger.exception("Sync diario falló")


def start_scheduler() -> None:
    if not settings.api_football_key:
        logger.warning("API_FOOTBALL_KEY no configurado — sync scheduler deshabilitado")
        return
    scheduler.add_job(
        _daily_sync_job,
        trigger=CronTrigger(
            hour=settings.sync_cron_hour,
            minute=settings.sync_cron_minute,
        ),
        id="daily_api_football_sync",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    logger.info(
        "Sync scheduler iniciado — corre diariamente a las %02d:%02d UTC",
        settings.sync_cron_hour,
        settings.sync_cron_minute,
    )


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Sync scheduler detenido")
