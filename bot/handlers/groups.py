import json
from aiogram import Router, F
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters import ChatMemberUpdatedFilter, ADMINISTRATOR, MEMBER, LEFT
from bot.database.database import Database
from bot.database.models import ChatType

router = Router()


def get_chat_type(chat_type_str: str) -> ChatType:
    """Convert Telegram chat type to ChatType enum"""
    type_map = {
        "group": ChatType.GROUP,
        "supergroup": ChatType.SUPERGROUP,
        "channel": ChatType.CHANNEL
    }
    return type_map.get(chat_type_str, ChatType.GROUP)


def get_bot_permissions(member) -> str:
    """Extract bot permissions as JSON string"""
    if not hasattr(member, 'can_be_edited'):
        return json.dumps({"is_admin": False})
    
    permissions = {
        "is_admin": member.status in ["creator", "administrator"],
        "can_be_edited": getattr(member, 'can_be_edited', False),
        "can_manage_chat": getattr(member, 'can_manage_chat', False),
        "can_delete_messages": getattr(member, 'can_delete_messages', False),
        "can_manage_video_chats": getattr(member, 'can_manage_video_chats', False),
        "can_restrict_members": getattr(member, 'can_restrict_members', False),
        "can_promote_members": getattr(member, 'can_promote_members', False),
        "can_change_info": getattr(member, 'can_change_info', False),
        "can_invite_users": getattr(member, 'can_invite_users', False),
        "can_post_messages": getattr(member, 'can_post_messages', False),
        "can_edit_messages": getattr(member, 'can_edit_messages', False),
        "can_pin_messages": getattr(member, 'can_pin_messages', False),
    }
    return json.dumps(permissions, ensure_ascii=False)


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER | ADMINISTRATOR))
async def bot_added_to_chat(event: ChatMemberUpdated, db: Database):
    """Bot guruhga qo'shilganda yoki admin qilinganda"""
    chat = event.chat
    new_member = event.new_chat_member
    
    # Check if bot is admin
    bot_is_admin = new_member.status in ["creator", "administrator"]
    
    # Get chat type
    chat_type = get_chat_type(chat.type)
    
    # Get bot permissions
    permissions = get_bot_permissions(new_member)
    
    # Get member count
    try:
        member_count = await event.bot.get_chat_member_count(chat.id)
    except:
        member_count = None
    
    # Get chat description
    try:
        full_chat = await event.bot.get_chat(chat.id)
        description = full_chat.description
    except:
        description = None
    
    # Check if group already exists in database
    existing_group = await db.get_group(chat.id)
    
    if existing_group:
        # Reactivate if it was deactivated
        if not existing_group.is_active:
            await db.reactivate_group(chat.id)
        
        # Update group info
        await db.update_group(
            chat_id=chat.id,
            title=chat.title,
            username=chat.username,
            description=description,
            bot_is_admin=bot_is_admin,
            bot_permissions=permissions,
            member_count=member_count
        )
    else:
        # Create new group record
        await db.create_group(
            chat_id=chat.id,
            title=chat.title,
            chat_type=chat_type,
            username=chat.username,
            description=description,
            bot_is_admin=bot_is_admin,
            bot_permissions=permissions,
            member_count=member_count
        )
    
    # Send welcome message
    role_text = "admin" if bot_is_admin else "oddiy a'zo"
    await event.answer(
        f"✅ Assalomu alaykum!\n\n"
        f"Men {chat.title} guruhiga qo'shildim.\n"
        f"Mening rolim: {role_text}\n\n"
        f"Guruh ma'lumotlari bazaga saqlandi! 📊"
    )


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=LEFT))
async def bot_removed_from_chat(event: ChatMemberUpdated, db: Database):
    """Bot guruhdan chiqarilganda yoki o'zi chiqqanda"""
    chat = event.chat
    
    # Deactivate group but keep data
    await db.deactivate_group(chat.id)


@router.message(F.chat.type.in_(["group", "supergroup"]))
async def group_message_handler(message: Message, db: Database):
    """Guruhda xabar yuborilganda guruh ma'lumotlarini yangilash"""
    chat = message.chat
    
    # Check if group exists
    group = await db.get_group(chat.id)
    
    if not group:
        # If group doesn't exist, create it
        # Get bot member info
        try:
            bot_member = await message.bot.get_chat_member(chat.id, message.bot.id)
            bot_is_admin = bot_member.status in ["creator", "administrator"]
            permissions = get_bot_permissions(bot_member)
        except:
            bot_is_admin = False
            permissions = json.dumps({"is_admin": False})
        
        # Get member count
        try:
            member_count = await message.bot.get_chat_member_count(chat.id)
        except:
            member_count = None
        
        # Get description
        try:
            full_chat = await message.bot.get_chat(chat.id)
            description = full_chat.description
        except:
            description = None
        
        await db.create_group(
            chat_id=chat.id,
            title=chat.title,
            chat_type=get_chat_type(chat.type),
            username=chat.username,
            description=description,
            bot_is_admin=bot_is_admin,
            bot_permissions=permissions,
            member_count=member_count
        )
    else:
        # Update title if changed
        if group.title != chat.title:
            await db.update_group(chat_id=chat.id, title=chat.title)


@router.message(F.chat.type == "channel")
async def channel_message_handler(message: Message, db: Database):
    """Kanalda xabar yuborilganda kanal ma'lumotlarini yangilash"""
    chat = message.chat
    
    # Check if channel exists
    channel = await db.get_group(chat.id)
    
    if not channel:
        # Get member count
        try:
            member_count = await message.bot.get_chat_member_count(chat.id)
        except:
            member_count = None
        
        # Get description
        try:
            full_chat = await message.bot.get_chat(chat.id)
            description = full_chat.description
        except:
            description = None
        
        # Bot in channels is always admin
        await db.create_group(
            chat_id=chat.id,
            title=chat.title,
            chat_type=ChatType.CHANNEL,
            username=chat.username,
            description=description,
            bot_is_admin=True,
            bot_permissions=json.dumps({"is_admin": True, "can_post_messages": True}),
            member_count=member_count
        )
