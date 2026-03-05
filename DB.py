"""
Модуль для работы с базой данных SQLite (aiosqlite).
Содержит функции для инициализации, получения и обновления состояний пользователей,
а также для сохранения и получения истории диалогов.
Все функции асинхронны и используют параметризованные запросы для защиты от SQL-инъекций.
"""

import aiosqlite
from typing import Optional, List, Dict

# Имя файла базы данных
DB_NAME = "bot.db"


# ---------- Инициализация базы данных ----------
async def init_db() -> None:
    """
    Создаёт необходимые таблицы, если они ещё не существуют.
    Должна вызываться один раз при запуске бота.
    """
    async with aiosqlite.connect(DB_NAME) as db:
        # Таблица состояний пользователя
        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_states (
                user_id INTEGER PRIMARY KEY,
                companion_mode INTEGER DEFAULT 0,
                dictionary_mode INTEGER DEFAULT 0,
                news_mode INTEGER DEFAULT 0,
                dictionary_direction TEXT
            )
        ''')
        # Таблица истории диалога (для собеседника)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # (Опционально) Таблица пользователей для хранения имени и другой информации
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
        await db.commit()


# ---------- Работа с пользователями (опционально) ----------
async def save_user_info(user_id: int, first_name: str = None, last_name: str = None,
                         username: str = None, language_code: str = None) -> None:
    """
    Сохраняет или обновляет информацию о пользователе.
    """
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT OR REPLACE INTO users (user_id, first_name, last_name, username, language_code)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, first_name, last_name, username, language_code))
        await db.commit()


async def get_user_state(user_id: int) -> Dict[str, Optional[int | str]]:
    """
    Возвращает словарь с состояниями режимов пользователя.
    Если записи нет – создаёт её со значениями по умолчанию.
    """
    async with aiosqlite.connect(DB_NAME) as db:
        # Гарантируем, что запись существует (INSERT OR IGNORE не вызовет ошибку)
        await db.execute('''
            INSERT OR IGNORE INTO user_states (user_id, companion_mode, dictionary_mode, news_mode, dictionary_direction)
            VALUES (?, 0, 0, 0, NULL)
        ''', (user_id,))
        await db.commit()

        # Теперь запись точно есть, выбираем её
        async with db.execute('''
            SELECT companion_mode, dictionary_mode, news_mode, dictionary_direction
            FROM user_states WHERE user_id = ?
        ''', (user_id,)) as cursor:
            row = await cursor.fetchone()

        return {
            "companion_mode": row[0],
            "dictionary_mode": row[1],
            "news_mode": row[2],
            "dictionary_direction": row[3]
        }

async def set_user_mode(user_id: int, mode_name: str, value: int) -> None:
    """
    Устанавливает значение конкретного режима (companion_mode, dictionary_mode, news_mode).
    mode_name — имя поля в таблице (строка). value — 0 или 1.
    """
    # Проверяем, что mode_name — допустимое имя поля (защита от инъекций)
    allowed_modes = {"companion_mode", "dictionary_mode", "news_mode"}
    if mode_name not in allowed_modes:
        raise ValueError(f"Недопустимое имя режима: {mode_name}")

    async with aiosqlite.connect(DB_NAME) as db:
        # Убеждаемся, что запись существует
        await get_user_state(user_id)
        # Используем параметризованный запрос, но имя поля нельзя подставить через параметр,
        # поэтому проверяем через allowed_modes
        await db.execute(f'''
            UPDATE user_states SET {mode_name} = ? WHERE user_id = ?
        ''', (value, user_id))
        await db.commit()


async def set_dictionary_direction(user_id: int, direction: Optional[str]) -> None:
    """
    Устанавливает направление перевода для словаря.
    direction может быть, например, 'en_ru', 'ru_en' или None.
    """
    async with aiosqlite.connect(DB_NAME) as db:
        await get_user_state(user_id)
        await db.execute('''
            UPDATE user_states SET dictionary_direction = ? WHERE user_id = ?
        ''', (direction, user_id))
        await db.commit()


async def reset_all_modes(user_id: int) -> None:
    """
    Сбрасывает все режимы и направление словаря для пользователя.
    """
    async with aiosqlite.connect(DB_NAME) as db:
        await get_user_state(user_id)
        await db.execute('''
            UPDATE user_states 
            SET companion_mode = 0, dictionary_mode = 0, news_mode = 0, dictionary_direction = NULL
            WHERE user_id = ?
        ''', (user_id,))
        await db.commit()


# ---------- Работа с историей диалогов ----------
async def save_message(user_id: int, role: str, content: str) -> None:
    """
    Сохраняет сообщение в таблицу conversations.
    role: 'user' или 'assistant'
    """
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT INTO conversations (user_id, role, content)
            VALUES (?, ?, ?)
        ''', (user_id, role, content))
        await db.commit()


async def get_recent_messages(user_id: int, limit: int = 10) -> List[Dict[str, str]]:
    """
    Возвращает последние 'limit' сообщений пользователя (роль + текст)
    в хронологическом порядке (от старых к новым).
    Каждый элемент словаря: {"role": "...", "content": "..."}
    """
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('''
            SELECT role, content FROM conversations
            WHERE user_id = ?
            ORDER BY timestamp ASC
            LIMIT ?
        ''', (user_id, limit)) as cursor:
            rows = await cursor.fetchall()
    return [{"role": row[0], "content": row[1]} for row in rows]


# (Опционально) Функция для очистки истории пользователя
async def clear_user_history(user_id: int) -> None:
    """
    Удаляет все сообщения пользователя из истории.
    """
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('DELETE FROM conversations WHERE user_id = ?', (user_id,))
        await db.commit()