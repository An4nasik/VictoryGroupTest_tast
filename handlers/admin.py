from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from keyboards.inline import get_role_selection_keyboard
from middlewares.auth import IsAdmin
from models.models import Newsletter, NewsletterStatusEnum, User
from services.newsletter_service import get_newsletter_stats
from services.user_service import get_role_by_name
from states.admin import SetRoleState
from utils.logger import get_logger

router = Router()
logger = get_logger(__name__)

router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


@router.message(Command("stats"))
async def get_stats(message: Message, session: AsyncSession):
    query = select(func.count(User.id))
    result = await session.execute(query)
    user_count = result.scalar_one()
    await message.answer(f"Всего пользователей в боте: {user_count}")


@router.message(Command("setrole"))
async def start_set_role(message: Message, state: FSMContext):
    logger.info(f"Администратор {message.from_user.id} инициировал смену роли.")
    await state.set_state(SetRoleState.waiting_for_user_id)
    await message.answer(
        "Введите Telegram ID пользователя, которому вы хотите изменить роль:"
    )


@router.message(SetRoleState.waiting_for_user_id, F.text)
async def user_id_received(message: Message, session: AsyncSession, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Telegram ID должен быть числом. Попробуйте еще раз.")
        return
    target_user_id = int(message.text)
    logger.info(
        f"Администратор {message.from_user.id} ввел ID: {target_user_id} для смены роли."
    )
    query = select(User).filter(User.telegram_id == target_user_id)
    result = await session.execute(query)
    user_to_update = result.scalar_one_or_none()
    if not user_to_update:
        await message.answer(
            f"Пользователь с ID {target_user_id} не найден. Попробуйте другой ID или отмените операцию."
        )
        return
    await state.update_data(target_user_id=target_user_id)
    await state.set_state(SetRoleState.waiting_for_role_selection)
    await message.answer(
        f"Пользователь {user_to_update.email} (ID: {target_user_id}) найден. Выберите новую роль:",
        reply_markup=get_role_selection_keyboard(),
    )


@router.callback_query(
    SetRoleState.waiting_for_role_selection, F.data.startswith("role_")
)
async def role_for_user_selected(
    callback: CallbackQuery, session: AsyncSession, state: FSMContext
):
    user_data = await state.get_data()
    target_user_id = user_data.get("target_user_id")
    new_role_name = callback.data.split("_")[1]
    admin_id = callback.from_user.id
    logger.info(
        f"Администратор {admin_id} выбрал роль '{new_role_name}' для пользователя {target_user_id}."
    )
    user_query = select(User).filter(User.telegram_id == target_user_id)
    user_result = await session.execute(user_query)
    user_to_update = user_result.scalar_one()
    new_role = await get_role_by_name(session, new_role_name)
    if not new_role:
        logger.error(
            f"Роль '{new_role_name}' не найдена в БД. Операция отменена администратором {admin_id}."
        )
        await callback.message.edit_text(
            "Произошла ошибка: не удалось найти указанную роль."
        )
        await state.clear()
        return
    user_to_update.role_id = new_role.id
    session.add(user_to_update)
    await session.commit()
    logger.info(
        f"Роль для пользователя {target_user_id} успешно обновлена на '{new_role_name}'."
    )
    await state.clear()
    await callback.message.edit_text(
        f"Роль для пользователя {target_user_id} успешно изменена на {new_role_name}."
    )
    await callback.answer()


@router.message(Command("newsletters"))
async def view_newsletters(message: Message, session: AsyncSession):
    stats = await get_newsletter_stats(session)
    result = await session.execute(
        select(Newsletter)
        .options(selectinload(Newsletter.creator))
        .order_by(desc(Newsletter.created_at))
        .limit(10)
    )
    recent_newsletters = result.scalars().all()
    text = "📊 <b>Статистика рассылок:</b>\n"
    text += f"• Всего рассылок: {stats['total']}\n"
    text += "• По статусам:\n"
    for status, count in stats["by_status"].items():
        status_emoji = {
            "draft": "📝",
            "pending": "⏳",
            "scheduled": "⏰",
            "sending": "📤",
            "sent": "✅",
        }.get(status, "❓")
        text += f"  {status_emoji} {status}: {count}\n"
    text += "\n📋 <b>Последние 10 рассылок:</b>\n\n"
    if not recent_newsletters:
        text += "Рассылок пока нет."
    else:
        for i, newsletter in enumerate(recent_newsletters, 1):
            creator_name = (
                newsletter.creator.email if newsletter.creator else "Неизвестно"
            )
            text += f"{i}. <b>ID:</b> {newsletter.id}\n"
            text += f"   📝 <b>Текст:</b> {newsletter.text[:30]}{'...' if len(newsletter.text) > 30 else ''}\n"
            text += f"   👤 <b>Создатель:</b> {creator_name}\n"
            text += f"   👥 <b>Аудитория:</b> {newsletter.target_audience.value}\n"
            text += f"   📅 <b>Создано:</b> {newsletter.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            text += f"   ⏰ <b>Запланировано:</b> {newsletter.scheduled_at.strftime('%d.%m.%Y %H:%M') if newsletter.scheduled_at else 'Не задано'}\n"
            text += f"   📊 <b>Статус:</b> {newsletter.status.value}\n\n"
    await message.answer(text, parse_mode="HTML")


@router.message(Command("newsletter"))
async def view_specific_newsletter(message: Message, session: AsyncSession):
    command_parts = message.text.split()
    if len(command_parts) != 2 or not command_parts[1].isdigit():
        await message.answer(
            "❌ <b>Неверный формат команды!</b>\n\n"
            "Используйте: <code>/newsletter &lt;ID&gt;</code>\n"
            "Например: <code>/newsletter 1</code>\n\n"
            "Чтобы увидеть список рассылок, используйте /newsletters",
            parse_mode="HTML",
        )
        return
    newsletter_id = int(command_parts[1])
    result = await session.execute(
        select(Newsletter)
        .options(selectinload(Newsletter.creator))
        .where(Newsletter.id == newsletter_id)
    )
    newsletter = result.scalar_one_or_none()
    if not newsletter:
        await message.answer(f"❌ Рассылка с ID {newsletter_id} не найдена.")
        return
    creator_name = newsletter.creator.email if newsletter.creator else "Неизвестно"
    text = "📄 <b>Рассылка"
    text += f"📝 <b>Текст:</b>\n{newsletter.text}\n\n"
    text += f"👤 <b>Создатель:</b> {creator_name}\n"
    text += f"👥 <b>Целевая аудитория:</b> {newsletter.target_audience.value}\n"
    text += (
        f"📅 <b>Дата создания:</b> {newsletter.created_at.strftime('%d.%m.%Y %H:%M')}\n"
    )
    if newsletter.scheduled_at:
        text += f"⏰ <b>Запланировано на:</b> {newsletter.scheduled_at.strftime('%d.%m.%Y %H:%M')}\n"
    status_info = {
        NewsletterStatusEnum.DRAFT: ("📝", "Черновик"),
        NewsletterStatusEnum.PENDING: ("⏳", "Ожидает отправки"),
        NewsletterStatusEnum.SCHEDULED: ("⏰", "Запланирована"),
        NewsletterStatusEnum.SENDING: ("📤", "Отправляется"),
        NewsletterStatusEnum.SENT: ("✅", "Отправлена"),
    }
    emoji, status_text = status_info.get(
        newsletter.status, ("❓", newsletter.status.value)
    )
    text += f"📊 <b>Статус:</b> {emoji} {status_text}\n"
    await message.answer(text, parse_mode="HTML")
