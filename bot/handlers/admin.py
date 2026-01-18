from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.database.database import Database
from bot.database.models import UserRole, TransactionType
from bot.keyboards.inline import (
    get_admin_main_menu,
    get_stats_keyboard,
    get_back_button,
    get_users_navigation,
    get_groups_navigation,
    get_coin_management_menu,
    get_transactions_navigation
)
from bot.states.admin import CoinManagementStates
import math

router = Router()

USERS_PER_PAGE = 10
GROUPS_PER_PAGE = 10


def format_user_info(user, index: int) -> str:
    """Format user information"""
    role_emoji = "👑" if user.role == UserRole.ADMIN else "👤"
    status = "✅" if user.is_registered else "⏳"
    
    info = f"{index}. {role_emoji} {status}\n"
    if user.preferred_name:
        info += f"   Ism: {user.preferred_name}\n"
    else:
        unknown = "Noma'lum"
        info += f"   Ism: {user.first_name or unknown}\n"
    
    if user.username:
        info += f"   @{user.username}\n"
    
    if user.phone_number:
        info += f"   📱 {user.phone_number}\n"
    
    info += f"   ID: {user.telegram_id}\n"
    
    return info


def format_group_info(group, index: int) -> str:
    """Format group information"""
    status = "✅" if group.is_active else "❌"
    admin_emoji = "👑" if group.bot_is_admin else "👤"
    
    type_emoji = {
        "group": "💬",
        "supergroup": "🔷",
        "channel": "📢"
    }
    
    info = f"{index}. {type_emoji.get(group.chat_type.value, '💬')} {status} {admin_emoji}\n"
    info += f"   {group.title}\n"
    
    if group.username:
        info += f"   @{group.username}\n"
    
    if group.member_count:
        info += f"   👥 {group.member_count} a'zo\n"
    
    info += f"   ID: {group.chat_id}\n"
    
    return info


@router.message(Command("admin"))
async def cmd_admin(message: Message, db: Database):
    """Admin panel buyrug'i"""
    telegram_id = message.from_user.id
    user = await db.get_user(telegram_id)
    
    # Check if user is admin
    if not user or user.role != UserRole.ADMIN:
        await message.answer(
            "❌ Kechirasiz, sizda admin huquqi yo'q!\n\n"
            "Bu buyruq faqat adminlar uchun."
        )
        return
    
    # Get statistics
    all_users = await db.get_all_users()
    registered_users = [u for u in all_users if u.is_registered]
    admins = await db.get_all_users(role=UserRole.ADMIN)
    
    all_groups = await db.get_all_groups()
    active_groups = await db.get_all_groups(active_only=True)
    
    text = (
        "👑 <b>Admin Panel</b>\n\n"
        "Xush kelibsiz, admin! Bu yerda botni boshqarishingiz mumkin.\n\n"
        "Kerakli bo'limni tanlang:"
    )
    
    await message.answer(text, reply_markup=get_admin_main_menu())


@router.callback_query(F.data == "admin_stats")
async def show_statistics(callback: CallbackQuery, db: Database):
    """Statistika ko'rsatish"""
    # Get all statistics
    all_users = await db.get_all_users()
    registered_users = [u for u in all_users if u.is_registered]
    admins = await db.get_all_users(role=UserRole.ADMIN)
    regular_users = await db.get_all_users(role=UserRole.USER)
    
    all_groups = await db.get_all_groups()
    active_groups = await db.get_all_groups(active_only=True)
    
    # Count bot roles in groups
    admin_in_groups = sum(1 for g in active_groups if g.bot_is_admin)
    member_in_groups = sum(1 for g in active_groups if not g.bot_is_admin)
    
    # Count chat types
    channels = sum(1 for g in all_groups if g.chat_type.value == "channel")
    supergroups = sum(1 for g in all_groups if g.chat_type.value == "supergroup")
    groups = sum(1 for g in all_groups if g.chat_type.value == "group")
    
    text = (
        "📊 <b>Statistika</b>\n\n"
        "<b>👥 Foydalanuvchilar:</b>\n"
        f"├ Jami: <b>{len(all_users)}</b>\n"
        f"├ Ro'yxatdan o'tgan: <b>{len(registered_users)}</b>\n"
        f"├ Adminlar: <b>{len(admins)}</b>\n"
        f"└ Oddiy userlar: <b>{len(regular_users)}</b>\n\n"
        
        "<b>💬 Guruhlar va Kanallar:</b>\n"
        f"├ Jami: <b>{len(all_groups)}</b>\n"
        f"├ Aktiv: <b>{len(active_groups)}</b>\n"
        f"├ Chiqib ketgan: <b>{len(all_groups) - len(active_groups)}</b>\n\n"
        
        "<b>📢 Tur bo'yicha:</b>\n"
        f"├ Kanallar: <b>{channels}</b>\n"
        f"├ Superguruhlar: <b>{supergroups}</b>\n"
        f"└ Oddiy guruhlar: <b>{groups}</b>\n\n"
        
        "<b>🤖 Bot roli:</b>\n"
        f"├ Admin: <b>{admin_in_groups}</b>\n"
        f"└ Oddiy a'zo: <b>{member_in_groups}</b>"
    )
    
    await callback.message.edit_text(text, reply_markup=get_stats_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("admin_users") | F.data.startswith("users_page_"))
