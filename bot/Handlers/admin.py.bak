import asyncio
import csv
import io
from datetime import datetime, timezone
from collections import Counter

from aiogram import Dispatcher
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ContentTypes, InputFile,
)

from bot.Services import db
from bot.State.states import AddParticipant, Broadcast, AddAdmin
from bot.Keyboards.admin_kb import admin_menu
from bot.Middleware.admin_filter import IsAdmin, IsSuperAdmin
from bot.Utils.helpers import send_results
from bot.config import ADMIN_IDS, SUPERADMIN_IDS


# ------------------ утилиты ------------------

def _fmt_time(utc_str):
    """SQLite отдаёт UTC → показываем локально."""
    try:
        dt = datetime.strptime(utc_str, "%Y-%m-%d %H:%M:%S")
        dt = dt.replace(tzinfo=timezone.utc).astimezone()
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return utc_str


def _fmt_user(uid, username, full_name):
    if username:
        return f"@{username} (<code>{uid}</code>)"
    if full_name:
        return f"{full_name} (<code>{uid}</code>)"
    return f"<code>{uid}</code>"


async def _ensure_user_info(bot, uid, username, full_name):
    """Если username нет в БД — подтянуть через API и сохранить."""
    if username or full_name:
        return username, full_name
    try:
        chat = await bot.get_chat(uid)
        uname = chat.username
        fname = chat.full_name or ""
        await db.update_vote_user_info(uid, uname, fname)
        return uname, fname
    except Exception:
        return username, full_name


# ------------------ /admin ------------------

async def cmd_admin(message: Message):
    status = "🟢 открыто" if await db.is_open() else "🔴 закрыто"
    await message.answer(
        f"Админ-панель (статус: {status}):",
        reply_markup=admin_menu(),
    )


# ------------------ добавление участника ------------------

async def adm_add(call: CallbackQuery, state):
    await AddParticipant.name.set()
    await call.message.answer("Введите имя участника (или /cancel):")
    await call.answer()


async def add_name(message: Message, state):
    await state.update_data(name=message.text.strip())
    await AddParticipant.photo.set()
    await message.answer("Теперь отправьте фото участника:")


async def add_photo(message: Message, state):
    data = await state.get_data()
    await db.add_participant(data["name"], message.photo[-1].file_id)
    await state.finish()
    await message.answer(
        f"✅ Участник «{data['name']}» добавлен.\n"
        f"Добавить ещё — /admin"
    )


async def add_photo_wrong(message: Message):
    await message.answer("Нужно отправить именно фото (не файл, не текст).")


async def cmd_cancel(message: Message, state):
    await state.finish()
    await message.answer("Отменено.")


# ------------------ управление ------------------

async def adm_open(call: CallbackQuery):
    await db.set_open(True)
    await call.message.answer("🟢 Голосование открыто. Пользователи могут /vote")
    await call.answer()


async def adm_close(call: CallbackQuery):
    await db.set_open(False)
    await call.message.answer("🔴 Голосование закрыто.")
    await call.answer()


async def adm_list(call: CallbackQuery):
    parts = await db.get_participants()
    if not parts:
        return await call.message.answer(
            "Список пуст. Добавьте участников через ➕."
        )

    kb = InlineKeyboardMarkup(row_width=1)
    for pid, name, _ in parts:
        kb.add(InlineKeyboardButton(
            f"🗑 {name}", callback_data=f"adm:del:{pid}"
        ))
    kb.add(InlineKeyboardButton(
        "❌ УДАЛИТЬ ВСЕХ", callback_data="adm:delall"
    ))

    await call.message.answer(
        f"📋 <b>Участники</b> ({len(parts)}):\n"
        f"Нажмите 🗑 рядом с именем, чтобы удалить участника "
        f"и все голоса за него.",
        reply_markup=kb,
    )
    await call.answer()


async def adm_del(call: CallbackQuery):
    try:
        pid = int(call.data.split(":")[2])
    except (IndexError, ValueError):
        return await call.answer()

    p = await db.get_participant(pid)
    if not p:
        return await call.answer("Участник уже удалён", show_alert=True)

    name = p[1]
    await db.delete_participant(pid)

    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await call.message.answer(
        f"🗑 Участник «{name}» (id={pid}) удалён.\n"
        f"Голоса за него также очищены."
    )
    await call.answer(f"Удалён: {name}", show_alert=True)


