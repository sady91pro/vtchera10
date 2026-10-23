from aiogram.dispatcher.filters import BoundFilter

from bot.config import ADMIN_IDS, SUPERADMIN_IDS
from bot.Services import db


class IsAdmin(BoundFilter):
    """Суперадмин ИЛИ env-админ ИЛИ админ, добавленный через бота."""

    async def check(self, obj) -> bool:
        user = getattr(obj, "from_user", None)
        if not user:
            return False
        if user.id in SUPERADMIN_IDS or user.id in ADMIN_IDS:
            return True
        return await db.is_admin(user.id)


class IsSuperAdmin(BoundFilter):
    """Только суперадмин (из .env). Может управлять другими админами."""

    async def check(self, obj) -> bool:
        user = getattr(obj, "from_user", None)
        return bool(
            user and (user.id in SUPERADMIN_IDS or user.id in ADMIN_IDS)
        )
