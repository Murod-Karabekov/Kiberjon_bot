from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_admin_main_menu() -> InlineKeyboardMarkup:
    """Admin asosiy menyu"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
            [InlineKeyboardButton(text="📢 Broadcast", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text="❌ Yopish", callback_data="admin_close")]
        ]
    )
    return keyboard


def get_stats_keyboard() -> InlineKeyboardMarkup:
    """Statistika sahifasi klaviaturasi"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👥 Users", callback_data="admin_users"),
                InlineKeyboardButton(text="💬 Groups", callback_data="admin_groups")
            ],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="stats_back")]
        ]
    )
    return keyboard


def get_back_button() -> InlineKeyboardMarkup:
    """Orqaga qaytish tugmasi"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_back")]
        ]
    )
    return keyboard


def get_users_navigation(page: int = 1, total_pages: int = 1) -> InlineKeyboardMarkup:
    """Users ro'yxati uchun navigatsiya"""
    buttons = []
    
    # Navigation buttons
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="◀️", callback_data=f"users_page_{page-1}"))
    
    nav_row.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="users_current"))
    
    if page < total_pages:
        nav_row.append(InlineKeyboardButton(text="▶️", callback_data=f"users_page_{page+1}"))
    
    if nav_row:
        buttons.append(nav_row)
    
    # Back button
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="users_back")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_groups_navigation(page: int = 1, total_pages: int = 1) -> InlineKeyboardMarkup:
    """Groups ro'yxati uchun navigatsiya"""
    buttons = []
    
    # Navigation buttons
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="◀️", callback_data=f"groups_page_{page-1}"))
    
    nav_row.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="groups_current"))
    
    if page < total_pages:
        nav_row.append(InlineKeyboardButton(text="▶️", callback_data=f"groups_page_{page+1}"))
    
    if nav_row:
        buttons.append(nav_row)
    
    # Back button
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="groups_back")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_broadcast_target_keyboard() -> InlineKeyboardMarkup:
    """Broadcast yuborish uchun target tanlash"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👥 Users", callback_data="broadcast_users"),
                InlineKeyboardButton(text="💬 Groups", callback_data="broadcast_groups")
            ],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="broadcast_cancel")]
        ]
    )
    return keyboard
