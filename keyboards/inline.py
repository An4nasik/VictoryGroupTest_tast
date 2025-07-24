from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_role_selection_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Простой пользователь", callback_data="role_user")],
        [InlineKeyboardButton(text="Модератор", callback_data="role_moderator")],
        [InlineKeyboardButton(text="Администратор", callback_data="role_admin")],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard
def get_audience_selection_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Всем пользователям", callback_data="audience_all")],
        [
            InlineKeyboardButton(
                text="Только пользователям", callback_data="audience_users"
            )
        ],
        [
            InlineKeyboardButton(
                text="Только модераторам", callback_data="audience_moderators"
            )
        ],
        [
            InlineKeyboardButton(
                text="Только администраторам", callback_data="audience_admins"
            )
        ],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard
def get_schedule_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Отправить сейчас", callback_data="schedule_now")],
        [InlineKeyboardButton(text="Запланировать", callback_data="schedule_later")],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard
def get_content_type_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="📝 Только текст", callback_data="content_type_text"
            )
        ],
        [
            InlineKeyboardButton(
                text="🖼️ Фото с текстом", callback_data="content_type_photo"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎬 Видео с текстом", callback_data="content_type_video"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎭 GIF с текстом", callback_data="content_type_animation"
            )
        ],
        [
            InlineKeyboardButton(
                text="📎 Документ с текстом", callback_data="content_type_document"
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
def get_media_actions_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="➕ Добавить кнопки", callback_data="add_buttons")],
        [
            InlineKeyboardButton(
                text="⏭️ Пропустить кнопки", callback_data="skip_buttons"
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
def get_buttons_management_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="➕ Добавить кнопку", callback_data="add_new_button"
            )
        ],
        [InlineKeyboardButton(text="✅ Завершить", callback_data="finish_buttons")],
        [
            InlineKeyboardButton(
                text="🗑️ Удалить последнюю", callback_data="remove_last_button"
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
def get_newsletter_preview_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="📤 Отправить сейчас", callback_data="confirm_send_now"
            ),
            InlineKeyboardButton(
                text="📅 Запланировать", callback_data="confirm_schedule"
            ),
        ],
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_newsletter")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_newsletter")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
def create_newsletter_inline_keyboard(buttons_data: list) -> InlineKeyboardMarkup:
    if not buttons_data:
        return None
    buttons = []
    for button_data in buttons_data:
        button = InlineKeyboardButton(text=button_data["text"], url=button_data["url"])
        buttons.append([button])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
