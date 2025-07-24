import asyncio
import datetime

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.database import AsyncSessionLocal
from models.models import (
    ContentTypeEnum,
    Newsletter,
    NewsletterStatusEnum,
    Role,
    TargetAudienceEnum,
    User,
)
from utils.logger import get_logger

logger = get_logger(__name__)
class NewsletterService:
    def __init__(self, bot: Bot):
        self.bot = bot
    async def send_newsletter(
        self, session: AsyncSession, newsletter_id: int
    ) -> dict[str, int]:
        result = await session.execute(
            select(Newsletter)
            .options(
                selectinload(Newsletter.creator),
                selectinload(Newsletter.media_files),
                selectinload(Newsletter.inline_buttons),
            )
            .where(Newsletter.id == newsletter_id)
        )
        newsletter = result.scalar_one_or_none()
        if not newsletter:
            raise ValueError(f"Рассылка с ID {newsletter_id} не найдена")
        if newsletter.status != NewsletterStatusEnum.PENDING:
            raise ValueError(f"Рассылка уже обработана. Статус: {newsletter.status}")
        newsletter.status = NewsletterStatusEnum.SENDING
        await session.commit()
        logger.info(f"Начинаем отправку рассылки {newsletter_id}")
        target_users = await self._get_target_users(session, newsletter.target_audience)
        if not target_users:
            logger.warning(f"Не найдено пользователей для рассылки {newsletter_id}")
            newsletter.status = NewsletterStatusEnum.SENT
            await session.commit()
            return {"total": 0, "success": 0, "failed": 0}
        stats = {"total": len(target_users), "success": 0, "failed": 0, "errors": []}
        for user in target_users:
            try:
                await self._send_message_to_user(user.telegram_id, newsletter)
                stats["success"] += 1
                logger.debug(f"Сообщение отправлено пользователю {user.telegram_id}")
                await asyncio.sleep(0.05)
            except TelegramForbiddenError:
                stats["failed"] += 1
                stats["errors"].append(f"User {user.telegram_id}: bot blocked")
                logger.warning(f"Пользователь {user.telegram_id} заблокировал бота")
            except TelegramBadRequest as e:
                stats["failed"] += 1
                stats["errors"].append(f"User {user.telegram_id}: {str(e)}")
                logger.error(f"Ошибка отправки пользователю {user.telegram_id}: {e}")
            except Exception as e:
                stats["failed"] += 1
                stats["errors"].append(
                    f"User {user.telegram_id}: unexpected error - {str(e)}"
                )
                logger.error(
                    f"Неожиданная ошибка при отправке пользователю {user.telegram_id}: {e}"
                )
        newsletter.status = NewsletterStatusEnum.SENT
        await session.commit()
        logger.info(
            f"Рассылка {newsletter_id} завершена. "
            f"Успешно: {stats['success']}, Ошибок: {stats['failed']}"
        )
        return stats
    async def _get_target_users(
        self, session: AsyncSession, target_audience: TargetAudienceEnum
    ) -> list[User]:
        if target_audience == TargetAudienceEnum.ALL:
            result = await session.execute(
                select(User).options(selectinload(User.role))
            )
            return result.scalars().all()
        elif target_audience == TargetAudienceEnum.USERS:
            result = await session.execute(
                select(User)
                .join(Role)
                .where(Role.name == "user")
                .options(selectinload(User.role))
            )
            return result.scalars().all()
        elif target_audience == TargetAudienceEnum.MODERATORS:
            result = await session.execute(
                select(User)
                .join(Role)
                .where(Role.name == "moderator")
                .options(selectinload(User.role))
            )
            return result.scalars().all()
        elif target_audience == TargetAudienceEnum.ADMINS:
            result = await session.execute(
                select(User)
                .join(Role)
                .where(Role.name == "admin")
                .options(selectinload(User.role))
            )
            return result.scalars().all()
        return []
    async def process_pending_newsletters(self):
        async with AsyncSessionLocal() as session:
            try:
                now = datetime.datetime.now()
                print("DEBUG: Планировщик проверяет рассылки")
                print(f"DEBUG: Текущее время сервера: {now}")
                print(f"DEBUG: Временная зона сервера: {now.astimezone().tzinfo}")
                all_scheduled_result = await session.execute(
                    select(Newsletter).where(
                        Newsletter.status == NewsletterStatusEnum.SCHEDULED
                    )
                )
                all_scheduled = all_scheduled_result.scalars().all()
                print(
                    f"DEBUG: Всего запланированных рассылок в базе: {len(all_scheduled)}"
                )
                for newsletter in all_scheduled:
                    print(
                        f"DEBUG: Рассылка ID={newsletter.id}, время={newsletter.scheduled_at}, статус={newsletter.status}"
                    )
                    print(f"DEBUG: Время наступило? {newsletter.scheduled_at <= now}")
                result = await session.execute(
                    select(Newsletter)
                    .options(selectinload(Newsletter.creator))
                    .where(
                        Newsletter.status == NewsletterStatusEnum.SCHEDULED,
                        Newsletter.scheduled_at <= now,
                    )
                )
                pending_newsletters = result.scalars().all()
                print(
                    f"DEBUG: Найдено {len(pending_newsletters)} рассылок для обработки"
                )
                for newsletter in pending_newsletters:
                    print(
                        f"DEBUG: Рассылка ID={newsletter.id}, время={newsletter.scheduled_at}, статус={newsletter.status}"
                    )
                for newsletter in pending_newsletters:
                    try:
                        newsletter.status = NewsletterStatusEnum.PENDING
                        await session.commit()
                        stats = await self.send_newsletter(session, newsletter.id)
                        await self._notify_creator_about_results(newsletter, stats)
                    except Exception as e:
                        logger.error(
                            f"Ошибка при обработке рассылки {newsletter.id}: {e}"
                        )
                        failed_newsletter_result = await session.execute(
                            select(Newsletter)
                            .options(selectinload(Newsletter.creator))
                            .where(Newsletter.id == newsletter.id)
                        )
                        failed_newsletter = (
                            failed_newsletter_result.scalar_one_or_none()
                        )
                        if failed_newsletter:
                            failed_newsletter.status = (
                                NewsletterStatusEnum.SCHEDULED
                            )
                            await session.commit()
            except Exception as e:
                logger.error(f"Ошибка при обработке pending рассылок: {e}")
    async def _notify_creator_about_results(
        self, newsletter: Newsletter, stats: dict[str, int]
    ):
        try:
            async with AsyncSessionLocal() as session:
                creator = await session.get(User, newsletter.creator_id)
                if not creator:
                    logger.warning(f"Создатель рассылки {newsletter.id} не найден")
                    return
                report_text = (
                    f"📊 <b>Отчет о рассылке</b>\n\n"
                    f"📝 <b>Текст:</b> {newsletter.text[:50]}{'...' if len(newsletter.text) > 50 else ''}\n"
                    f"👥 <b>Аудитория:</b> {newsletter.target_audience.value}\n"
                    f"📈 <b>Статистика:</b>\n"
                    f"• Всего пользователей: {stats['total']}\n"
                    f"• Успешно доставлено: {stats['success']}\n"
                    f"• Не доставлено: {stats['failed']}\n"
                    f"⏰ <b>Время завершения:</b> {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}"
                )
                await self.bot.send_message(
                    chat_id=creator.telegram_id, text=report_text, parse_mode="HTML"
                )
                logger.info(f"Отчет о рассылке {newsletter.id} отправлен создателю")
        except Exception as e:
            logger.error(
                f"Ошибка при отправке отчета создателю рассылки {newsletter.id}: {e}"
            )
    async def _send_message_to_user(self, chat_id: int, newsletter: Newsletter):
        reply_markup = self._create_inline_keyboard(newsletter)
        content_type = getattr(newsletter, "content_type", ContentTypeEnum.TEXT)
        if content_type == ContentTypeEnum.TEXT:
            await self.bot.send_message(
                chat_id=chat_id,
                text=newsletter.text,
                parse_mode="HTML",
                reply_markup=reply_markup,
            )
        elif content_type == ContentTypeEnum.PHOTO:
            media_file = self._get_media_file(newsletter, "photo")
            if media_file:
                await self.bot.send_photo(
                    chat_id=chat_id,
                    photo=media_file.file_id,
                    caption=newsletter.text,
                    parse_mode="HTML",
                    reply_markup=reply_markup,
                )
            else:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=f"🖼️ [Фото недоступно]\n\n{newsletter.text}",
                    parse_mode="HTML",
                    reply_markup=reply_markup,
                )
        elif content_type == ContentTypeEnum.VIDEO:
            media_file = self._get_media_file(newsletter, "video")
            if media_file:
                await self.bot.send_video(
                    chat_id=chat_id,
                    video=media_file.file_id,
                    caption=newsletter.text,
                    parse_mode="HTML",
                    reply_markup=reply_markup,
                )
            else:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=f"🎬 [Видео недоступно]\n\n{newsletter.text}",
                    parse_mode="HTML",
                    reply_markup=reply_markup,
                )
        elif content_type == ContentTypeEnum.ANIMATION:
            media_file = self._get_media_file(newsletter, "animation")
            if media_file:
                await self.bot.send_animation(
                    chat_id=chat_id,
                    animation=media_file.file_id,
                    caption=newsletter.text,
                    parse_mode="HTML",
                    reply_markup=reply_markup,
                )
            else:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=f"🎭 [GIF недоступен]\n\n{newsletter.text}",
                    parse_mode="HTML",
                    reply_markup=reply_markup,
                )
        elif content_type == ContentTypeEnum.DOCUMENT:
            media_file = self._get_media_file(newsletter, "document")
            if media_file:
                await self.bot.send_document(
                    chat_id=chat_id,
                    document=media_file.file_id,
                    caption=newsletter.text,
                    parse_mode="HTML",
                    reply_markup=reply_markup,
                )
            else:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=f"📎 [Документ недоступен]\n\n{newsletter.text}",
                    parse_mode="HTML",
                    reply_markup=reply_markup,
                )
        else:
            await self.bot.send_message(
                chat_id=chat_id,
                text=newsletter.text,
                parse_mode="HTML",
                reply_markup=reply_markup,
            )
    def _create_inline_keyboard(
        self, newsletter: Newsletter
    ) -> InlineKeyboardMarkup | None:
        if not newsletter.inline_buttons:
            return None
        buttons = sorted(
            newsletter.inline_buttons, key=lambda b: (b.row_position, b.column_position)
        )
        if not buttons:
            return None
        rows = {}
        for button in buttons:
            row = button.row_position
            if row not in rows:
                rows[row] = []
            rows[row].append(button)
        keyboard_buttons = []
        for row_num in sorted(rows.keys()):
            row_buttons = []
            for button in rows[row_num]:
                if button.url:
                    row_buttons.append(
                        InlineKeyboardButton(text=button.text, url=button.url)
                    )
            if row_buttons:
                keyboard_buttons.append(row_buttons)
        if keyboard_buttons:
            return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        return None
async def get_newsletter_stats(session: AsyncSession) -> dict:
    total_result = await session.execute(select(func.count(Newsletter.id)))
    total_newsletters = total_result.scalar()
    stats_by_status = {}
    for status in NewsletterStatusEnum:
        result = await session.execute(
            select(func.count(Newsletter.id)).where(Newsletter.status == status)
        )
        stats_by_status[status.value] = result.scalar()
    return {"total": total_newsletters, "by_status": stats_by_status}
