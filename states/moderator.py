from aiogram.fsm.state import State, StatesGroup


class CreateNewsletter(StatesGroup):
    waiting_for_text = State()
    waiting_for_audience = State()
    waiting_for_schedule = State()
    waiting_for_schedule_datetime = State()
    waiting_for_content_type = State()
    waiting_for_media = State()
    waiting_for_inline_buttons = State()
    confirming_newsletter = State()

