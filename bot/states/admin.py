from aiogram.fsm.state import State, StatesGroup


class CoinManagementStates(StatesGroup):
    """States for coin management operations"""
    waiting_for_phone = State()
    waiting_for_amount = State()
