import logging
from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from bot.config import BOT_TOKEN
from bot.Services import db
from bot.Handlers import user, admin


def create_dispatcher() -> Dispatcher:
    bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
    dp = Dispatcher(bot, storage=MemoryStorage())
    user.register_handlers(dp)
    admin.register_handlers(dp)
    return dp


async def on_startup(dp: Dispatcher):
    await db.init_db()
    logging.info("Bot started")


def run():
    logging.basicConfig(level=logging.INFO)
    dp = create_dispatcher()
    executor.start_polling(
        dp,
        skip_updates=True,
        on_startup=on_startup,
    )
