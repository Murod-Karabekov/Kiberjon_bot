from aiogram import Router, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters.command import CommandObject
from bot.database.database import Database
from bot.database.models import TransactionType
from bot.keyboards.reply import get_phone_keyboard

router = Router()


class RegistrationStates(StatesGroup):
    waiting_for_phone = State()
    waiting_for_name = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, db: Database, command: CommandObject):
    """Handle /start command"""
    telegram_id = message.from_user.id
    user = await db.get_user(telegram_id)

    # If user already registered, greet them
    if user and user.is_registered:
        await message.answer(
            f"Assalomu alaykum, {user.preferred_name}! 🎉\n\n"
            f"Sizni yana ko'rganimdan xursandman! 😊\n\n"
            f"💰 KiberCoin balansingiz: {user.coins}\n"
            f"Referal tizimi haqida ma'lumot olish uchun /coins buyrug'ini yuboring."
        )
        return

    # Check for referral code in command arguments
    referral_code = None
    if command.args:
        referral_code = command.args.strip()

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

    # Save referral code to state if provided
    if referral_code:
        await state.update_data(referral_code=referral_code)

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
    user = await db.update_user_name(telegram_id, preferred_name)
    
    # Generate referral code for new user
    await db.set_referral_code(user.id)

    # Check if user came from referral link
    state_data = await state.get_data()
    referral_code = state_data.get('referral_code')
    
    if referral_code:
        referrer = await db.get_user_by_referral_code(referral_code)
        if referrer and referrer.id != user.id:
            # Update referred_by
            async with db.session_maker() as session:
                from sqlalchemy import select
                from bot.database.models import User
                result = await session.execute(
                    select(User).where(User.id == user.id)
                )
                user_obj = result.scalar_one_or_none()
                if user_obj:
                    user_obj.referred_by_id = referrer.id
                    await session.commit()
            
            # Give 7 KiberCoins to referrer
            await db.add_coins(
                user_id=referrer.id,
                amount=7,
                transaction_type=TransactionType.REFERRAL_BONUS,
                description=f"Referal bonus: {preferred_name} botga qo'shildi",
                related_user_id=user.id
            )
            
            # Notify referrer
            try:
                from aiogram import Bot
                from bot.config import BOT_TOKEN
                bot = Bot(token=BOT_TOKEN)
                await bot.send_message(
                    referrer.telegram_id,
                    f"🎉 Tabriklaymiz!\n\n"
                    f"Sizning referal linkingiz orqali {preferred_name} botga qo'shildi!\n\n"
                    f"💰 +7 KiberCoin\n"
                    f"Jami balansingiz: {referrer.coins + 7} KiberCoin"
                )
            except:
                pass

    # Congratulate user on successful registration
    await message.answer(
        f"Juda yaxshi, {preferred_name}! 🎉\n\n"
        f"Ro'yxatdan o'tish muvaffaqiyatli yakunlandi! ✅\n\n"
        f"💰 Do'stlaringizni taklif qiling va KiberCoin yutib oling!\n"
        f"/coins buyrug'i orqali referal linkingizni oling."
    )
    await state.clear()


@router.message(RegistrationStates.waiting_for_name)
async def invalid_name(message: Message):
    """Handle invalid name input"""
    await message.answer(
        "Iltimos, ismingizni matn ko'rinishida yozing. 📝"
    )
