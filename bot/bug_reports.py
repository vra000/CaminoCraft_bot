from aiogram.fsm.state import StatesGroup, State

class BugReport(StatesGroup):
    desc = State()
    photo = State()
    confirm = State()
