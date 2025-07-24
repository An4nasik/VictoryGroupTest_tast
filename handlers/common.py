from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from models.models import Newsletter, User
from states.register import RegisterState
from utils.logger import get_logger

router = Router()
logger = get_logger(__name__)
@router.message(Command("start"))
async def start_command(message: Message, session: AsyncSession, state: FSMContext):
    user_id = message.from_user.id
    logger.info(f"Пользователь {user_id} вызвал команду /start.")
    await state.clear()
    query = (
        select(User)
        .options(selectinload(User.role))
        .filter(User.telegram_id == user_id)
    )
    result = await session.execute(query)
    existing_user = result.scalar_one_or_none()
    if existing_user:
        logger.info(
            f"Пользователь {user_id} уже зарегистрирован. Пропускаем регистрацию."
        )
        await message.answer(
            f"С возвращением, {message.from_user.full_name}! Вы — {existing_user.role.name}."
        )
        return
    logger.info(f"Начало нового процесса регистрации для пользователя {user_id}")
    await state.set_state(RegisterState.email)
    await message.answer(
        "Добро пожаловать! Давайте зарегистрируемся. Пожалуйста, введите ваш email:"
    )
@router.message(Command("reregister"))
async def reregister_command(
    message: Message, session: AsyncSession, state: FSMContext
):
    user_id = message.from_user.id
    logger.info(f"Пользователь {user_id} инициировал перерегистрацию.")
    await state.clear()
    logger.info(f"Состояние для пользователя {user_id} очищено.")
    query = select(User).filter(User.telegram_id == user_id)
    result = await session.execute(query)
    existing_user = result.scalar_one_or_none()
    if existing_user:
        newsletters_check = await session.execute(
            select(func.count(Newsletter.id)).where(
                Newsletter.creator_id == existing_user.id
            )
        )
        newsletters_count = newsletters_check.scalar()
        if newsletters_count > 0:
            logger.info(
                f"Пользователь {user_id} имеет {newsletters_count} рассылок, обновляем без удаления."
            )
            await message.answer(
                f"У вас есть {newsletters_count} рассылок. Ваши данные будут обновлены, "
                "но рассылки сохранятся."
            )
        else:
            logger.info(
                f"Пользователь {user_id} не имеет рассылок, можно безопасно обновить."
            )
            await message.answer("Ваши данные будут обновлены.")
        await state.set_state(RegisterState.email)
        await message.answer("Введите новый email для обновления профиля:")
        return
    else:
        logger.info(
            f"Пользователь {user_id} не найден в базе, начинаем новую регистрацию."
        )
        await message.answer("Начинаем процесс регистрации.")
    await state.set_state(RegisterState.email)
    await message.answer("Пожалуйста, введите ваш email:")
