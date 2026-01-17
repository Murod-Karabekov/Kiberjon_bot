import asyncio
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from bot.database.database import Database
from bot.database.models import UserRole
from bot.keyboards.inline import get_broadcast_target_keyboard
from bot.states.broadcast import BroadcastStates

router = Router()


@router.callback_query(F.data == "admin_broadcast")
async def start_broadcast(callback: CallbackQuery, state: FSMContext, db: Database):
    """Broadcast jarayonini boshlash"""
    telegram_id = callback.from_user.id
    user = await db.get_user(telegram_id)
    
    # Check if user is admin
    if not user or user.role != UserRole.ADMIN:
        await callback.answer("❌ Sizda admin huquqi yo'q!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📢 <b>Broadcast</b>\n\n"
        "Yubormoqchi bo'lgan kontentingizni yuboring:\n\n"
        "✅ Matn\n"
        "✅ Rasm\n"
        "✅ Video\n"
        "✅ Audio/Musiqa\n"
        "✅ Dokument/Fayl\n"
        "✅ Voice/Video xabar\n"
        "✅ Sticker\n"
        "✅ Aralash (matn + media)\n\n"
        "Kontentni yuboring:"
    )
    
    await state.set_state(BroadcastStates.waiting_for_content)
    await callback.answer()


@router.message(BroadcastStates.waiting_for_content)
async def receive_broadcast_content(message: Message, state: FSMContext):
    """Broadcast kontentini qabul qilish"""
    # Save message_id and chat_id for later copying
    await state.update_data(
        message_id=message.message_id,
        chat_id=message.chat.id
    )
    
    # Determine content type
    content_type = "noma'lum"
    if message.text:
        content_type = "📝 Matn"
    elif message.photo:
        content_type = "🖼 Rasm" + (" + matn" if message.caption else "")
    elif message.video:
        content_type = "🎥 Video" + (" + matn" if message.caption else "")
    elif message.audio:
        content_type = "🎵 Audio" + (" + matn" if message.caption else "")
    elif message.voice:
        content_type = "🎤 Voice xabar"
    elif message.video_note:
        content_type = "📹 Video xabar"
    elif message.document:
        content_type = "📎 Fayl" + (" + matn" if message.caption else "")
    elif message.sticker:
        content_type = "🎭 Sticker"
    elif message.animation:
        content_type = "🎞 GIF" + (" + matn" if message.caption else "")
    
    await message.answer(
        f"✅ Kontent qabul qilindi!\n\n"
        f"Turi: {content_type}\n\n"
        f"Kimga yuborish kerak?",
        reply_markup=get_broadcast_target_keyboard()
    )


@router.callback_query(F.data == "broadcast_users")
async def broadcast_to_users(callback: CallbackQuery, state: FSMContext, db: Database):
    """Barcha userlarga yuborish"""
    data = await state.get_data()
    message_id = data.get("message_id")
    chat_id = data.get("chat_id")
    
    if not message_id or not chat_id:
        await callback.answer("❌ Xatolik! Qaytadan urinib ko'ring.", show_alert=True)
        await state.clear()
        return
    
    # Get all registered users
    all_users = await db.get_all_users()
    registered_users = [u for u in all_users if u.is_registered]
    
    await callback.message.edit_text(
        f"📤 Yuborilmoqda...\n\n"
        f"Jami: {len(registered_users)} ta user\n\n"
        f"⏳ Iltimos kuting..."
    )
    
    success = 0
    failed = 0
    
    for user in registered_users:
        try:
            # Copy message (special forward without "Forwarded from")
            await callback.bot.copy_message(
                chat_id=user.telegram_id,
                from_chat_id=chat_id,
                message_id=message_id
            )
            success += 1
            
            # Small delay to avoid flood limits
            await asyncio.sleep(0.05)
            
        except Exception as e:
            failed += 1
            # Silently continue on error (user blocked bot, deleted account, etc.)
            continue
    
    await callback.message.edit_text(
        f"✅ <b>Broadcast yakunlandi!</b>\n\n"
        f"👥 Target: <b>Users</b>\n\n"
        f"📊 Natijalar:\n"
        f"├ Muvaffaqiyatli: <b>{success}</b>\n"
        f"├ Muvaffaqiyatsiz: <b>{failed}</b>\n"
        f"└ Jami: <b>{len(registered_users)}</b>\n\n"
        f"✨ Barcha foydalanuvchilarga yetkazildi!"
    )
    
    await state.clear()
    await callback.answer("✅ Yuborildi!")


@router.callback_query(F.data == "broadcast_groups")
async def broadcast_to_groups(callback: CallbackQuery, state: FSMContext, db: Database):
    """Barcha guruh va kanallarga yuborish"""
    data = await state.get_data()
    message_id = data.get("message_id")
    chat_id = data.get("chat_id")
    
    if not message_id or not chat_id:
        await callback.answer("❌ Xatolik! Qaytadan urinib ko'ring.", show_alert=True)
        await state.clear()
        return
    
    # Get all active groups
    active_groups = await db.get_all_groups(active_only=True)
    
    if not active_groups:
        await callback.answer("❌ Aktiv guruhlar topilmadi!", show_alert=True)
        await state.clear()
        return
    
    await callback.message.edit_text(
        f"📤 Yuborilmoqda...\n\n"
        f"Jami: {len(active_groups)} ta guruh/kanal\n\n"
        f"⏳ Iltimos kuting..."
    )
    
    success = 0
    failed = 0
    
    for group in active_groups:
        try:
            # Copy message (special forward without "Forwarded from")
            await callback.bot.copy_message(
                chat_id=group.chat_id,
                from_chat_id=chat_id,
                message_id=message_id
            )
            success += 1
            
            # Delay to avoid flood limits
            await asyncio.sleep(0.1)
            
        except Exception as e:
            failed += 1
            # If bot was removed or doesn't have permissions
            # Optionally deactivate the group
            if "bot was kicked" in str(e).lower() or "chat not found" in str(e).lower():
                await db.deactivate_group(group.chat_id)
            continue
    
    await callback.message.edit_text(
        f"✅ <b>Broadcast yakunlandi!</b>\n\n"
        f"💬 Target: <b>Groups/Channels</b>\n\n"
        f"📊 Natijalar:\n"
        f"├ Muvaffaqiyatli: <b>{success}</b>\n"
        f"├ Muvaffaqiyatsiz: <b>{failed}</b>\n"
        f"└ Jami: <b>{len(active_groups)}</b>\n\n"
        f"✨ Barcha guruh va kanallarga yetkazildi!"
    )
    
    await state.clear()
    await callback.answer("✅ Yuborildi!")


@router.callback_query(F.data == "broadcast_cancel")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    """Broadcastni bekor qilish"""
    await state.clear()
    
    await callback.message.edit_text(
        "❌ Broadcast bekor qilindi.\n\n"
        "Admin panelga qaytish uchun /admin buyrug'ini ishlating."
    )
    
    await callback.answer("Bekor qilindi")
