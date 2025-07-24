from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards.inline import get_role_selection_keyboard
from services.user_service import (
    create_user,
    get_role_by_name,
    get_user_by_telegram_id,
    update_user,
)
from states.register import RegisterState
from utils.logger import get_logger

router = Router()
logger = get_logger(__name__)
@router.message(RegisterState.email, ~F.text.contains("@"))
async def invalid_email(message: Message):
    logger.warning(
        f"Пользователь {message.from_user.id} ввел некорректный email: {message.text}"
    )
    await message.answer(
        "Это не похоже на email. Пожалуйста, введите корректный адрес электронной почты."
    )
@router.message(RegisterState.email, F.text.contains("@"))
async def email_received(message: Message, state: FSMContext):
    logger.info(f"Пользователь {message.from_user.id} ввел email: {message.text}")
    await state.update_data(email=message.text)
    await state.set_state(RegisterState.role)
    await message.answer(
        "Отлично! Теперь выберите вашу роль:",
        reply_markup=get_role_selection_keyboard(),
    )
@router.callback_query(RegisterState.role, F.data.startswith("role_"))
async def role_selected(
    callback: CallbackQuery, session: AsyncSession, state: FSMContext
):
    role_name = callback.data.split("_")[1]
    logger.info(f"Пользователь {callback.from_user.id} выбрал роль: {role_name}")
    user_data = await state.get_data()
    email = user_data.get("email")
    role = await get_role_by_name(session, role_name)
    if not role:
        logger.error(
            f"Не удалось найти роль '{role_name}' в базе данных для пользователя {callback.from_user.id}"
        )
        await callback.message.answer("Произошла ошибка. Попробуйте снова.")
        return
    try:
        existing_user = await get_user_by_telegram_id(session, callback.from_user.id)
        if existing_user:
            logger.info(
                f"Обновление данных существующего пользователя {callback.from_user.id}"
            )
            updated_user = await update_user(
                session=session,
                telegram_id=callback.from_user.id,
                email=email,
                role=role,
            )
            message_text = f"Ваши данные успешно обновлены! Теперь вы {role.name}."
        else:
            logger.info(f"Создание нового пользователя {callback.from_user.id}")
            new_user = await create_user(
                session=session,
                telegram_id=callback.from_user.id,
                email=email,
                role=role,
            )
            message_text = f"Вы успешно зарегистрированы как {role.name}!"
        await state.clear()
        await callback.message.edit_text(message_text)
        await callback.answer()
    except IntegrityError as e:
        logger.error(
            f"Ошибка при создании/обновлении пользователя {callback.from_user.id}: {e}"
        )
        await callback.message.answer(
            "Произошла ошибка при сохранении данных. Попробуйте команду /reregister для перерегистрации."
        )
        await callback.answer()
    except Exception as e:
        logger.error(
            f"Неожиданная ошибка при регистрации пользователя {callback.from_user.id}: {e}"
        )
        await callback.message.answer(
            "Произошла неожиданная ошибка. Обратитесь к администратору."
        )
        await callback.answer()
