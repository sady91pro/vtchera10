from aiogram.dispatcher.filters import BoundFilter
from aiogram.dispatcher.middlewares import BaseMiddleware

from bot.config import ADMIN_IDS, SUPERADMIN_IDS
from bot.Services import db


class IsAdmin(BoundFilter):
    async def check(self, obj) -> bool:
        user = getattr(obj, "from_user", None)
        if not user:
            return False
        if user.id in SUPERADMIN_IDS or user.id in ADMIN_IDS:
            return True
        return await db.is_admin(user.id)


class IsSuperAdmin(BoundFilter):
    """ТОЛЬКО SUPERADMIN_IDS из .env или is_super=1 в БД."""

    async def check(self, obj) -> bool:
        user = getattr(obj, "from_user", None)
        if not user:
            return False
        if user.id in SUPERADMIN_IDS:
            return True
        return await db.is_superadmin(user.id)


class UserTracker(BaseMiddleware):
    async def on_pre_process_message(self, message, data):
        u = getattr(message, "from_user", None)
        if u and not u.is_bot:
            try:
                await db.upsert_known_user(u.id, u.username, u.full_name)
            except Exception:
                pass

    async def on_pre_process_callback_query(self, cq, data):
        u = getattr(cq, "from_user", None)
        if u and not u.is_bot:
            try:
                await db.upsert_known_user(u.id, u.username, u.full_name)
            except Exception:
                pass
