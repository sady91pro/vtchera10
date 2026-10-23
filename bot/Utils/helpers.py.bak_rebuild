import json
from aiogram.types import CallbackQuery, InputMediaPhoto
from bot.Services import db
from bot.Keyboards.user_kb import vote_keyboard


def photos_of(row) -> list:
    """row: (id, name, photo_id, photo_ids_json) или старый (id, name, photo_id)."""
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
        f"<b>{name}</b>\n"
        f"Карточка {idx + 1} из {len(parts)}{extra}"
    )
    kb = vote_keyboard(idx, len(parts), pid, photos_count=len(photos))

    if isinstance(target, CallbackQuery) and edit:
        try:
            await msg.edit_media(
                InputMediaPhoto(media=primary, caption=caption),
                reply_markup=kb,
            )
            return
        except Exception:
            pass

    await msg.answer_photo(primary, caption=caption, reply_markup=kb)


async def send_results(target):
    rows = await db.get_results()
    msg = target.message if isinstance(target, CallbackQuery) else target

    if not rows:
        await msg.answer("Пока нет участников.")
        return

    total = sum(r[2] for r in rows)
    medals = ["🥇", "🥈", "🥉"]
    lines = ["🏆 <b>Результаты голосования</b>\n"]
    for i, (_, name, cnt) in enumerate(rows):
        prefix = medals[i] if i < 3 else f"{i + 1}."
        pct = f" ({cnt * 100 // total}%)" if total else ""
        lines.append(f"{prefix} {name} — {cnt}{pct}")
    lines.append(f"\nВсего голосов: <b>{total}</b>")
    await msg.answer("\n".join(lines))
