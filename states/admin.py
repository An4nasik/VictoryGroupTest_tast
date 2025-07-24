from aiogram.fsm.state import State, StatesGroup


class SetRoleState(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_role_selection = State()
