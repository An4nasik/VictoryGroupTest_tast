from aiogram.fsm.state import State, StatesGroup


class RegisterState(StatesGroup):
    email = State()
    role = State()

