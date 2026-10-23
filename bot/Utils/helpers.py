import json
import logging
from html import escape

from aiogram.types import CallbackQuery, InputMediaPhoto
from bot.Services import db
from bot.Keyboards.user_kb import vote_keyboard

MAX_MESSAGE_LENGTH = 4000


def esc(s) -> str:
    if s is None:
        return ""
    return escape(str(s), quote=False)


def split_text(text: str, limit: int = None) -> list:
    limit = limit or MAX_MESSAGE_LENGTH
    if len(text) <= limit:
        return [text]
    parts = []
    current = ""
    for line in text.split("\n"):
        candidate = (current + "\n" + line) if current else line
        if len(candidate) <= limit:
            current = candidate
        else:
            if current:
                parts.append(current)
                current = ""
            while len(line) > limit:
                parts.append(line[:limit])
                line = line[limit:]
            current = line
    if current:
        parts.append(current)
    return parts


async def safe_send(target, text: str, **kwargs):
    msg = target.message if isinstance(target, CallbackQuery) else target
    for part in split_text(text):
        try:
            await msg.answer(part, **kwargs)
        except Exception as e:
            logging.error(f"send failed: {e}")


def photos_of(row) -> list:
    if len(row) >= 4 and row[3]:
        try:
            lst = json.loads(row[3])
            if lst:
                return lst
        except Exception:
            pass
    return [row[2]]


async def render_participant(target, idx: int, edit: bool = False):
    parts = await db.get_participants()
    if isinstance(target, CallbackQuery):
        msg = target.message
    else:
        msg = target
    if not parts:
        await msg.answer("Участников пока нет.")
        return
    idx = max(0, min(idx, len(parts) - 1))
    row = parts[idx]
    pid, name = row[0], row[1]
    photos = photos_of(row)
    primary = photos[0]
    extra = f" • {len(photos)} фото" if len(photos) > 1 else ""
    caption = (
        f"<b>{esc(name)}</b>\n"
        f"Карточка {idx + 1} из {len(parts)}{extra}"
    )[:1024]
    kb = vote_keyboard(idx, len(parts), pid, photos_count=len(photos))
    if isinstance(target, CallbackQuery) and edit:
        try:
            await msg.edit_media(
                InputMediaPhoto(media=primary, caption=caption),
                reply_markup=kb,
            )
            return
        except Exception as e:
            logging.warning(f"edit_media failed: {e}")
    await msg.answer_photo(primary, caption=caption, reply_markup=kb)


async def send_results(target):
    rows = await db.get_results()
    if not rows:
        return await safe_send(target, "Пока нет участников.")
    total = sum(r[2] for r in rows)
    medals = ["🥇", "🥈", "🥉"]
    lines = ["🏆 <b>Результаты голосования</b>\n"]
    for i, (_, name, cnt) in enumerate(rows):
        prefix = medals[i] if i < 3 else f"{i + 1}."
        pct = f" ({cnt * 100 // total}%)" if total else ""
        lines.append(f"{prefix} {esc(name)} — {cnt}{pct}")
    lines.append(f"\nВсего голосов: <b>{total}</b>")
    await safe_send(target, "\n".join(lines))
