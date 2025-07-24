import asyncio

from aiogram import Bot

from services.newsletter_service import NewsletterService
from utils.logger import get_logger

logger = get_logger(__name__)
class NewsletterScheduler:
    def __init__(self, bot: Bot, check_interval: int = 60):
        self.bot = bot
        self.check_interval = check_interval
        self.newsletter_service = NewsletterService(bot)
        self.running = False
        self._task = None
    async def start(self):
        if self.running:
            logger.warning("Планировщик уже запущен")
            return
        self.running = True
        self._task = asyncio.create_task(self._run_scheduler())
        logger.info(
            f"Планировщик рассылок запущен с интервалом {self.check_interval} секунд"
        )
    async def stop(self):
        if not self.running:
            return
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Планировщик рассылок остановлен")
    async def _run_scheduler(self):
        logger.info("Планировщик рассылок начал работу")
        while self.running:
            try:
                await self.newsletter_service.process_pending_newsletters()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                logger.info("Планировщик был отменен")
                break
            except Exception as e:
                logger.error(f"Ошибка в планировщике рассылок: {e}")
                await asyncio.sleep(self.check_interval)
        logger.info("Планировщик рассылок завершил работу")
scheduler = None
async def start_newsletter_scheduler(bot: Bot):
    global scheduler
    if scheduler is None:
        scheduler = NewsletterScheduler(
            bot, check_interval=60
        )
    await scheduler.start()
async def stop_newsletter_scheduler():
    global scheduler
    if scheduler:
        await scheduler.stop()