async def adm_delall(call: CallbackQuery):
    parts = await db.get_participants()
    if not parts:
        return await call.answer("Список уже пуст", show_alert=True)

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            "✅ Да, удалить ВСЕХ", callback_data="adm:delall:yes"
        ),
        InlineKeyboardButton("❌ Отмена", callback_data="adm:delall:no"),
    ]])
    await call.message.answer(
        f"⚠️ <b>Удалить всех участников?</b>\n\n"
        f"Будет удалено: <b>{len(parts)}</b> участник(ов)\n"
        f"Также будут удалены <b>все голоса</b> за них.\n\n"
        f"Действие необратимо.",
        reply_markup=kb,
    )
    await call.answer()


async def adm_delall_yes(call: CallbackQuery):
    cnt = await db.delete_all_participants()
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await call.message.answer(
        f"🗑 Удалено участников: <b>{cnt}</b>.\n"
        f"Все голоса также очищены."
    )
    await call.answer()


async def adm_delall_no(call: CallbackQuery):
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await call.message.answer("❌ Удаление отменено.")
    await call.answer("Отменено")


async def adm_results(call: CallbackQuery):
    await send_results(call.message)
    await call.answer()


async def adm_reset(call: CallbackQuery):
    await db.reset_votes()
    await call.message.answer("🗑 Все голоса сброшены.")
    await call.answer()


# ------------------ /votes ------------------

async def cmd_votes(message: Message):
    rows = await db.get_votes_detailed()
    if not rows:
        return await message.answer("Голосов пока нет.")

    enriched = []
    for uid, username, full_name, name, voted_at in rows:
        username, full_name = await _ensure_user_info(
            message.bot, uid, username, full_name
        )
        enriched.append((uid, username, full_name, name, voted_at))
        await asyncio.sleep(0.05)  # мягкий rate-limit

    lines = ["🗳 <b>Список голосов</b>\n"]
    for uid, username, full_name, name, voted_at in enriched:
        lines.append(
            f"• {_fmt_user(uid, username, full_name)} → "
            f"<b>{name}</b>  <i>({_fmt_time(voted_at)})</i>"
        )
    lines.append(f"\nВсего: <b>{len(enriched)}</b>")

    text = "\n".join(lines)
    if len(text) > 4000:
        for i in range(0, len(text), 4000):
            await message.answer(text[i:i + 4000])
    else:
        await message.answer(text)


# ------------------ /unvote ------------------

async def cmd_unvote(message: Message, command):
    args = (command.args or "").strip()
    if not args.isdigit():
        return await message.answer(
            "Использование: <code>/unvote 123456789</code>\n"
            "ID можно узнать через @userinfobot или посмотреть в /votes."
        )
    uid = int(args)

    prev_pid = await db.get_user_vote(uid)
    if not prev_pid:
        return await message.answer(
            f"У пользователя <code>{uid}</code> нет голоса."
        )

    p = await db.get_participant(prev_pid)
    pname = p[1] if p else "?"

    await db.delete_user_vote(uid)
    await message.answer(
        f"✅ Голос пользователя <code>{uid}</code> "
        f"(за «{pname}») снят.\n"
        f"Он может голосовать заново через /vote."
    )


# ------------------ /export (CSV) ------------------

async def cmd_export(message: Message):
    rows = await db.get_votes_detailed()
    if not rows:
        return await message.answer("Голосов пока нет — нечего выгружать.")

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        ["user_id", "username", "full_name", "participant", "voted_at"]
    )
    for uid, username, full_name, name, voted_at in rows:
        writer.writerow([
            uid,
            f"@{username}" if username else "",
            full_name or "",
            name,
            _fmt_time(voted_at),
        ])

    # utf-8-sig (BOM) — чтобы Excel корректно открыл кириллицу
    csv_bytes = buf.getvalue().encode("utf-8-sig")
    file = InputFile(io.BytesIO(csv_bytes), filename="votes.csv")

    await message.answer_document(
        file,
        caption=f"📄 Голоса: <b>{len(rows)}</b> шт.\n"
                f"Открывается в Excel / Google Sheets.",
    )


# ------------------ /stats ------------------

