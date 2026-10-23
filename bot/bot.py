import asyncio
import logging
from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from bot.config import BOT_TOKEN, DB_PATH
from bot.Services import db
from bot.Handlers import user, admin
from bot.Middleware.admin_filter import UserTracker


async def _schedule_loop(dp: Dispatcher):
    from datetime import datetime
    while True:
        try:
            now = datetime.now()

            open_at = await db.get_setting("schedule_open_at", "")
            if open_at:
                try:
                    dt = datetime.fromisoformat(open_at)
                    if now >= dt:
                        # Очищаем ВСЕГДА, даже если голосование уже открыто
                        await db.set_setting("schedule_open_at", "")
                        if not await db.is_open():
                            await db.set_open(True)
                            logging.info("[schedule] голосование открыто")
                except Exception as e:
                    logging.warning(f"schedule open parse: {e}")
                    await db.set_setting("schedule_open_at", "")

            close_at = await db.get_setting("schedule_close_at", "")
            if close_at:
                try:
                    dt = datetime.fromisoformat(close_at)
                    if now >= dt:
                        await db.set_setting("schedule_close_at", "")
                        was_open = await db.is_open()
                        if was_open:
                            await db.set_open(False)
                            logging.info("[schedule] голосование закрыто")
                            if await db.get_setting("announce_on_close") == "1":
                                try:
                                    from bot.Handlers.admin import _do_announce
                                    await _do_announce(dp.bot, actor=None)
                                except Exception as e:
                                    logging.error(f"schedule announce failed: {e}")
                except Exception as e:
                    logging.warning(f"schedule close parse: {e}")
                    await db.set_setting("schedule_close_at", "")
        except Exception as e:
            logging.error(f"schedule_loop: {e}")
        await asyncio.sleep(30)


async def on_startup(dp: Dispatcher):
    await db.init_db()

    try:
        broken = await db.check_db_integrity()
        if broken > 0:
            logging.warning(
                f"[integrity] Удалено {broken} голосов за удалённых участников"
            )
    except Exception as e:
        logging.error(f"integrity check failed: {e}")

    try:
        rows = await db.list_admins()
        for uid, uname, fname, _, _ in rows:
            if uid and (uname or fname):
                await db.upsert_known_user(uid, uname, fname)
    except Exception as e:
        logging.warning(f"known_users backfill (admins): {e}")

    try:
        import aiosqlite
        async with aiosqlite.connect(DB_PATH) as _db:
            async with _db.execute(
                "SELECT user_id, username, full_name FROM votes"
            ) as cur:
                for uid, uname, fname in await cur.fetchall():
                    if uid and (uname or fname):
                        await db.upsert_known_user(uid, uname, fname)
    except Exception as e:
        logging.warning(f"known_users backfill (votes): {e}")

    asyncio.ensure_future(_schedule_loop(dp))
    logging.info("Bot started, schedule loop running")


def create_dispatcher() -> Dispatcher:
    bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
    dp = Dispatcher(bot, storage=MemoryStorage())
    dp.middleware.setup(UserTracker())
    user.register_handlers(dp)
    admin.register_handlers(dp)
    return dp


def run():
    logging.basicConfig(level=logging.INFO)
    dp = create_dispatcher()
    executor.start_polling(
        dp,
        skip_updates=True,
        on_startup=on_startup,
    )
