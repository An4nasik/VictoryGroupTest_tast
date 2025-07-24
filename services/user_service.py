from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models.models import Role, User
from utils.logger import get_logger

logger = get_logger(__name__)
async def get_role_by_name(session: AsyncSession, name: str) -> Role | None:
    result = await session.execute(select(Role).filter(Role.name == name))
    return result.scalar_one_or_none()
async def get_user_by_telegram_id(
    session: AsyncSession, telegram_id: int
) -> User | None:
    result = await session.execute(select(User).filter(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()
async def create_user(
    session: AsyncSession, telegram_id: int, email: str, role: Role
) -> User:
    existing_user = await get_user_by_telegram_id(session, telegram_id)
    if existing_user:
        logger.warning(
            f"Попытка создать дублирующегося пользователя с telegram_id: {telegram_id}"
        )
        raise IntegrityError(
            f"Пользователь с telegram_id {telegram_id} уже существует", None, None
        )
    new_user = User(telegram_id=telegram_id, email=email, role_id=role.id)
    session.add(new_user)
    try:
        await session.commit()
        await session.refresh(new_user)
        logger.info(f"Успешно создан пользователь с telegram_id: {telegram_id}")
        return new_user
    except IntegrityError as e:
        await session.rollback()
        logger.error(f"Ошибка создания пользователя {telegram_id}: {e}")
        raise
async def update_user(
    session: AsyncSession, telegram_id: int, email: str, role: Role
) -> User:
    user = await get_user_by_telegram_id(session, telegram_id)
    if not user:
        raise ValueError(f"Пользователь с telegram_id {telegram_id} не найден")
    user.email = email
    user.role_id = role.id
    await session.commit()
    await session.refresh(user)
    logger.info(f"Обновлены данные пользователя {telegram_id}")
    return user