async def cmd_stats(message: Message):
    rows = await db.get_votes_detailed()
    if not rows:
        return await message.answer("Голосов пока нет.")

    total = len(rows)
    first_at = rows[0][4]
    last_at = rows[-1][4]

    # Длительность
    try:
        d1 = datetime.strptime(first_at, "%Y-%m-%d %H:%M:%S")
        d2 = datetime.strptime(last_at, "%Y-%m-%d %H:%M:%S")
        sec = int((d2 - d1).total_seconds())
        dur_str = f"{sec // 3600}ч {(sec % 3600) // 60}м {sec % 60}с"
    except Exception:
        dur_str = "?"

    # Активность по часам
    hours = Counter()
    for _, _, _, _, voted_at in rows:
        try:
            dt = datetime.strptime(voted_at, "%Y-%m-%d %H:%M:%S")
            hours[dt.strftime("%Y-%m-%d %H:00")] += 1
        except Exception:
            pass

    # Топ участников
    results = await db.get_results()
    top = results[:5]

    is_open = await db.is_open()
    status = "🟢 открыто" if is_open else "🔴 закрыто"

    lines = [
        "📊 <b>Статистика голосования</b>\n",
        f"Статус: {status}",
        f"Всего голосов: <b>{total}</b>",
        f"Первый: <code>{_fmt_time(first_at)}</code>",
        f"Последний: <code>{_fmt_time(last_at)}</code>",
        f"Длительность: <b>{dur_str}</b>",
        "",
        "📈 <b>Активность по часам:</b>",
    ]

    max_cnt = max(hours.values()) if hours else 1
    for hour, cnt in sorted(hours.items())[-15:]:
        bar_len = max(1, int(cnt * 20 / max_cnt))
        bar = "█" * bar_len
        lines.append(f"<code>{hour}</code> {bar} <b>{cnt}</b>")

    lines.append("")
    lines.append("🏆 <b>Топ-5 участников:</b>")
    medals = ["🥇", "🥈", "🥉"]
    for i, (_, name, cnt) in enumerate(top):
        prefix = medals[i] if i < 3 else f"{i + 1}."
        pct = cnt * 100 // total if total else 0
        lines.append(f"{prefix} {name} — <b>{cnt}</b> ({pct}%)")

    text = "\n".join(lines)
    if len(text) > 4000:
        for i in range(0, len(text), 4000):
            await message.answer(text[i:i + 4000])
    else:
        await message.answer(text)


# ------------------ /broadcast ------------------

async def cmd_broadcast(message: Message, state):
    await Broadcast.message.set()
    await message.answer(
        "📢 <b>Рассылка</b>\n\n"
        "Отправьте сообщение для рассылки (текст, фото, видео — что угодно).\n"
        "Оно уйдёт всем, кто проголосовал.\n\n"
        "Отмена: /cancel"
    )


async def broadcast_message(message: Message, state):
    voter_ids = await db.get_voter_ids()
    if not voter_ids:
        await state.finish()
        return await message.answer(
            "Нет получателей — пока никто не голосовал."
        )

    await state.update_data(
        chat_id=message.chat.id,
        message_id=message.message_id,
    )
    await Broadcast.confirm.set()

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            f"📤 Отправить ({len(voter_ids)})", callback_data="bcast:go"
        ),
        InlineKeyboardButton("❌ Отмена", callback_data="bcast:cancel"),
    ]])
    await message.answer(
        f"Получателей: <b>{len(voter_ids)}</b>\n"
        f"Отправить это сообщение всем?",
        reply_markup=kb,
    )


async def bcast_go(call: CallbackQuery, state):
    data = await state.get_data()
    await state.finish()
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await call.answer("Рассылка запущена")

    voter_ids = await db.get_voter_ids()
    if not voter_ids:
        return await call.message.answer("Нет получателей.")

    status = await call.message.answer(f"📤 Отправка... 0/{len(voter_ids)}")
    sent = failed = 0
    for i, uid in enumerate(voter_ids, 1):
        try:
            await call.bot.copy_message(
                chat_id=uid,
                from_chat_id=data["chat_id"],
                message_id=data["message_id"],
            )
            sent += 1
        except Exception:
            failed += 1
        if i % 10 == 0 or i == len(voter_ids):
            try:
                await status.edit_text(
                    f"📤 Отправка... {i}/{len(voter_ids)}"
                )
            except Exception:
                pass
        await asyncio.sleep(0.05)

    await status.edit_text(
        f"✅ <b>Рассылка завершена</b>\n\n"
        f"Отправлено: <b>{sent}</b>\n"
        f"Ошибок: <b>{failed}</b>"
    )


async def bcast_cancel(call: CallbackQuery, state):
    await state.finish()
    try:
        await call.message.edit_text("❌ Рассылка отменена.")
    except Exception:
        await call.message.answer("❌ Рассылка отменена.")
    await call.answer()


# ------------------ регистрация ------------------

