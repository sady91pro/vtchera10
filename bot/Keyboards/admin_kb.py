from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def admin_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("➕ Добавить участника", callback_data="adm:add"))
    kb.add(InlineKeyboardButton(
        "📋 Управление участниками", callback_data="adm:list"
    ))
    kb.add(
        InlineKeyboardButton("🟢 Открыть", callback_data="adm:open"),
        InlineKeyboardButton("🔴 Закрыть", callback_data="adm:close"),
    )
    kb.add(InlineKeyboardButton("📊 Результаты", callback_data="adm:results"))
    kb.add(InlineKeyboardButton("🗑 Сбросить голоса", callback_data="adm:reset"))
    kb.add(InlineKeyboardButton(
        "❌ Удалить всех участников", callback_data="adm:delall"
    ))
    kb.add(InlineKeyboardButton("👥 Управление админами", callback_data="adm:admins"))
    return kb
