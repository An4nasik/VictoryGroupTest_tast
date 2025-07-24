from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.filters import Filter
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from models.models import User
from utils.logger import get_logger

logger = get_logger(__name__)
class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, session_pool):
        super().__init__()
        self.session_pool = session_pool
    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        async with self.session_pool() as session:
            data["session"] = session
            return await handler(event, data)
class RoleFilter(Filter):
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles
    async def __call__(self, message: Message, session: AsyncSession) -> bool:
        query = (
            select(User)
            .options(selectinload(User.role))
            .filter(User.telegram_id == message.from_user.id)
        )
        result = await session.execute(query)
        user: User | None = result.scalar_one_or_none()
        if user and user.role and user.role.name in self.allowed_roles:
            return True
        logger.warning(
            f"Пользователь {message.from_user.id} (роль: {user.role.name if user and user.role else 'None'}) "
            f"попытался выполнить команду, требующую одну из ролей: {self.allowed_roles}"
        )
        return False
class IsAdmin(RoleFilter):
    def __init__(self):
        super().__init__(["admin"])
class IsModerator(RoleFilter):
    def __init__(self):
        super().__init__(
            ["moderator", "admin"]
        )
