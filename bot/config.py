import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан в .env")

ADMIN_IDS = [
    int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
]

_sa = os.getenv("SUPERADMIN_IDS", "").strip()
SUPERADMIN_IDS = (
    [int(x.strip()) for x in _sa.split(",") if x.strip()]
    if _sa else list(ADMIN_IDS)
)

DB_PATH = os.getenv("DB_PATH", "votes.db")