async def cmd_delparticipant(message: Message, command):
    args = (command.args or "").strip()
    if not args.isdigit():
        return await message.answer(
            "Использование: <code>/delparticipant 5</code>\n"
            "ID участника — в /admin → 📋 Управление участниками."
        )
    pid = int(args)
    p = await db.get_participant(pid)
    if not p:
        return await message.answer(f"Участник с id={pid} не найден.")
    name = p[1]
    await db.delete_participant(pid)
    await message.answer(
        f"🗑 Участник «{name}» (id={pid}) удалён.\n"
        f"Голоса за него также очищены."
    )


async def _add_admin_by_id(bot, uid: int, added_by: int):
    """Возвращает (ok: bool, message: str)."""
    if uid in SUPERADMIN_IDS:
        return False, "Этот пользователь — суперадмин, он уже есть."
    if uid in ADMIN_IDS:
        return False, "Этот пользователь уже в ADMIN_IDS (.env)."
    if await db.is_admin(uid):
        return False, "Этот пользователь уже админ."

    uname = fname = None
    try:
        chat = await bot.get_chat(uid)
        uname = chat.username
        fname = chat.full_name
    except Exception:
        pass

    await db.add_admin(uid, uname, fname, added_by=added_by)
    disp = f"@{uname}" if uname else (fname or "")
    suffix = f" ({disp})" if disp else ""
    return True, f"✅ Пользователь <code>{uid}</code>{suffix} теперь админ."


async def cmd_admins(message: Message):
    lines = ["👥 <b>Управление админами</b>\n", "<b>Суперадмины (.env, нельзя удалить):</b>"]
    for uid in (SUPERADMIN_IDS or ADMIN_IDS):
        lines.append(f"• <code>{uid}</code> 🔒")

    rows = await db.list_admins()
    if rows:
        lines.append("\n<b>Админы (добавлены через бота):</b>")
        for uid, uname, fname, _ in rows:
            disp = f"@{uname}" if uname else (fname or "")
            label = f"{disp} (<code>{uid}</code>)" if disp else f"<code>{uid}</code>"
            lines.append(f"• {label}")
    else:
        lines.append("\n<i>Пока нет админов, добавленных через бота.</i>")

    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("➕ Добавить админа", callback_data="adm:adm_add"))
    for uid, uname, fname, _ in rows:
        label = f"🗑 {('@' + uname) if uname else (fname or str(uid))}"
        kb.add(InlineKeyboardButton(label, callback_data=f"adm:adm_del:{uid}"))

    await message.answer("\n".join(lines), reply_markup=kb)


async def adm_admins_menu(call: CallbackQuery):
    await cmd_admins(call.message)
    await call.answer()


async def adm_adm_add_cb(call: CallbackQuery, state):
    await AddAdmin.user_id.set()
    await call.message.answer(
        "Отправьте <b>user_id</b> нового админа (только цифры).\n"
        "Пользователь может узнать свой ID через /myid или @userinfobot.\n\n"
        "Отмена: /cancel"
    )
    await call.answer()


async def add_admin_input(message: Message, state):
    text = (message.text or "").strip()
    if not text.isdigit():
        return await message.answer(
            "Нужно целое число. Попробуйте снова или /cancel."
        )
    uid = int(text)
    await state.finish()
    ok, msg = await _add_admin_by_id(message.bot, uid, message.from_user.id)
    await message.answer(msg)


async def adm_adm_del_cb(call: CallbackQuery):
    try:
        uid = int(call.data.split(":")[2])
    except (IndexError, ValueError):
        return await call.answer()
    if uid in SUPERADMIN_IDS or uid in ADMIN_IDS:
        return await call.answer("Суперадмина удалить нельзя", show_alert=True)
    if uid == call.from_user.id:
        return await call.answer("Нельзя удалить самого себя", show_alert=True)
    if not await db.is_admin(uid):
        return await call.answer("Этот пользователь не админ", show_alert=True)

    await db.delete_admin(uid)
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await call.message.answer(
        f"🗑 Админ <code>{uid}</code> удалён.\n"
        f"Он больше не имеет доступа к /admin."
    )
    await call.answer("Удалён")


async def cmd_addadmin(message: Message, command):
    args = (command.args or "").strip()
    if not args.isdigit():
        return await message.answer(
            "Использование: <code>/addadmin 123456789</code>"
        )
    ok, msg = await _add_admin_by_id(
        message.bot, int(args), message.from_user.id
    )
    await message.answer(msg)


