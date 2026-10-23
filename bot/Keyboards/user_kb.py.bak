from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def vote_keyboard(idx: int, total: int, pid: int,
                  photos_count: int = 1) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    nav = []
    if idx > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"pg:{idx - 1}"))
    if idx < total - 1:
        nav.append(InlineKeyboardButton("➡️", callback_data=f"pg:{idx + 1}"))
    if nav:
        kb.row(*nav)
    kb.add(InlineKeyboardButton(
        "🗳 Голосовать за этого", callback_data=f"vote:{pid}"
    ))
    if photos_count > 1:
        kb.add(InlineKeyboardButton(
            f"🖼 Все фото ({photos_count})",
            callback_data=f"photos:{pid}",
        ))
    return kb