async def show_users_list(callback: CallbackQuery, db: Database):
    """Userlar ro'yxatini ko'rsatish"""
    # Get page number
    if callback.data.startswith("users_page_"):
        page = int(callback.data.split("_")[-1])
    else:
        page = 1
    
    # Get all users
    all_users = await db.get_all_users()
    
    if not all_users:
        await callback.message.edit_text(
            "📭 Hozircha userlar yo'q.",
            reply_markup=get_back_button()
        )
        await callback.answer()
        return
    
    # Calculate pagination
    total_users = len(all_users)
    total_pages = math.ceil(total_users / USERS_PER_PAGE)
    
    # Ensure page is valid
    page = max(1, min(page, total_pages))
    
    # Get users for current page
    start_idx = (page - 1) * USERS_PER_PAGE
    end_idx = start_idx + USERS_PER_PAGE
    page_users = all_users[start_idx:end_idx]
    
    # Format message
    text = f"👥 <b>Foydalanuvchilar</b> (Sahifa {page}/{total_pages})\n\n"
    text += f"Jami: <b>{total_users}</b> ta user\n\n"
    
    for i, user in enumerate(page_users, start=start_idx + 1):
        text += format_user_info(user, i)
        text += "\n"
    
    text += "\n<i>👑 - Admin | 👤 - User\n✅ - Ro'yxatdan o'tgan | ⏳ - Jarayonda</i>"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_users_navigation(page, total_pages)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_groups") | F.data.startswith("groups_page_"))
async def show_groups_list(callback: CallbackQuery, db: Database):
    """Guruhlar ro'yxatini ko'rsatish"""
    # Get page number
    if callback.data.startswith("groups_page_"):
        page = int(callback.data.split("_")[-1])
    else:
        page = 1
    
    # Get all groups
    all_groups = await db.get_all_groups()
    
    if not all_groups:
        await callback.message.edit_text(
            "📭 Hozircha guruhlar yo'q.",
            reply_markup=get_back_button()
        )
        await callback.answer()
        return
    
    # Calculate pagination
    total_groups = len(all_groups)
    total_pages = math.ceil(total_groups / GROUPS_PER_PAGE)
    
    # Ensure page is valid
    page = max(1, min(page, total_pages))
    
    # Get groups for current page
    start_idx = (page - 1) * GROUPS_PER_PAGE
    end_idx = start_idx + GROUPS_PER_PAGE
    page_groups = all_groups[start_idx:end_idx]
    
    # Format message
    text = f"💬 <b>Guruhlar va Kanallar</b> (Sahifa {page}/{total_pages})\n\n"
    text += f"Jami: <b>{total_groups}</b> ta\n\n"
    
    for i, group in enumerate(page_groups, start=start_idx + 1):
        text += format_group_info(group, i)
        text += "\n"
    
    text += "\n<i>💬 - Guruh | 🔷 - Superguruh | 📢 - Kanal\n"
    text += "✅ - Aktiv | ❌ - Chiqib ketgan\n"
    text += "👑 - Bot admin | 👤 - Oddiy a'zo</i>"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_groups_navigation(page, total_pages)
    )
    await callback.answer()


@router.callback_query(F.data == "stats_back")
async def back_from_stats(callback: CallbackQuery):
    """Statistikadan asosiy menyuga qaytish"""
    text = (
        "👑 <b>Admin Panel</b>\n\n"
        "Xush kelibsiz, admin! Bu yerda botni boshqarishingiz mumkin.\n\n"
        "Kerakli bo'limni tanlang:"
    )
    
    await callback.message.edit_text(text, reply_markup=get_admin_main_menu())
    await callback.answer()


