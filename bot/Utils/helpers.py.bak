from aiogram.types import CallbackQuery, InputMediaPhoto
from bot.Services import db
from bot.Keyboards.user_kb import vote_keyboard


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
    pid, name, photo = parts[idx]
    caption = f"<b>{name}</b>\nКарточка {idx + 1} из {len(parts)}"
    kb = vote_keyboard(idx, len(parts), pid)

    if isinstance(target, CallbackQuery) and edit:
        try:
            await msg.edit_media(
                InputMediaPhoto(media=photo, caption=caption),
                reply_markup=kb,
            )
            return
        except Exception:
            pass

    await msg.answer_photo(photo, caption=caption, reply_markup=kb)


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
