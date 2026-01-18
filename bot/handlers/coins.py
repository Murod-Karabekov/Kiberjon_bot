from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from bot.database.database import Database
from bot.config import BOT_TOKEN

router = Router()

# Cache bot info
_bot_username = None

async def get_bot_username() -> str:
    """Get bot username (cached)"""
    global _bot_username
    if _bot_username is None:
        bot = Bot(token=BOT_TOKEN)
        me = await bot.get_me()
        _bot_username = me.username
        await bot.session.close()
    return _bot_username


@router.message(Command("coins"))
async def cmd_coins(message: Message, db: Database):
    """Handle /coins command - show KiberCoin balance and referral info"""
    telegram_id = message.from_user.id
    user = await db.get_user(telegram_id)

    if not user or not user.is_registered:
        await message.answer(
            "❌ Avval ro'yxatdan o'ting!\n\n"
            "/start buyrug'ini yuboring."
        )
        return

    # Get referral statistics
    referrals_count = 0
    async with db.session_maker() as session:
        from sqlalchemy import select, func
        from bot.database.models import User
        result = await session.execute(
            select(func.count(User.id)).where(User.referred_by_id == user.id)
        )
        referrals_count = result.scalar() or 0

    # Build referral link
    bot_username = await get_bot_username()
    referral_link = f"https://t.me/{bot_username}?start={user.referral_code}"

    text = (
        f"💰 <b>KiberCoin Balansingiz</b>\n\n"
        f"👤 Ism: {user.preferred_name}\n"
        f"💎 Balans: <b>{user.coins} KiberCoin</b>\n"
        f"👥 Referal: {referrals_count} kishi\n\n"
        f"🔗 <b>Sizning referal linkingiz:</b>\n"
        f"<code>{referral_link}</code>\n\n"
        f"📊 Har bir taklif qilingan do'st uchun:\n"
        f"💰 +7 KiberCoin\n\n"
        f"Do'stlaringizni taklif qiling va KiberCoin yutib oling! 🎉"
    )

    # Create keyboard with share button
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📋 Nusxalash", callback_data="copy_referral_link"),
                InlineKeyboardButton(text="📤 Ulashish", switch_inline_query=user.referral_code)
            ],
            [InlineKeyboardButton(text="📊 Tranzaksiyalar", callback_data="my_transactions")]
        ]
    )

    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "copy_referral_link")
async def copy_referral_link(callback: CallbackQuery, db: Database):
    """Send referral link for easy copying"""
    telegram_id = callback.from_user.id
    user = await db.get_user(telegram_id)

    if not user:
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
        return

    bot_username = await get_bot_username()
    referral_link = f"https://t.me/{bot_username}?start={user.referral_code}"

    await callback.message.answer(
        f"🔗 <b>Referal linkingiz:</b>\n\n"
        f"<code>{referral_link}</code>\n\n"
        f"☝️ Linkni nusxalash uchun ustiga bosing!\n"
        f"Keyin do'stlaringizga yuboring.",
        parse_mode="HTML"
    )
    await callback.answer("✅ Link yuborildi!")


@router.callback_query(F.data == "my_transactions")
async def my_transactions(callback: CallbackQuery, db: Database):
    """Show user's transaction history"""
    telegram_id = callback.from_user.id
    user = await db.get_user(telegram_id)

    if not user:
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
        return

    transactions = await db.get_transactions(user_id=user.id, limit=10)

    if not transactions:
        await callback.answer("📭 Hali tranzaksiyalar yo'q", show_alert=True)
        return

    text = "📊 <b>Oxirgi 10 ta tranzaksiya:</b>\n\n"
    
    for tx in transactions:
        amount_str = f"+{tx.amount}" if tx.amount > 0 else str(tx.amount)
        emoji = "💰" if tx.amount > 0 else "💸"
        
        type_name = {
            "referral_bonus": "Referal bonus",
            "admin_add": "Admin qo'shdi",
            "admin_remove": "Admin olib tashladi"
        }.get(tx.transaction_type.value, "Noma'lum")
        
        date_str = tx.created_at.strftime("%d.%m.%Y %H:%M")
        
        text += f"{emoji} <b>{amount_str} KiberCoin</b>\n"
        text += f"📝 {type_name}\n"
        if tx.description:
            text += f"💬 {tx.description}\n"
        text += f"📅 {date_str}\n\n"

    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer("✅")


@router.inline_query()
async def inline_share_referral(inline_query: InlineQuery, db: Database):
    """Handle inline query for sharing referral link"""
    referral_code = inline_query.query.strip()
    
    if not referral_code:
        await inline_query.answer([])
        return
    
    # Get user by referral code
    user = await db.get_user_by_referral_code(referral_code)
    
    if not user:
        await inline_query.answer([])
        return
    
    # Get bot username
    bot_username = await get_bot_username()
    referral_link = f"https://t.me/{bot_username}?start={referral_code}"
    
    # Create attractive share message
    share_message = (
        f"🎉 <b>Salom do'stim!</b>\n\n"
        f"Men ajoyib botni topdim va siz bilan ulashmoqchiman! 🤖\n\n"
        f"💰 <b>KiberCoin</b> yig'ish imkoniyati bor!\n"
        f"🎁 Ro'yxatdan o'ting va bonuslar oling\n"
        f"🚀 Do'stlaringizni taklif qilib coin yutib oling\n\n"
        f"👇 <b>Hoziroq qo'shiling:</b>\n"
        f"{referral_link}\n\n"
        f"Tezroq start oling va KiberCoin yig'ing! 💎"
    )
    
    # Create inline query result
    result = InlineQueryResultArticle(
        id="1",
        title="🎁 Do'stingizni taklif qiling!",
        description="KiberCoin yutib oling - Har bir referal uchun +7 coin!",
        input_message_content=InputTextMessageContent(
            message_text=share_message,
            parse_mode="HTML"
        ),
        thumbnail_url="https://img.icons8.com/color/96/000000/gift.png"
    )
    
    await inline_query.answer([result], cache_time=1)
