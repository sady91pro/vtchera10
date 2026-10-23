from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery

from bot.Services import db
from bot.Utils.helpers import render_participant, send_results
from bot.config import ADMIN_IDS, SUPERADMIN_IDS


async def cmd_start(message: Message):
    text = (
        "👋 Это бот голосования за лучший костюм.\n\n"
        "• /vote — начать голосование\n"
        "• /results — результаты\n"
        "• /help — все команды\n"
    )
    _is_adm = (
        message.from_user.id in ADMIN_IDS
        or message.from_user.id in SUPERADMIN_IDS
        or await db.is_admin(message.from_user.id)
    )
    if _is_adm:
        text += "\n<b>Админ:</b> /admin — панель управления"
    await message.answer(text)


async def cmd_help(message: Message):
    lines = [
        "<b>📖 Помощь по командам</b>\n",
        "<b>Для всех:</b>",
        "/start — приветствие",
        "/help — эта справка",
        "/vote — голосовать за костюм",
        "/results — текущие результаты",
        "/myid — узнать свой Telegram ID",
        "/cancel — отменить ввод",
    ]
    _is_adm = (
        message.from_user.id in ADMIN_IDS
        or message.from_user.id in SUPERADMIN_IDS
        or await db.is_admin(message.from_user.id)
    )
    _is_super = (
        message.from_user.id in ADMIN_IDS
        or message.from_user.id in SUPERADMIN_IDS
    )
    if _is_adm:
        lines += [
            "",
            "<b>Для админов:</b>",
            "/admin — панель управления",
            "/votes — кто за кого проголосовал",
            "/unvote &lt;id&gt; — снять голос пользователя",
            "/delparticipant &lt;id&gt; — удалить участника",
            "/stats — статистика голосования",
            "/export — выгрузить голоса в CSV",
            "/broadcast — рассылка всем проголосовавшим",
        ]
        if _is_super:
            lines += [
                "",
                "<b>Только суперадмин:</b>",
                "/admins — управление админами",
                "/addadmin &lt;id&gt; — добавить админа",
                "/deladmin &lt;id&gt; — удалить админа",
            ]
    await message.answer("\n".join(lines))


async def cmd_myid(message: Message):
    uid = message.from_user.id
    if uid in SUPERADMIN_IDS or uid in ADMIN_IDS:
        status = "👑 СУПЕРАДМИН"
    elif await db.is_admin(uid):
        status = "✅ АДМИН (через бота)"
    else:
        status = "❌ не админ"
    await message.answer(
        f"<b>Ваш user_id:</b> <code>{uid}</code>\n"
        f"<b>Username:</b> @{message.from_user.username or '—'}\n"
        f"<b>Статус:</b> {status}\n"
        f"<b>Суперадмины:</b> <code>{SUPERADMIN_IDS}</code>"
    )


async def cmd_vote(message: Message):
    if not await db.is_open():
        await message.answer("🔒 Голосование сейчас закрыто.")
        return

    prev_pid = await db.get_user_vote(message.from_user.id)
    if prev_pid:
        p = await db.get_participant(prev_pid)
        name = p[1] if p else "?"
        await message.answer(
            f"Вы уже голосовали за «{name}».\n"
            f"Можно передумать — выберите другого участника ниже. "
            f"Старый голос будет заменён."
        )

    await render_participant(message, 0)


async def cmd_results(message: Message):
    await send_results(message)


async def cb_page(call: CallbackQuery):
    try:
        idx = int(call.data.split(":")[1])
    except (IndexError, ValueError):
        return await call.answer()
    await render_participant(call, idx, edit=True)
    await call.answer()


async def cb_vote(call: CallbackQuery):
    if not await db.is_open():
        return await call.answer("Голосование закрыто", show_alert=True)

    uid = call.from_user.id
    prev_pid = await db.get_user_vote(uid)

    try:
        pid = int(call.data.split(":")[1])
    except (IndexError, ValueError):
        return await call.answer()

    if prev_pid == pid:
        return await call.answer(
            "Вы уже голосуете за этого участника", show_alert=True
        )

    await db.save_vote(
        uid, pid,
        call.from_user.username,
        call.from_user.full_name,
    )
    p = await db.get_participant(pid)
    name = p[1] if p else "?"

    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    if prev_pid:
        await call.message.answer(f"🔁 Голос изменён на «<b>{name}</b>».")
    else:
        await call.message.answer(f"✅ Ваш голос за «<b>{name}</b>» принят!")
    await call.answer("Голос учтён")


def register_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands=["start"])
    dp.register_message_handler(cmd_help, commands=["help"])
    dp.register_message_handler(cmd_myid, commands=["myid"])
    dp.register_message_handler(cmd_vote, commands=["vote"])
    dp.register_message_handler(cmd_results, commands=["results"])
    dp.register_callback_query_handler(
        cb_page, lambda c: c.data and c.data.startswith("pg:"), state="*"
    )
    dp.register_callback_query_handler(
        cb_vote, lambda c: c.data and c.data.startswith("vote:"), state="*"
    )
