import datetime

from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards.inline import (
    get_audience_selection_keyboard,
    get_buttons_management_keyboard,
    get_content_type_keyboard,
    get_media_actions_keyboard,
    get_schedule_keyboard,
)
from middlewares.auth import IsModerator
from models.models import (
    ButtonTypeEnum,
    ContentTypeEnum,
    Newsletter,
    NewsletterButton,
    NewsletterMedia,
    NewsletterStatusEnum,
    TargetAudienceEnum,
)
from services.newsletter_service import NewsletterService
from services.user_service import get_user_by_telegram_id
from states.moderator import CreateNewsletter

router = Router()
router.message.filter(IsModerator())
router.callback_query.filter(IsModerator())
@router.message(Command("create_newsletter"))
async def start_newsletter(message: Message, state: FSMContext):
    await state.set_state(CreateNewsletter.waiting_for_text)
    await message.answer(
        "Введите текст для рассылки. Вы можете использовать форматирование Telegram (жирный, курсив и т.д.)."
    )
@router.message(CreateNewsletter.waiting_for_text, F.text)
async def newsletter_text_received(message: Message, state: FSMContext):
    await state.update_data(text=message.html_text)
    await state.set_state(CreateNewsletter.waiting_for_content_type)
    await message.answer(
        "Отлично! Теперь выберите тип контента для рассылки:",
        reply_markup=get_content_type_keyboard(),
    )
