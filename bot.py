import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from decouple import config
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from handlers import admin, common, moderator, register
from middlewares.auth import DbSessionMiddleware
from models.database import AsyncSessionLocal, Base, engine
from models.models import Role
from services.scheduler import start_newsletter_scheduler, stop_newsletter_scheduler
from services.user_service import get_role_by_name
from utils.logger import get_logger

ROLES = ["user", "moderator", "admin"]
logger = get_logger(__name__)
async def create_default_roles(session: AsyncSession):
    for role_name in ROLES:
        existing_role = await get_role_by_name(session, role_name)
        if not existing_role:
            new_role = Role(name=role_name)
            session.add(new_role)
            logger.info(f"Создана роль по умолчанию: {role_name}")
    await session.commit()
async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        await create_default_roles(session)
    redis_url = config("REDIS_URL", default="redis://redis:6379/0")
    logger.info(f"Подключение к Redis: {redis_url}")
    redis = Redis.from_url(redis_url, decode_responses=True)
    storage = RedisStorage(redis)
    bot = Bot(
        token=config("BOT_TOKEN"),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=storage)
    dp.update.middleware(DbSessionMiddleware(session_pool=AsyncSessionLocal))
    dp.include_router(common.router)
    dp.include_router(admin.router)
    dp.include_router(moderator.router)
    dp.include_router(register.router)
    logger.info("Запуск планировщика рассылок...")
    await start_newsletter_scheduler(bot)
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Бот запущен и готов к работе!")
        await dp.start_polling(bot)
    finally:
        logger.info("Остановка планировщика рассылок...")
        await stop_newsletter_scheduler()
        await redis.close()
if __name__ == "__main__":
    logger.info("Запуск бота...")
    asyncio.run(main())
