import aiosqlite
from typing import Optional, List, Dict
from datetime import datetime, timedelta

DB_NAME = "*.db"

# ==================== ИНИЦИАЛИЗАЦИЯ ====================
async def init_db() -> None:
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_states (
                user_id INTEGER PRIMARY KEY,
                companion_mode INTEGER DEFAULT 0,
                dictionary_mode INTEGER DEFAULT 0,
                news_mode INTEGER DEFAULT 0,
                dictionary_direction TEXT,
                role TEXT DEFAULT "teammate"
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                username TEXT,
                language_code TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS moderation (
                user_id INTEGER PRIMARY KEY,
                warnings INTEGER DEFAULT 0,
                banned_until DATETIME
            )
        ''')
        await db.commit()

# ==================== ПОЛЬЗОВАТЕЛИ ====================
async def save_user_info(user_id: int, first_name: str = None, last_name: str = None,
                         username: str = None, language_code: str = None) -> None:
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT OR REPLACE INTO users 
            (user_id, first_name, last_name, username, language_code)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, first_name, last_name, username, language_code))
        await db.commit()

async def get_user_state(user_id: int) -> Dict[str, Optional[int | str]]:
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT OR IGNORE INTO user_states 
            (user_id, companion_mode, dictionary_mode, news_mode, dictionary_direction, role)
            VALUES (?, 0, 0, 0, NULL, "teammate")
        ''', (user_id,))
        await db.commit()

        async with db.execute('''
            SELECT companion_mode, dictionary_mode, news_mode, dictionary_direction, role
            FROM user_states WHERE user_id = ?
        ''', (user_id,)) as cursor:
            row = await cursor.fetchone()

        return {
            "companion_mode": row[0],
            "dictionary_mode": row[1],
            "news_mode": row[2],
            "dictionary_direction": row[3],
            "role": row[4]
        }

async def set_user_mode(user_id: int, mode_name: str, value: int) -> None:
    allowed_modes = {"companion_mode", "dictionary_mode", "news_mode"}
    if mode_name not in allowed_modes:
        raise ValueError(f"Недопустимое имя режима: {mode_name}")

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(f'UPDATE user_states SET {mode_name} = ? WHERE user_id = ?', (value, user_id))
        await db.commit()

async def set_user_role(user_id: int, role: str) -> None:
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('UPDATE user_states SET role = ? WHERE user_id = ?', (role, user_id))
        await db.commit()

async def reset_all_modes(user_id: int) -> None:
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            UPDATE user_states
            SET companion_mode = 0, dictionary_mode = 0, news_mode = 0, dictionary_direction = NULL
            WHERE user_id = ?
        ''', (user_id,))
        await db.commit()
# ==================== ИСТОРИЯ ДИАЛОГОВ ====================
async def save_message(user_id: int, role: str, content: str) -> None:
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('INSERT INTO conversations (user_id, role, content) VALUES (?, ?, ?)',
                         (user_id, role, content))
        await db.commit()

async def get_recent_messages(user_id: int, limit: int = 10) -> List[Dict[str, str]]:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('''
            SELECT role, content FROM conversations
            WHERE user_id = ? ORDER BY timestamp ASC LIMIT ?
        ''', (user_id, limit)) as cursor:
            rows = await cursor.fetchall()
    return [{"role": row[0], "content": row[1]} for row in rows]

async def clear_user_history(user_id: int) -> None:
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('DELETE FROM conversations WHERE user_id = ?', (user_id,))
        await db.commit()

# ==================== МОДЕРАЦИЯ ====================
async def get_moderation(user_id: int) -> Dict:
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('INSERT OR IGNORE INTO moderation (user_id) VALUES (?)', (user_id,))
        await db.commit()
        async with db.execute('SELECT warnings, banned_until FROM moderation WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return {"warnings": row[0], "banned_until": row[1]}

async def add_warning(user_id: int) -> int:
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('UPDATE moderation SET warnings = warnings + 1 WHERE user_id = ?', (user_id,))
        await db.commit()
        async with db.execute('SELECT warnings FROM moderation WHERE user_id = ?', (user_id,)) as cursor:
            return (await cursor.fetchone())[0]

async def ban_user(user_id: int, level: int):
    durations = [5, 30, 60, 1440, None]  # минуты
    until = None if level == 5 else (datetime.now() + timedelta(minutes=durations[level-1]))
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('UPDATE moderation SET banned_until = ? WHERE user_id = ?', (until, user_id))
        await db.commit()

async def get_ban_message(user_id: int) -> str | None:
    data = await get_moderation(user_id)
    if not data["banned_until"]:
        return None
    try:
        ban_time = datetime.fromisoformat(str(data["banned_until"]).replace("Z", "+00:00"))
    except:
        return None
    if ban_time <= datetime.now():
        await reset_warnings(user_id)
        return "✅ Бан снят!\n\nДобро пожаловать обратно, mate!"
    delta = ban_time - datetime.now()
    minutes_left = int(delta.total_seconds() // 60)
    hours = minutes_left // 60
    mins = minutes_left % 60
    time_str = f"{hours} ч {mins} мин" if hours else f"{mins} минут"
    end_time = ban_time.strftime("%H:%M")
    return f"""🚫 Ты в бане
Осталось: {time_str}
Разбан в {end_time}
Если хочешь обжаловать — пиши @*"""

async def reset_warnings(user_id: int) -> None:
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('UPDATE moderation SET warnings = 0, banned_until = NULL WHERE user_id = ?', (user_id,))
        await db.commit()