@router.callback_query(F.data == "users_back")
async def back_from_users(callback: CallbackQuery, db: Database):
    """Users dan statistikaga qaytish"""
    # Get all statistics
    all_users = await db.get_all_users()
    registered_users = [u for u in all_users if u.is_registered]
    admins = await db.get_all_users(role=UserRole.ADMIN)
    regular_users = await db.get_all_users(role=UserRole.USER)
    
    all_groups = await db.get_all_groups()
    active_groups = await db.get_all_groups(active_only=True)
    
    # Count bot roles in groups
    admin_in_groups = sum(1 for g in active_groups if g.bot_is_admin)
    member_in_groups = sum(1 for g in active_groups if not g.bot_is_admin)
    
    # Count chat types
    channels = sum(1 for g in all_groups if g.chat_type.value == "channel")
    supergroups = sum(1 for g in all_groups if g.chat_type.value == "supergroup")
    groups = sum(1 for g in all_groups if g.chat_type.value == "group")
    
    text = (
        "📊 <b>Statistika</b>\n\n"
        "<b>👥 Foydalanuvchilar:</b>\n"
        f"├ Jami: <b>{len(all_users)}</b>\n"
        f"├ Ro'yxatdan o'tgan: <b>{len(registered_users)}</b>\n"
        f"├ Adminlar: <b>{len(admins)}</b>\n"
        f"└ Oddiy userlar: <b>{len(regular_users)}</b>\n\n"
        
        "<b>💬 Guruhlar va Kanallar:</b>\n"
        f"├ Jami: <b>{len(all_groups)}</b>\n"
        f"├ Aktiv: <b>{len(active_groups)}</b>\n"
        f"├ Chiqib ketgan: <b>{len(all_groups) - len(active_groups)}</b>\n\n"
        
        "<b>📢 Tur bo'yicha:</b>\n"
        f"├ Kanallar: <b>{channels}</b>\n"
        f"├ Superguruhlar: <b>{supergroups}</b>\n"
        f"└ Oddiy guruhlar: <b>{groups}</b>\n\n"
        
        "<b>🤖 Bot roli:</b>\n"
        f"├ Admin: <b>{admin_in_groups}</b>\n"
        f"└ Oddiy a'zo: <b>{member_in_groups}</b>"
    )
    
    await callback.message.edit_text(text, reply_markup=get_stats_keyboard())
    await callback.answer()


