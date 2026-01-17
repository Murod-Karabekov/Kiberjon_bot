from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from bot.database.database import Database
from bot.database.models import UserRole
from bot.keyboards.inline import (
    get_admin_main_menu,
    get_stats_keyboard,
    get_back_button,
    get_users_navigation,
    get_groups_navigation
)
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
