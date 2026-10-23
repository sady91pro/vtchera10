from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def admin_menu(is_super: bool = False) -> InlineKeyboardMarkup:
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
    kb.add(InlineKeyboardButton(
        "🎉 Объявить победителей", callback_data="adm:announce"
    ))
    kb.add(InlineKeyboardButton("🗑 Сбросить голоса", callback_data="adm:reset"))
    kb.add(InlineKeyboardButton(
        "❌ Удалить всех участников", callback_data="adm:delall"
    ))
    kb.add(InlineKeyboardButton("🔀 Перемешать порядок", callback_data="adm:shuffle"))
    if is_super:
        kb.add(InlineKeyboardButton(
            "👥 Управление админами", callback_data="adm:admins"
        ))
        kb.add(InlineKeyboardButton("📜 Аудит-лог", callback_data="adm:audit"))
    return kb