@router.callback_query(F.data == "groups_back")
async def back_from_groups(callback: CallbackQuery, db: Database):
    """Groups dan statistikaga qaytish"""
    # Get all statistics
    all_users = await db.get_all_users()
    registered_users = [u for u in all_users if u.is_registered]
    admins = await db.get_all_users(role=UserRole.ADMIN)
    regular_users = await db.get_all_users(role=UserRole.USER)
    
    all_groups = await db.get_all_groups()
    active_groups = await db.get_all_groups(active_only=True)
    
    # Count bot roles in groups
    admin_in_groups = sum(1 for g in active_groups if g.bot_is_admin)
    member_in_groups = sum(1 for g in active_groups if not g.bot_is_admin)
    
    # Count chat types
    channels = sum(1 for g in all_groups if g.chat_type.value == "channel")
    supergroups = sum(1 for g in all_groups if g.chat_type.value == "supergroup")
    groups = sum(1 for g in all_groups if g.chat_type.value == "group")
    
    text = (
        "📊 <b>Statistika</b>\n\n"
        "<b>👥 Foydalanuvchilar:</b>\n"
        f"├ Jami: <b>{len(all_users)}</b>\n"
        f"├ Ro'yxatdan o'tgan: <b>{len(registered_users)}</b>\n"
        f"├ Adminlar: <b>{len(admins)}</b>\n"
        f"└ Oddiy userlar: <b>{len(regular_users)}</b>\n\n"
        
        "<b>💬 Guruhlar va Kanallar:</b>\n"
        f"├ Jami: <b>{len(all_groups)}</b>\n"
        f"├ Aktiv: <b>{len(active_groups)}</b>\n"
        f"├ Chiqib ketgan: <b>{len(all_groups) - len(active_groups)}</b>\n\n"
        
        "<b>📢 Tur bo'yicha:</b>\n"
        f"├ Kanallar: <b>{channels}</b>\n"
        f"├ Superguruhlar: <b>{supergroups}</b>\n"
        f"└ Oddiy guruhlar: <b>{groups}</b>\n\n"
        
        "<b>🤖 Bot roli:</b>\n"
        f"├ Admin: <b>{admin_in_groups}</b>\n"
        f"└ Oddiy a'zo: <b>{member_in_groups}</b>"
    )
    
    await callback.message.edit_text(text, reply_markup=get_stats_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin_close")
async def close_admin_panel(callback: CallbackQuery):
    """Admin panelni yopish"""
    await callback.message.delete()
    await callback.answer("Admin panel yopildi ✅")


@router.callback_query(F.data.in_(["users_current", "groups_current"]))
async def ignore_current_page(callback: CallbackQuery):
    """Current page tugmasini ignore qilish"""
    await callback.answer()


# KiberCoin Management handlers
@router.callback_query(F.data == "admin_coin_management")
async def admin_coin_management(callback: CallbackQuery, db: Database):
    """KiberCoin boshqaruvi menyu"""
    # Get total coins in system
    total_coins = await db.get_total_coins_in_system()
    
    # Get user count
    all_users = await db.get_all_users()
    users_with_coins = sum(1 for u in all_users if u.coins > 0)
    
    text = (
        "💰 <b>KiberCoin Boshqaruvi</b>\n\n"
        f"📊 Tizimda jami: <b>{total_coins} KiberCoin</b>\n"
        f"👥 Coin'li userlar: <b>{users_with_coins}</b>\n\n"
        "Quyidagi tugmalardan birini tanlang:"
    )
    
    await callback.message.edit_text(text, reply_markup=get_coin_management_menu())
    await callback.answer()


@router.callback_query(F.data == "coin_add")
async def coin_add(callback: CallbackQuery, state: FSMContext):
    """Coin qo'shish - telefon raqam so'rash"""
    await state.set_state(CoinManagementStates.waiting_for_phone)
    await state.update_data(action="add")
    
    await callback.message.answer(
        "➕ <b>Coin Qo'shish</b>\n\n"
        "Userlarning telefon raqamlarini yuboring:\n\n"
        "📱 <b>Bir user:</b> +998901234567\n"
        "📱 <b>Ko'p userlar:</b>\n"
        "+998901234567\n"
        "+998909876543\n"
        "+998331234567\n\n"
        "Yoki vergul bilan: +998901234567, +998909876543\n\n"
        "❌ Bekor qilish uchun /cancel yuboring",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "coin_remove")
async def coin_remove(callback: CallbackQuery, state: FSMContext):
    """Coin ayirish - telefon raqam so'rash"""
    await state.set_state(CoinManagementStates.waiting_for_phone)
    await state.update_data(action="remove")
    
    await callback.message.answer(
        "➖ <b>Coin Ayirish</b>\n\n"
        "Userlarning telefon raqamlarini yuboring:\n\n"
        "📱 <b>Bir user:</b> +998901234567\n"
        "📱 <b>Ko'p userlar:</b>\n"
        "+998901234567\n"
        "+998909876543\n"
        "+998331234567\n\n"
        "Yoki vergul bilan: +998901234567, +998909876543\n\n"
        "❌ Bekor qilish uchun /cancel yuboring",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(CoinManagementStates.waiting_for_phone, F.text)
async def process_phone_for_coins(message: Message, state: FSMContext, db: Database):
    """Telefon raqamlarni qabul qilish va userlarni topish"""
    phones_text = message.text.strip()
    
    # Split by comma or newline
    phone_list = []
    for line in phones_text.replace(',', '\n').split('\n'):
        phone = line.strip()
        if phone:
            phone_list.append(phone)
    
    if not phone_list:
        await message.answer("❌ Telefon raqam kiriting!")
        return
    
    # Find all users
    found_users = []
    not_found = []
    
    for phone in phone_list:
        user = await db.get_user_by_phone(phone)
        if user:
            found_users.append({
                'user': user,
                'phone': phone
            })
        else:
            not_found.append(phone)
    
    if not found_users:
        await message.answer(
            f"❌ Hech bir user topilmadi!\n\n"
            f"Topilmagan raqamlar:\n" + "\n".join(not_found) + "\n\n"
            "Boshqa raqamlar kiriting yoki /cancel yuboring."
        )
        return
    
    # Save user_ids to state
    user_ids = [u['user'].id for u in found_users]
    user_names = [u['user'].preferred_name or u['user'].first_name for u in found_users]
    
    is_bulk = len(found_users) > 1
    if is_bulk:
        await state.update_data(
            user_ids=user_ids,
            user_names=user_names,
            is_bulk=True
        )
    else:
        # Single user uchun user_id va user_name ni saqlash
        await state.update_data(
            user_id=found_users[0]['user'].id,
            user_name=found_users[0]['user'].preferred_name or found_users[0]['user'].first_name,
            is_bulk=False
        )
    
    # Show found users
    state_data = await state.get_data()
    action = state_data.get("action")
    action_text = "qo'shmoqchisiz" if action == "add" else "ayirmoqchisiz"
    
    result_text = f"✅ <b>{len(found_users)} ta user topildi:</b>\n\n"
    
    for item in found_users:
        user = item['user']
        result_text += f"👤 {user.preferred_name or user.first_name}\n"
        result_text += f"   💰 Balans: {user.coins} KiberCoin\n"
        result_text += f"   📱 {item['phone']}\n\n"
    
    if not_found:
        result_text += f"❌ <b>Topilmagan raqamlar:</b>\n" + "\n".join(not_found) + "\n\n"
    
    result_text += f"Hamma userlarga nechta KiberCoin {action_text}?\n"
    result_text += "Masalan: 100\n\n"
    result_text += "❌ Bekor qilish uchun /cancel yuboring"
    
    await message.answer(result_text, parse_mode="HTML")
    await state.set_state(CoinManagementStates.waiting_for_amount)


@router.message(CoinManagementStates.waiting_for_amount, F.text)
async def process_coin_amount(message: Message, state: FSMContext, db: Database):
    """Coin miqdorini qabul qilish va amalga oshirish"""
    try:
        amount = int(message.text.strip())
        if amount <= 0:
            await message.answer("❌ Musbat son kiriting!")
            return
    except ValueError:
        await message.answer("❌ Faqat raqam kiriting!")
        return
    
    state_data = await state.get_data()
    is_bulk = state_data.get("is_bulk", False)
    action = state_data.get("action")
    
    # Get admin user
    admin = await db.get_user(message.from_user.id)
    
    if is_bulk:
        # Multiple users
        user_ids = state_data.get("user_ids", [])
        user_names = state_data.get("user_names", [])
        
        success_count = 0
        failed_count = 0
        
        for user_id, user_name in zip(user_ids, user_names):
            if action == "add":
                success = await db.add_coins(
                    user_id=user_id,
                    amount=amount,
                    transaction_type=TransactionType.ADMIN_ADD,
                    description=f"Admin tomonidan qo'shildi (bulk)",
                    admin_id=admin.id
                )
            else:  # remove
                success = await db.remove_coins(
                    user_id=user_id,
                    amount=amount,
                    description=f"Admin tomonidan olib tashlandi (bulk)",
                    admin_id=admin.id
                )
            
            if success:
                success_count += 1
            else:
                failed_count += 1
        
        action_symbol = "➕" if action == "add" else "➖"
        action_word = "qo'shildi" if action == "add" else "olib tashlandi"
        
        await message.answer(
            f"✅ <b>Bulk operatsiya yakunlandi!</b>\n\n"
            f"{action_symbol} Miqdor: <b>{amount} KiberCoin</b>\n"
            f"👥 Jami userlar: <b>{len(user_ids)}</b>\n"
            f"✅ Muvaffaqiyatli: <b>{success_count}</b>\n"
            f"❌ Xatolik: <b>{failed_count}</b>\n\n"
            f"Barcha userlarga {amount} KiberCoin {action_word}!",
            parse_mode="HTML"
        )
    
    else:
        # Single user
        user_id = state_data.get("user_id")
        user_name = state_data.get("user_name")
        
        if action == "add":
            # Add coins
            success = await db.add_coins(
                user_id=user_id,
                amount=amount,
                transaction_type=TransactionType.ADMIN_ADD,
                description=f"Admin tomonidan qo'shildi",
                admin_id=admin.id
            )
            
            if success:
                # Get updated user
                async with db.session_maker() as session:
                    from sqlalchemy import select
                    from bot.database.models import User
                    result = await session.execute(select(User).where(User.id == user_id))
                    user = result.scalar_one_or_none()
                
                await message.answer(
                    f"✅ Muvaffaqiyatli!\n\n"
                    f"👤 User: <b>{user_name}</b>\n"
                    f"➕ Qo'shildi: <b>{amount} KiberCoin</b>\n"
                    f"💰 Yangi balans: <b>{user.coins} KiberCoin</b>",
                    parse_mode="HTML"
                )
            else:
                await message.answer("❌ Xatolik yuz berdi!")
        
        else:  # remove
            # Remove coins
            success = await db.remove_coins(
                user_id=user_id,
                amount=amount,
                description=f"Admin tomonidan olib tashlandi",
                admin_id=admin.id
            )
            
            if success:
                # Get updated user
                async with db.session_maker() as session:
                    from sqlalchemy import select
                    from bot.database.models import User
                    result = await session.execute(select(User).where(User.id == user_id))
                    user = result.scalar_one_or_none()
                
                await message.answer(
                    f"✅ Muvaffaqiyatli!\n\n"
                    f"👤 User: <b>{user_name}</b>\n"
                    f"➖ Olib tashlandi: <b>{amount} KiberCoin</b>\n"
                    f"💰 Yangi balans: <b>{user.coins} KiberCoin</b>",
                    parse_mode="HTML"
                )
            else:
                await message.answer("❌ Xatolik yuz berdi!")
    
    await state.clear()


@router.callback_query(F.data.startswith("coin_transactions") | F.data.startswith("transactions_page_"))
async def show_all_transactions(callback: CallbackQuery, db: Database):
    """Barcha tranzaksiyalarni ko'rsatish"""
    # Parse page number
    page = 1
    if callback.data.startswith("transactions_page_"):
        page = int(callback.data.split("_")[-1])
    
    # Get all transactions
    all_transactions = await db.get_transactions(limit=1000)
    
    # Pagination
    items_per_page = 10
    total_pages = max(1, math.ceil(len(all_transactions) / items_per_page))
    page = max(1, min(page, total_pages))
    
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_transactions = all_transactions[start_idx:end_idx]
    
    if not page_transactions:
        await callback.answer("📭 Tranzaksiyalar yo'q", show_alert=True)
        return
    
    text = f"📊 <b>Barcha Tranzaksiyalar</b> (Sahifa {page}/{total_pages})\n\n"
    
    for tx in page_transactions:
        # Get user info
        async with db.session_maker() as session:
            from sqlalchemy import select
            from bot.database.models import User
            result = await session.execute(select(User).where(User.id == tx.user_id))
            user = result.scalar_one_or_none()
        
        amount_str = f"+{tx.amount}" if tx.amount > 0 else str(tx.amount)
        emoji = "💰" if tx.amount > 0 else "💸"
        
        type_name = {
            "referral_bonus": "Referal bonus",
            "admin_add": "Admin qo'shdi",
            "admin_remove": "Admin ayirdi"
        }.get(tx.transaction_type.value, "Noma'lum")
        
        user_name = user.preferred_name or user.first_name if user else "Noma'lum"
        date_str = tx.created_at.strftime("%d.%m.%Y %H:%M")
        
        text += f"{emoji} <b>{amount_str}</b> - {user_name}\n"
        text += f"   {type_name} - {date_str}\n"
        if tx.description:
            text += f"   💬 {tx.description}\n"
        text += "\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_transactions_navigation(page, total_pages),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "transactions_back")
async def transactions_back(callback: CallbackQuery, db: Database):
    """Tranzaksiyalardan coin management'ga qaytish"""
    await admin_coin_management(callback, db)


@router.callback_query(F.data == "coin_back")
async def coin_back_to_admin(callback: CallbackQuery, db: Database):
    """Coin management'dan admin panelga qaytish"""
    text = (
        "👑 <b>Admin Panel</b>\n\n"
        "Xush kelibsiz, admin! Bu yerda botni boshqarishingiz mumkin.\n\n"
        "Kerakli bo'limni tanlang:"
    )
    
    await callback.message.edit_text(text, reply_markup=get_admin_main_menu())
    await callback.answer()


@router.message(Command("cancel"))
async def cancel_coin_operation(message: Message, state: FSMContext):
    """Coin operatsiyasini bekor qilish"""
    current_state = await state.get_state()
    if current_state is None:
        return
    
    await state.clear()
    await message.answer(
        "❌ Operatsiya bekor qilindi!",
        parse_mode="HTML"
    )