@router.callback_query(
    CreateNewsletter.waiting_for_content_type, F.data.startswith("content_type_")
)
async def content_type_selected(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    content_type = callback.data.split("_")[2]
    await state.update_data(content_type=content_type)
    if content_type == "text":
        await state.set_state(CreateNewsletter.waiting_for_audience)
        await callback.message.edit_text(
            "Теперь выберите, кому отправить рассылку:",
            reply_markup=get_audience_selection_keyboard(),
        )
    else:
        await state.set_state(CreateNewsletter.waiting_for_media)
        media_instructions = {
            "photo": "🖼️ Отправьте фотографию для рассылки",
            "video": "🎬 Отправьте видео для рассылки",
            "animation": "🎭 Отправьте GIF-анимацию для рассылки",
            "document": "📎 Отправьте документ для рассылки",
        }
        instruction = media_instructions.get(content_type, "Отправьте медиафайл")
        await callback.message.edit_text(instruction)
@router.message(CreateNewsletter.waiting_for_media, F.photo)
async def photo_received(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("content_type") != "photo":
        await message.answer("❌ Ожидается фотография. Отправьте фото.")
        return
    photo = message.photo[-1]
    await state.update_data(
        media_file_id=photo.file_id,
        media_file_unique_id=photo.file_unique_id,
        media_file_type="photo",
        media_file_size=photo.file_size,
    )
    await state.set_state(CreateNewsletter.waiting_for_audience)
    await message.answer(
        "✅ Фотография загружена! Теперь выберите аудиторию:",
        reply_markup=get_audience_selection_keyboard(),
    )
@router.message(CreateNewsletter.waiting_for_media, F.video)
async def video_received(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("content_type") != "video":
        await message.answer("❌ Ожидается видео. Отправьте видеофайл.")
        return
    video = message.video
    await state.update_data(
        media_file_id=video.file_id,
        media_file_unique_id=video.file_unique_id,
        media_file_type="video",
        media_file_size=video.file_size,
        media_mime_type=video.mime_type,
        media_file_name=video.file_name,
    )
    await state.set_state(CreateNewsletter.waiting_for_audience)
    await message.answer(
        "✅ Видео загружено! Теперь выберите аудиторию:",
        reply_markup=get_audience_selection_keyboard(),
    )
@router.message(CreateNewsletter.waiting_for_media, F.animation)
async def animation_received(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("content_type") != "animation":
        await message.answer("❌ Ожидается GIF-анимация. Отправьте GIF.")
        return
    animation = message.animation
    await state.update_data(
        media_file_id=animation.file_id,
        media_file_unique_id=animation.file_unique_id,
        media_file_type="animation",
        media_file_size=animation.file_size,
        media_mime_type=animation.mime_type,
        media_file_name=animation.file_name,
    )
    await state.set_state(CreateNewsletter.waiting_for_audience)
    await message.answer(
        "✅ GIF загружен! Теперь выберите аудиторию:",
        reply_markup=get_audience_selection_keyboard(),
    )
@router.message(CreateNewsletter.waiting_for_media, F.document)
async def document_received(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("content_type") != "document":
        await message.answer("❌ Ожидается документ. Отправьте файл.")
        return
    document = message.document
    await state.update_data(
        media_file_id=document.file_id,
        media_file_unique_id=document.file_unique_id,
        media_file_type="document",
        media_file_size=document.file_size,
        media_mime_type=document.mime_type,
        media_file_name=document.file_name,
    )
    await state.set_state(CreateNewsletter.waiting_for_audience)
    await message.answer(
        "✅ Документ загружен! Теперь выберите аудиторию:",
        reply_markup=get_audience_selection_keyboard(),
    )
@router.message(CreateNewsletter.waiting_for_media)
async def wrong_media_type(message: Message, state: FSMContext):
    """Обрабатывает неправильный тип медиафайла"""
    data = await state.get_data()
    content_type = data.get("content_type")
    error_messages = {
        "photo": "❌ Ожидается фотография. Отправьте фото.",
        "video": "❌ Ожидается видео. Отправьте видеофайл.",
        "animation": "❌ Ожидается GIF-анимация. Отправьте GIF.",
        "document": "❌ Ожидается документ. Отправьте файл.",
    }
    error_msg = error_messages.get(
        content_type, "❌ Отправьте правильный тип медиафайла."
    )
    await message.answer(error_msg)
@router.callback_query(
    CreateNewsletter.waiting_for_audience, F.data.startswith("audience_")
)
async def audience_selected(callback: types.CallbackQuery, state: FSMContext):
    """
    Получает аудиторию и предлагает добавить inline кнопки.
    """
    await callback.answer()
    audience = callback.data.split("_")[1]
    await state.update_data(audience=audience)
    await state.set_state(CreateNewsletter.waiting_for_inline_buttons)
    await callback.message.edit_text(
        "Аудитория выбрана! Хотите добавить кнопки-ссылки к рассылке?",
        reply_markup=get_media_actions_keyboard(),
    )
@router.callback_query(
    CreateNewsletter.waiting_for_inline_buttons,
    F.data.in_(["add_buttons", "skip_buttons"]),
)
async def buttons_action_selected(callback: types.CallbackQuery, state: FSMContext):
    """
    Обрабатывает выбор: добавить кнопки или пропустить
    """
    await callback.answer()
    if callback.data == "add_buttons":
        await state.update_data(buttons=[])
        await state.set_state(CreateNewsletter.waiting_for_inline_buttons)
        await callback.message.edit_text(
            "Отлично! Введите текст кнопки и URL через пробел.\n\n"
            "📝 <b>Формат:</b> <code>Текст_кнопки https://example.com</code>\n"
            "🌐 <b>Пример:</b> <code>Наш_сайт https://google.com</code>",
            parse_mode="HTML",
        )
    else:
        await state.set_state(CreateNewsletter.waiting_for_schedule)
        await callback.message.edit_text(
            "Кнопки пропущены. Теперь выберите, когда отправить рассылку:",
            reply_markup=get_schedule_keyboard(),
        )
@router.message(CreateNewsletter.waiting_for_inline_buttons, F.text)
async def button_received(message: Message, state: FSMContext):
    """
    Получает данные для новой кнопки
    """
    try:
        parts = message.text.strip().split()
        if len(parts) < 2:
            raise ValueError("Неполные данные")
        button_text = parts[0].replace("_", " ")
        button_url = " ".join(parts[1:])
        if not (button_url.startswith("http://") or button_url.startswith("https://")):
            await message.answer("❌ URL должен начинаться с http:// или https://")
            return
    except (ValueError, IndexError):
        await message.answer(
            "❌ Неверный формат!\n\n"
            "📝 <b>Правильный формат:</b> <code>Текст_кнопки https://example.com</code>\n"
            "🌐 <b>Пример:</b> <code>Наш_сайт https://google.com</code>",
            parse_mode="HTML",
        )
        return
    data = await state.get_data()
    buttons = data.get("buttons", [])
    button = {
        "text": button_text,
        "url": button_url,
        "type": "URL",
    }
    buttons.append(button)
    await state.update_data(buttons=buttons)
    await message.answer(
        f"✅ Кнопка добавлена: <b>{button_text}</b>\n"
        f"🔗 Ссылка: {button_url}\n\n"
        f"📊 Всего кнопок: {len(buttons)}",
        reply_markup=get_buttons_management_keyboard(),
        parse_mode="HTML",
    )
@router.callback_query(
    CreateNewsletter.waiting_for_inline_buttons,
    F.data.in_(["add_new_button", "finish_buttons", "remove_last_button"]),
)
async def manage_buttons_action(callback: types.CallbackQuery, state: FSMContext):
    """
    Управление кнопками: добавить еще, удалить последнюю или завершить
    """
    await callback.answer()
    data = await state.get_data()
    buttons = data.get("buttons", [])
    if callback.data == "add_new_button":
        await callback.message.edit_text(
            "Введите текст кнопки и URL через пробел.\n\n"
            "📝 <b>Формат:</b> <code>Текст_кнопки https://example.com</code>\n"
            "🌐 <b>Пример:</b> <code>Наш_сайт https://google.com</code>",
            parse_mode="HTML",
        )
    elif callback.data == "remove_last_button":
        if buttons:
            removed_button = buttons.pop()
            await state.update_data(buttons=buttons)
            await callback.message.edit_text(
                f"🗑️ Удалена кнопка: <b>{removed_button['text']}</b>\n"
                f"📊 Осталось кнопок: {len(buttons)}",
                reply_markup=get_buttons_management_keyboard(),
                parse_mode="HTML",
            )
        else:
            await callback.message.edit_text(
                "❌ Нет кнопок для удаления.",
                reply_markup=get_buttons_management_keyboard(),
            )
    elif callback.data == "finish_buttons":
        if buttons:
            button_list = "\n".join(
                [f"• {btn['text']} → {btn['url']}" for btn in buttons]
            )
            await state.set_state(CreateNewsletter.waiting_for_schedule)
            await callback.message.edit_text(
                f"✅ Настроено кнопок: {len(buttons)}\n\n"
                f"📋 <b>Список кнопок:</b>\n{button_list}\n\n"
                f"Теперь выберите, когда отправить рассылку:",
                reply_markup=get_schedule_keyboard(),
                parse_mode="HTML",
            )
        else:
            await callback.message.edit_text(
                "❌ Добавьте хотя бы одну кнопку или пропустите этот шаг.",
                reply_markup=get_buttons_management_keyboard(),
            )
    else:
        await callback.message.edit_text("❌ Неизвестное действие с кнопками.")
        await state.clear()
@router.callback_query(
    CreateNewsletter.waiting_for_schedule, F.data.startswith("schedule_")
)
async def schedule_selected(
    callback: types.CallbackQuery, state: FSMContext, session: AsyncSession
):
    """
    Обрабатывает выбор времени отправки.
    """
    await callback.answer()
    schedule_type = callback.data.split("_")[1]
    data = await state.get_data()
    user = await get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.message.edit_text("Ошибка: не удалось вас идентифицировать.")
        await state.clear()
        return
    audience_str = data.get("audience")
    print(f"DEBUG: Получено значение аудитории: '{audience_str}'")
    try:
        if audience_str == "all":
            audience_enum_member = TargetAudienceEnum.ALL
        elif audience_str == "users":
            audience_enum_member = TargetAudienceEnum.USERS
        elif audience_str == "moderators":
            audience_enum_member = TargetAudienceEnum.MODERATORS
        elif audience_str == "admins":
            audience_enum_member = TargetAudienceEnum.ADMINS
        else:
            raise ValueError(f"Неизвестное значение аудитории: {audience_str}")
        print(f"DEBUG: Создан enum объект: {audience_enum_member}")
    except ValueError as e:
        print(f"DEBUG: Ошибка создания enum: {e}")
        await callback.message.edit_text(
            f"Ошибка: неизвестная аудитория '{audience_str}'."
        )
        await state.clear()
        return
    if schedule_type == "now":
        content_type_str = data.get("content_type", "text")
        try:
            if content_type_str == "text":
                content_type_enum = ContentTypeEnum.TEXT
            elif content_type_str == "photo":
                content_type_enum = ContentTypeEnum.PHOTO
            elif content_type_str == "video":
                content_type_enum = ContentTypeEnum.VIDEO
            elif content_type_str == "animation":
                content_type_enum = ContentTypeEnum.ANIMATION
            elif content_type_str == "document":
                content_type_enum = ContentTypeEnum.DOCUMENT
            else:
                content_type_enum = ContentTypeEnum.TEXT
        except Exception as e:
            print(f"DEBUG: Ошибка создания content_type enum: {e}")
            content_type_enum = ContentTypeEnum.TEXT
        newsletter = Newsletter(
            creator_id=user.id,
            text=data.get("text"),
            target_audience=audience_enum_member,
            content_type=content_type_enum,
            status=NewsletterStatusEnum.PENDING,
            scheduled_at=datetime.datetime.now(),
        )
        session.add(newsletter)
        try:
            await session.commit()
            print(f"DEBUG: Рассылка успешно сохранена с ID: {newsletter.id}")
            if content_type_str != "text" and data.get("media_file_id"):
                media = NewsletterMedia(
                    newsletter_id=newsletter.id,
                    file_id=data.get("media_file_id"),
                    file_unique_id=data.get("media_file_unique_id"),
                    file_type=data.get("media_file_type"),
                    file_size=data.get("media_file_size"),
                    mime_type=data.get("media_mime_type"),
                    file_name=data.get("media_file_name"),
                )
                session.add(media)
                await session.commit()
                print(f"DEBUG: Медиафайл сохранен для рассылки {newsletter.id}")
            buttons = data.get("buttons", [])
            if buttons:
                for i, button in enumerate(buttons):
                    db_button = NewsletterButton(
                        newsletter_id=newsletter.id,
                        text=button["text"],
                        button_type=ButtonTypeEnum.URL,
                        url=button["url"],
                        row_position=0,
                        column_position=i,
                    )
                    session.add(db_button)
                await session.commit()
                print(
                    f"DEBUG: Сохранено {len(buttons)} кнопок для рассылки {newsletter.id}"
                )
        except Exception as e:
            print(f"DEBUG: Ошибка сохранения рассылки или медиафайла: {e}")
            await callback.message.edit_text(
                f"Ошибка при сохранении рассылки: {str(e)}"
            )
            await state.clear()
            return
        await state.clear()
        newsletter_service = NewsletterService(callback.bot)
        await callback.message.edit_text(
            "📤 Начинаем отправку рассылки...\nЭто может занять некоторое время."
        )
        try:
            stats = await newsletter_service.send_newsletter(session, newsletter.id)
            await callback.message.edit_text(
                f"✅ <b>Рассылка завершена!</b>\n\n"
                f"📝 <b>Текст:</b> {data.get('text')[:50]}{'...' if len(data.get('text')) > 50 else ''}\n"
                f"👥 <b>Аудитория:</b> {audience_str}\n\n"
                f"📊 <b>Статистика:</b>\n"
                f"• Всего пользователей: {stats['total']}\n"
                f"• Успешно доставлено: ✅ {stats['success']}\n"
                f"• Не доставлено: ❌ {stats['failed']}\n\n"
                f"⏰ <b>Время завершения:</b> {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}",
                parse_mode="HTML",
            )
        except Exception as e:
            await callback.message.edit_text(
                f"❌ Ошибка при отправке рассылки: {str(e)}"
            )
    else:
        await state.set_state(CreateNewsletter.waiting_for_schedule_datetime)
        await callback.message.edit_text(
            "Введите дату и время для отправки рассылки в формате: `ДД.ММ.ГГГГ ЧЧ:ММ`"
        )
@router.message(CreateNewsletter.waiting_for_schedule_datetime, F.text)
async def schedule_datetime_received(
    message: Message, state: FSMContext, session: AsyncSession
):
    try:
        scheduled_dt = datetime.datetime.strptime(message.text, "%d.%m.%Y %H:%M")
        now = datetime.datetime.now()
        if scheduled_dt <= now:
            await message.answer(
                f"⚠️ Указанное время уже прошло!\n"
                f"Текущее время: {now.strftime('%d.%m.%Y %H:%M')}\n"
                f"Укажите время в будущем."
            )
            return
        print(f"DEBUG: Пользователь ввел: {message.text}")
        print(f"DEBUG: Сохраняется как naive datetime: {scheduled_dt}")
        print(f"DEBUG: Текущее время: {now}")
    except ValueError:
        await message.answer(
            "Неверный формат. Пожалуйста, введите дату и время в формате: `ДД.ММ.ГГГГ ЧЧ:ММ`\n"
            "Например: `24.07.2025 22:12`"
        )
        return
    data = await state.get_data()
    user = await get_user_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer("Ошибка: не удалось вас идентифицировать.")
        await state.clear()
        return
    audience_str = data.get("audience")
    print(
        f"DEBUG: Получено значение аудитории для запланированной рассылки: '{audience_str}'"
    )
    try:
        if audience_str == "all":
            audience_enum_member = TargetAudienceEnum.ALL
        elif audience_str == "users":
            audience_enum_member = TargetAudienceEnum.USERS
        elif audience_str == "moderators":
            audience_enum_member = TargetAudienceEnum.MODERATORS
        elif audience_str == "admins":
            audience_enum_member = TargetAudienceEnum.ADMINS
        else:
            raise ValueError(f"Неизвестное значение аудитории: {audience_str}")
        print(
            f"DEBUG: Создан enum объект для запланированной рассылки: {audience_enum_member}"
        )
    except ValueError as e:
        print(f"DEBUG: Ошибка создания enum для запланированной рассылки: {e}")
        await message.answer(f"Ошибка: неизвестная аудитория '{audience_str}'.")
        await state.clear()
        return
    content_type_str = data.get("content_type", "text")
    try:
        if content_type_str == "text":
            content_type_enum = ContentTypeEnum.TEXT
        elif content_type_str == "photo":
            content_type_enum = ContentTypeEnum.PHOTO
        elif content_type_str == "video":
            content_type_enum = ContentTypeEnum.VIDEO
        elif content_type_str == "animation":
            content_type_enum = ContentTypeEnum.ANIMATION
        elif content_type_str == "document":
            content_type_enum = ContentTypeEnum.DOCUMENT
        else:
            content_type_enum = ContentTypeEnum.TEXT
    except Exception as e:
        print(
            f"DEBUG: Ошибка создания content_type enum для запланированной рассылки: {e}"
        )
        content_type_enum = ContentTypeEnum.TEXT
    newsletter = Newsletter(
        creator_id=user.id,
        text=data.get("text"),
        target_audience=audience_enum_member,
        content_type=content_type_enum,
        status=NewsletterStatusEnum.SCHEDULED,
        scheduled_at=scheduled_dt,
    )
    session.add(newsletter)
    try:
        await session.commit()
        print(
            f"DEBUG: Запланированная рассылка успешно сохранена с ID: {newsletter.id}"
        )
        if content_type_str != "text" and data.get("media_file_id"):
            media = NewsletterMedia(
                newsletter_id=newsletter.id,
                file_id=data.get("media_file_id"),
                file_unique_id=data.get("media_file_unique_id"),
                file_type=data.get("media_file_type"),
                file_size=data.get("media_file_size"),
                mime_type=data.get("media_mime_type"),
                file_name=data.get("media_file_name"),
            )
            session.add(media)
            await session.commit()
            print(
                f"DEBUG: Медиафайл сохранен для запланированной рассылки {newsletter.id}"
            )
        buttons = data.get("buttons", [])
        if buttons:
            for i, button in enumerate(buttons):
                db_button = NewsletterButton(
                    newsletter_id=newsletter.id,
                    text=button["text"],
                    button_type=ButtonTypeEnum.URL,
                    url=button["url"],
                    row_position=0,
                    column_position=i,
                )
                session.add(db_button)
            await session.commit()
            print(
                f"DEBUG: Сохранено {len(buttons)} кнопок для запланированной рассылки {newsletter.id}"
            )
    except Exception as e:
        print(f"DEBUG: Ошибка сохранения запланированной рассылки или медиафайла: {e}")
        await message.answer(f"Ошибка при сохранении рассылки: {str(e)}")
        await state.clear()
        return
    await state.clear()
    content_type_emoji = {
        "text": "📝",
        "photo": "🖼️",
        "video": "🎬",
        "animation": "🎭",
        "document": "📎",
    }
    emoji = content_type_emoji.get(content_type_str, "📝")
    await message.answer(
        f"✅ Рассылка запланирована на {scheduled_dt.strftime('%d.%m.%Y %H:%M')}.\n\n"
        f"{emoji} <b>Тип:</b> {content_type_str}\n"
        f"📝 <b>Текст:</b> {data.get('text')}\n"
        f"👥 <b>Аудитория:</b> {audience_str}",
        parse_mode="HTML",
    )
