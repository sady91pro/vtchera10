from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def vote_keyboard(idx: int, total: int, pid: int) -> InlineKeyboardMarkup:
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
    return kb
