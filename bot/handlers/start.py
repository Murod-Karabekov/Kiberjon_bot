from aiogram import Router, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardRemove
from bot.database.database import Database
from bot.keyboards.reply import get_phone_keyboard

router = Router()


class RegistrationStates(StatesGroup):
    waiting_for_phone = State()
    waiting_for_name = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, db: Database):
    """Handle /start command"""
    telegram_id = message.from_user.id
    user = await db.get_user(telegram_id)

    # If user already registered, greet them
    if user and user.is_registered:
        await message.answer(
            f"Assalomu alaykum, {user.preferred_name}! 🎉\n\n"
            f"Sizni yana ko'rganimdan xursandman! 😊"
        )
        return

    # If user exists but not registered, continue registration
    if not user:
        # Create new user
        user = await db.create_user(
            telegram_id=telegram_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            language_code=message.from_user.language_code
        )

    # Start registration process
    await message.answer(
        "Assalomu alaykum! 👋\n\n"
        "Botimizga xush kelibsiz! Ro'yxatdan o'tish uchun telefon raqamingizni yuboring.\n\n"
        "Pastdagi tugmani bosing va telefon raqamingiz avtomatik yuboriladi. 📱",
        reply_markup=get_phone_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_for_phone)


@router.message(RegistrationStates.waiting_for_phone, F.contact)
async def process_contact(message: Message, state: FSMContext, db: Database):
    """Process contact (phone number)"""
    phone_number = message.contact.phone_number
    telegram_id = message.from_user.id

    # Update user's phone number
    await db.update_user_phone(telegram_id, phone_number)

    # Ask for preferred name
    await message.answer(
        "Rahmat! Telefon raqamingiz qabul qilindi. ✅\n\n"
        "Endi sizni qanday chaqirsak bo'ladi? Ismingizni yozing. 😊",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(RegistrationStates.waiting_for_name)


@router.message(RegistrationStates.waiting_for_phone)
async def invalid_phone(message: Message):
    """Handle invalid phone number input"""
    await message.answer(
        "Iltimos, telefon raqamingizni yuborish uchun pastdagi tugmani bosing. 👇",
        reply_markup=get_phone_keyboard()
    )


@router.message(RegistrationStates.waiting_for_name, F.text)
async def process_name(message: Message, state: FSMContext, db: Database):
    """Process user's preferred name"""
    preferred_name = message.text.strip()
    telegram_id = message.from_user.id

    # Update user's name and mark as registered
    await db.update_user_name(telegram_id, preferred_name)

    # Congratulate user on successful registration
    await message.answer(
        f"Juda yaxshi, {preferred_name}! 🎉\n\n"
        f"Ro'yxatdan o'tish muvaffaqiyatli yakunlandi! ✅\n\n"
        f"Sizni ko'rganimdan juda xursandman! Botimizdan foydalanishda omad tilayman! 🚀"
    )
    await state.clear()


@router.message(RegistrationStates.waiting_for_name)
async def invalid_name(message: Message):
    """Handle invalid name input"""
    await message.answer(
        "Iltimos, ismingizni matn ko'rinishida yozing. 📝"
    )
