import json
import aiosqlite
from bot.config import DB_PATH


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "CREATE TABLE IF NOT EXISTS participants("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "name TEXT NOT NULL,"
            "photo_id TEXT NOT NULL,"
            "photo_ids TEXT)"
        )
        await db.execute(
            "CREATE TABLE IF NOT EXISTS votes("
            "user_id INTEGER PRIMARY KEY,"
            "participant_id INTEGER NOT NULL,"
            "voted_at TEXT DEFAULT CURRENT_TIMESTAMP,"
            "username TEXT,"
            "full_name TEXT)"
        )
        await db.execute(
            "CREATE TABLE IF NOT EXISTS settings("
            "key TEXT PRIMARY KEY, value TEXT)"
        )
        await db.execute(
            "INSERT OR IGNORE INTO settings(key,value) VALUES('voting_open','0')"
        )
        await db.execute(
            "CREATE TABLE IF NOT EXISTS admins("
            "user_id INTEGER PRIMARY KEY,"
            "username TEXT,"
            "full_name TEXT,"
            "added_by INTEGER,"
            "added_at TEXT DEFAULT CURRENT_TIMESTAMP)"
        )
        # Миграция для старых БД
        async with db.execute("PRAGMA table_info(votes)") as cur:
            cols = [r[1] for r in await cur.fetchall()]
        if "username" not in cols:
            await db.execute("ALTER TABLE votes ADD COLUMN username TEXT")
        if "full_name" not in cols:
            await db.execute("ALTER TABLE votes ADD COLUMN full_name TEXT")
        # Миграция participants.photo_ids
        async with db.execute("PRAGMA table_info(participants)") as cur:
            pcols = [r[1] for r in await cur.fetchall()]
        if "photo_ids" not in pcols:
            await db.execute("ALTER TABLE participants ADD COLUMN photo_ids TEXT")
        # Заполнить photo_ids для старых записей
        async with db.execute(
            "SELECT id, photo_id FROM participants WHERE photo_ids IS NULL"
        ) as cur:
            olds = await cur.fetchall()
        for pid, photo in olds:
            await db.execute(
                "UPDATE participants SET photo_ids=? WHERE id=?",
                (json.dumps([photo]), pid),
            )
        await db.commit()


async def get_participants():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id, name, photo_id, photo_ids "
            "FROM participants ORDER BY id"
        ) as cur:
            return await cur.fetchall()


async def get_participant(pid: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id, name, photo_id, photo_ids "
            "FROM participants WHERE id=?", (pid,)
        ) as cur:
            return await cur.fetchone()


async def add_participant(name: str, photos) -> int:
    """photos — file_id (str) или список file_id."""
    if isinstance(photos, str):
        photos = [photos]
    if not photos:
        raise ValueError("Нужно хотя бы одно фото")
    primary = photos[0]
    photo_ids_json = json.dumps(photos)
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO participants(name, photo_id, photo_ids) VALUES(?, ?, ?)",
            (name, primary, photo_ids_json),
        )
        await db.commit()
        return cur.lastrowid


async def is_open() -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT value FROM settings WHERE key='voting_open'"
        ) as cur:
            row = await cur.fetchone()
            return bool(row and row[0] == "1")


async def set_open(value: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO settings(key,value) VALUES('voting_open',?)",
            ("1" if value else "0",),
        )
        await db.commit()


async def get_user_vote(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT participant_id FROM votes WHERE user_id=?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else None


async def save_vote(user_id, participant_id, username=None, full_name=None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO votes"
            "(user_id, participant_id, username, full_name) "
            "VALUES(?, ?, ?, ?)",
            (user_id, participant_id, username, full_name),
        )
        await db.commit()


async def delete_user_vote(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM votes WHERE user_id=?", (user_id,))
        await db.commit()


async def get_results():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT p.id, p.name, COUNT(v.user_id) AS cnt "
            "FROM participants p "
            "LEFT JOIN votes v ON p.id = v.participant_id "
            "GROUP BY p.id "
            "ORDER BY cnt DESC, p.id"
        ) as cur:
            return await cur.fetchall()


async def reset_votes():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM votes")
        await db.commit()


async def get_votes_detailed():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT v.user_id, v.username, v.full_name, p.name, v.voted_at "
            "FROM votes v "
            "JOIN participants p ON p.id = v.participant_id "
            "ORDER BY v.voted_at"
        ) as cur:
            return await cur.fetchall()


async def get_voter_ids():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM votes") as cur:
            return [r[0] for r in await cur.fetchall()]


async def update_vote_user_info(user_id, username, full_name):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE votes SET username=?, full_name=? "
            "WHERE user_id=? AND (username IS NULL OR full_name IS NULL)",
            (username, full_name, user_id),
        )
        await db.commit()


async def delete_participant(pid: int) -> bool:
    """Удаляет участника и все голоса за него. Возвращает True, если был."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id FROM participants WHERE id=?", (pid,)
        ) as cur:
            if not await cur.fetchone():
                return False
        await db.execute("DELETE FROM votes WHERE participant_id=?", (pid,))
        await db.execute("DELETE FROM participants WHERE id=?", (pid,))
        await db.commit()
        return True


async def delete_all_participants() -> int:
    """Удаляет ВСЕХ участников и все голоса. Возвращает count удалённых."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM participants") as cur:
            cnt = (await cur.fetchone())[0]
        await db.execute("DELETE FROM votes")
        await db.execute("DELETE FROM participants")
        await db.commit()
        return cnt


# ---------- admins ----------

async def add_admin(user_id, username=None, full_name=None, added_by=None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO admins"
            "(user_id, username, full_name, added_by) VALUES(?, ?, ?, ?)",
            (user_id, username, full_name, added_by),
        )
        await db.commit()


async def delete_admin(user_id) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "DELETE FROM admins WHERE user_id=?", (user_id,)
        )
        await db.commit()
        return cur.rowcount > 0


async def list_admins():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT user_id, username, full_name, added_at "
            "FROM admins ORDER BY added_at"
        ) as cur:
            return await cur.fetchall()


async def is_admin(user_id) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM admins WHERE user_id=?", (user_id,)
        ) as cur:
            return bool(await cur.fetchone())
