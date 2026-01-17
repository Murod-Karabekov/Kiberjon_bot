from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_phone_keyboard() -> ReplyKeyboardMarkup:
    """Create keyboard for phone number sharing"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefon raqamimni yuborish", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard


def remove_keyboard() -> ReplyKeyboardMarkup:
    """Remove keyboard"""
    from aiogram.types import ReplyKeyboardRemove
    return ReplyKeyboardRemove()