async def cmd_deladmin(message: Message, command):
    args = (command.args or "").strip()
    if not args.isdigit():
        return await message.answer(
            "Использование: <code>/deladmin 123456789</code>"
        )
    uid = int(args)
    if uid in SUPERADMIN_IDS or uid in ADMIN_IDS:
        return await message.answer("Суперадмина удалить нельзя.")
    if uid == message.from_user.id:
        return await message.answer("Нельзя удалить самого себя.")
    if not await db.is_admin(uid):
        return await message.answer(f"Пользователь <code>{uid}</code> не админ.")
    await db.delete_admin(uid)
    await message.answer(f"🗑 Админ <code>{uid}</code> удалён.")


def register_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_cancel, commands=["cancel"], state="*")
    dp.register_message_handler(cmd_admin, IsAdmin(), commands=["admin"], state="*")

    dp.register_callback_query_handler(
        adm_add, IsAdmin(), lambda c: c.data == "adm:add", state="*"
    )
    dp.register_message_handler(
        add_name, IsAdmin(), state=AddParticipant.name, content_types=["text"]
    )
    dp.register_message_handler(
        add_photo, IsAdmin(), state=AddParticipant.photo, content_types=["photo"]
    )
    dp.register_message_handler(
        add_photo_wrong, IsAdmin(), state=AddParticipant.photo
    )

    dp.register_callback_query_handler(
        adm_open, IsAdmin(), lambda c: c.data == "adm:open", state="*"
    )
    dp.register_callback_query_handler(
        adm_close, IsAdmin(), lambda c: c.data == "adm:close", state="*"
    )
    dp.register_callback_query_handler(
        adm_list, IsAdmin(), lambda c: c.data == "adm:list", state="*"
    )
    dp.register_callback_query_handler(
        adm_results, IsAdmin(), lambda c: c.data == "adm:results", state="*"
    )
    dp.register_callback_query_handler(
        adm_reset, IsAdmin(), lambda c: c.data == "adm:reset", state="*"
    )

    dp.register_message_handler(
        cmd_votes, IsAdmin(), commands=["votes"], state="*"
    )
    dp.register_message_handler(
        cmd_unvote, IsAdmin(), commands=["unvote"], state="*"
    )
    dp.register_message_handler(
        cmd_export, IsAdmin(), commands=["export"], state="*"
    )
    dp.register_message_handler(
        cmd_stats, IsAdmin(), commands=["stats"], state="*"
    )
    dp.register_message_handler(
        cmd_broadcast, IsAdmin(), commands=["broadcast"], state="*"
    )
    dp.register_message_handler(
        cmd_delparticipant, IsAdmin(), commands=["delparticipant"], state="*"
    )
    dp.register_callback_query_handler(
        adm_del, IsAdmin(),
        lambda c: c.data and c.data.startswith("adm:del:"), state="*",
    )
    dp.register_callback_query_handler(
        adm_delall, IsAdmin(),
        lambda c: c.data == "adm:delall", state="*",
    )
    dp.register_callback_query_handler(
        adm_delall_yes, IsAdmin(),
        lambda c: c.data == "adm:delall:yes", state="*",
    )
    dp.register_callback_query_handler(
        adm_delall_no, IsAdmin(),
        lambda c: c.data == "adm:delall:no", state="*",
    )

    # --- управление админами (только суперадмин) ---
    dp.register_message_handler(
        cmd_admins, IsSuperAdmin(), commands=["admins"], state="*"
    )
    dp.register_message_handler(
        cmd_addadmin, IsSuperAdmin(), commands=["addadmin"], state="*"
    )
    dp.register_message_handler(
        cmd_deladmin, IsSuperAdmin(), commands=["deladmin"], state="*"
    )
    dp.register_callback_query_handler(
        adm_admins_menu, IsSuperAdmin(),
        lambda c: c.data == "adm:admins", state="*",
    )
    dp.register_callback_query_handler(
        adm_adm_add_cb, IsSuperAdmin(),
        lambda c: c.data == "adm:adm_add", state="*",
    )
    dp.register_callback_query_handler(
        adm_adm_del_cb, IsSuperAdmin(),
        lambda c: c.data and c.data.startswith("adm:adm_del:"), state="*",
    )
    dp.register_message_handler(
        add_admin_input, IsSuperAdmin(),
        state=AddAdmin.user_id, content_types=["text"],
    )

    # FSM рассылки
    dp.register_message_handler(
        broadcast_message, IsAdmin(),
        state=Broadcast.message, content_types=ContentTypes.ANY,
    )
    dp.register_callback_query_handler(
        bcast_go, IsAdmin(),
        lambda c: c.data == "bcast:go", state=Broadcast.confirm,
    )
    dp.register_callback_query_handler(
        bcast_cancel, IsAdmin(),
        lambda c: c.data == "bcast:cancel", state="*",
    )
