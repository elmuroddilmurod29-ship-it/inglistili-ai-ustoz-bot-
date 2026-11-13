from contextlib import asynccontextmanager
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import aiosqlite
from config import (
    DB_PATH,
    DEFAULT_CARD_NUMBER,
    DEFAULT_CARD_OWNER,
    DEFAULT_PROMO_CODE,
    DEFAULT_TOLOV_SHOP_ID,
    DEFAULT_TOLOV_SHOP_KEY,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def get_db():
    """Async context manager that yields a configured aiosqlite connection."""
    db = await aiosqlite.connect(DB_PATH)
    await db.execute("PRAGMA journal_mode=WAL;")
    await db.execute("PRAGMA busy_timeout=5000;")
    await db.execute("PRAGMA synchronous=NORMAL;")
    await db.execute("PRAGMA foreign_keys=ON;")
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()


async def init_db() -> None:
    """Initializes database tables, indices, and default settings."""
    async with get_db() as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT,
                username TEXT,
                phone TEXT,
                gender TEXT,
                ai_gender TEXT,
                level TEXT,
                persona TEXT,
                tariff TEXT DEFAULT 'free',
                tariff_expires_at TEXT,
                current_lesson_order INTEGER DEFAULT 1,
                emotional_memory TEXT DEFAULT 'Holat: Xursand, yangi tanishuv.',
                is_in_lesson BOOLEAN DEFAULT 0,
                is_in_exam BOOLEAN DEFAULT 0,
                is_blocked BOOLEAN DEFAULT 0,
                joined_at TEXT
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS syllabus (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT,
                lesson_order INTEGER,
                topic_title TEXT,
                grammar_notes TEXT,
                target_words_json TEXT,
                UNIQUE(level, lesson_order)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS active_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                chat_id INTEGER,
                message_id INTEGER
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS lessons_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                level TEXT,
                topic_title TEXT,
                score_percent INTEGER,
                completed_at TEXT
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS vocabulary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                word_en TEXT,
                word_uz TEXT,
                correct_count INTEGER DEFAULT 0,
                is_learned BOOLEAN DEFAULT 0,
                UNIQUE(user_id, word_en)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS homeworks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                topic_title TEXT,
                tasks_text TEXT,
                is_completed BOOLEAN DEFAULT 0
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS mandatory_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT UNIQUE,
                channel_title TEXT,
                invite_link TEXT
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS payment_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                tariff_requested TEXT,
                amount INTEGER,
                receipt_file_id TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS bot_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # Default settings initialization
        defaults = {
            "payment_card_number": DEFAULT_CARD_NUMBER,
            "payment_card_owner": DEFAULT_CARD_OWNER,
            "promo_code": DEFAULT_PROMO_CODE,
            "tolov_shop_id": DEFAULT_TOLOV_SHOP_ID,
            "tolov_shop_key": DEFAULT_TOLOV_SHOP_KEY,
        }
        for k, v in defaults.items():
            await db.execute(
                "INSERT OR IGNORE INTO bot_settings (key, value) VALUES (?, ?)",
                (k, v),
            )

        # Performance indices
        await db.execute("CREATE INDEX IF NOT EXISTS idx_active_messages_user ON active_messages(user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_vocabulary_user ON vocabulary(user_id, is_learned)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_syllabus_lookup ON syllabus(level, lesson_order)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_homeworks_user ON homeworks(user_id, is_completed)")

        await db.commit()
    logger.info("Database initialized successfully.")


# ==============================================================================
# USER OPERATIONS
# ==============================================================================

async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    async with get_db() as db:
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def create_user(
    user_id: int,
    full_name: str,
    username: Optional[str],
    phone: str,
    gender: str,
    ai_gender: str,
    level: str,
    persona: str,
    tariff: str = "free",
    tariff_expires_at: Optional[str] = None,
) -> None:
    now_str = datetime.now().isoformat()
    async with get_db() as db:
        await db.execute(
            """
            INSERT INTO users (
                user_id, full_name, username, phone, gender, ai_gender,
                level, persona, tariff, tariff_expires_at, joined_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                full_name=excluded.full_name,
                username=excluded.username,
                phone=excluded.phone,
                gender=excluded.gender,
                ai_gender=excluded.ai_gender,
                level=excluded.level,
                persona=excluded.persona,
                tariff=excluded.tariff,
                tariff_expires_at=excluded.tariff_expires_at
            """,
            (
                user_id,
                full_name,
                username,
                phone,
                gender,
                ai_gender,
                level,
                persona,
                tariff,
                tariff_expires_at,
                now_str,
            ),
        )
        await db.commit()


async def update_user(user_id: int, **kwargs: Any) -> None:
    if not kwargs:
        return
    set_clauses = [f"{k} = ?" for k in kwargs.keys()]
    values = list(kwargs.values()) + [user_id]
    sql = f"UPDATE users SET {', '.join(set_clauses)} WHERE user_id = ?"
    async with get_db() as db:
        await db.execute(sql, values)
        await db.commit()


async def search_user(query: str) -> Optional[Dict[str, Any]]:
    """Search user by user_id or username (without @)."""
    clean_query = query.strip().lstrip("@")
    async with get_db() as db:
        if clean_query.isdigit():
            async with db.execute("SELECT * FROM users WHERE user_id = ?", (int(clean_query),)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)

        async with db.execute("SELECT * FROM users WHERE LOWER(username) = LOWER(?)", (clean_query,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
    return None


async def get_all_users() -> List[Dict[str, Any]]:
    async with get_db() as db:
        async with db.execute("SELECT * FROM users ORDER BY joined_at DESC") as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_stats() -> Dict[str, Any]:
    """Calculates comprehensive analytics for admin dashboard."""
    async with get_db() as db:
        # Total users
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            total_users = (await cursor.fetchone())[0]

        # Active users (users with lessons completed or registered in last 24h)
        today_date = datetime.now().strftime("%Y-%m-%d")
        async with db.execute("SELECT COUNT(DISTINCT user_id) FROM lessons_history WHERE completed_at LIKE ?", (f"{today_date}%",)) as cursor:
            active_today = (await cursor.fetchone())[0]

        # Tariff breakdown
        async with db.execute("SELECT COUNT(*) FROM users WHERE tariff = 'free'") as cursor:
            free_count = (await cursor.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users WHERE tariff = 'standard_100k'") as cursor:
            standard_count = (await cursor.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users WHERE tariff = 'pro_200k'") as cursor:
            pro_count = (await cursor.fetchone())[0]

        # Total completed lessons
        async with db.execute("SELECT COUNT(*) FROM lessons_history") as cursor:
            total_lessons = (await cursor.fetchone())[0]

        # Pending payments
        async with db.execute("SELECT COUNT(*) FROM payment_requests WHERE status = 'pending'") as cursor:
            pending_payments = (await cursor.fetchone())[0]

        return {
            "total_users": total_users,
            "active_today": active_today,
            "free_count": free_count,
            "standard_count": standard_count,
            "pro_count": pro_count,
            "total_lessons": total_lessons,
            "pending_payments": pending_payments,
        }


# ==============================================================================
# ACTIVE MESSAGES (ANTI-CHEAT AUTO-WIPE)
# ==============================================================================

async def save_active_message(user_id: int, chat_id: int, message_id: int) -> None:
    async with get_db() as db:
        await db.execute(
            "INSERT INTO active_messages (user_id, chat_id, message_id) VALUES (?, ?, ?)",
            (user_id, chat_id, message_id),
        )
        await db.commit()


async def get_active_messages(user_id: int) -> List[Tuple[int, int]]:
    """Returns list of (chat_id, message_id) tuples."""
    async with get_db() as db:
        async with db.execute(
            "SELECT chat_id, message_id FROM active_messages WHERE user_id = ? ORDER BY id ASC",
            (user_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [(r["chat_id"], r["message_id"]) for r in rows]


async def clear_active_messages(user_id: int) -> None:
    async with get_db() as db:
        await db.execute("DELETE FROM active_messages WHERE user_id = ?", (user_id,))
        await db.commit()


# ==============================================================================
# SYLLABUS & LESSON HISTORY
# ==============================================================================

async def get_syllabus_lesson(level: str, lesson_order: int) -> Optional[Dict[str, Any]]:
    async with get_db() as db:
        async with db.execute(
            "SELECT * FROM syllabus WHERE level = ? AND lesson_order = ?",
            (level, lesson_order),
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            res = dict(row)
            try:
                res["target_words"] = json.loads(res["target_words_json"])
            except Exception:
                res["target_words"] = []
            return res


async def count_syllabus_lessons(level: str) -> int:
    async with get_db() as db:
        async with db.execute("SELECT COUNT(*) FROM syllabus WHERE level = ?", (level,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


async def count_all_syllabus_lessons() -> int:
    """Returns total number of lessons across all levels in syllabus table."""
    async with get_db() as db:
        async with db.execute("SELECT COUNT(*) FROM syllabus") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


async def add_syllabus_lesson(
    level: str,
    lesson_order: int,
    topic_title: str,
    grammar_notes: str,
    target_words: List[Dict[str, str]],
) -> None:
    async with get_db() as db:
        await db.execute(
            """
            INSERT INTO syllabus (level, lesson_order, topic_title, grammar_notes, target_words_json)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(level, lesson_order) DO UPDATE SET
                topic_title=excluded.topic_title,
                grammar_notes=excluded.grammar_notes,
                target_words_json=excluded.target_words_json
            """,
            (
                level,
                lesson_order,
                topic_title,
                grammar_notes,
                json.dumps(target_words, ensure_ascii=False),
            ),
        )
        await db.commit()


async def add_lesson_history(user_id: int, level: str, topic_title: str, score_percent: int) -> None:
    now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
    async with get_db() as db:
        await db.execute(
            """
            INSERT INTO lessons_history (user_id, level, topic_title, score_percent, completed_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, level, topic_title, score_percent, now_str),
        )
        await db.commit()


async def get_user_lesson_history(user_id: int, limit: int = 15) -> List[Dict[str, Any]]:
    async with get_db() as db:
        async with db.execute(
            "SELECT * FROM lessons_history WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


# ==============================================================================
# VOCABULARY & QUIZ ENGINE
# ==============================================================================

async def add_vocabulary_words(user_id: int, words: List[Dict[str, str]]) -> None:
    async with get_db() as db:
        for w in words:
            en = w.get("en", "").strip()
            uz = w.get("uz", "").strip()
            if not en or not uz:
                continue
            await db.execute(
                """
                INSERT INTO vocabulary (user_id, word_en, word_uz, correct_count, is_learned)
                VALUES (?, ?, ?, 0, 0)
                ON CONFLICT(user_id, word_en) DO NOTHING
                """,
                (user_id, en, uz),
            )
        await db.commit()


async def get_random_unlearned_word(user_id: int) -> Optional[Dict[str, Any]]:
    async with get_db() as db:
        async with db.execute(
            """
            SELECT * FROM vocabulary
            WHERE user_id = ? AND is_learned = 0
            ORDER BY RANDOM()
            LIMIT 1
            """,
            (user_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_vocab_distractors(user_id: int, current_uz: str, count: int = 3) -> List[str]:
    """Pulls random Uzbek translations from vocabulary or syllabus to serve as distractors."""
    async with get_db() as db:
        # First try from user's vocabulary
        async with db.execute(
            """
            SELECT DISTINCT word_uz FROM vocabulary
            WHERE user_id = ? AND word_uz != ?
            ORDER BY RANDOM()
            LIMIT ?
            """,
            (user_id, current_uz, count),
        ) as cursor:
            rows = await cursor.fetchall()
            distractors = [r["word_uz"] for r in rows]

        # If not enough, draw fallback distractors
        fallback_pool = [
            "kitob", "do'st", "maktab", "quyosh", "tong", "yulduz", "daryo",
            "shahar", "ishonch", "muhabbat", "vaqt", "qalb", "sayohat", "imkoniyat",
            "tajriba", "xavfsizlik", "tabassum", "kelajak", "orzu", "baxt", "mehnat"
        ]
        import random
        random.shuffle(fallback_pool)
        for fb in fallback_pool:
            if len(distractors) >= count:
                break
            if fb != current_uz and fb not in distractors:
                distractors.append(fb)

        return distractors[:count]


async def update_vocab_progress(vocab_id: int, is_correct: bool) -> Tuple[int, bool]:
    """Updates correct_count. If correct_count >= 4, sets is_learned = 1.
    Returns (new_correct_count, became_learned).
    """
    async with get_db() as db:
        async with db.execute("SELECT correct_count, is_learned FROM vocabulary WHERE id = ?", (vocab_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return (0, False)
            current_count = row["correct_count"]
            is_learned = row["is_learned"]

        became_learned = False
        if is_correct:
            new_count = current_count + 1
            if new_count >= 4 and not is_learned:
                is_learned = 1
                became_learned = True
        else:
            new_count = max(0, current_count - 1)

        await db.execute(
            "UPDATE vocabulary SET correct_count = ?, is_learned = ? WHERE id = ?",
            (new_count, is_learned, vocab_id),
        )
        await db.commit()
        return (new_count, became_learned)


async def get_vocab_stats(user_id: int) -> Tuple[int, int]:
    """Returns (learned_count, total_count)."""
    async with get_db() as db:
        async with db.execute("SELECT COUNT(*) FROM vocabulary WHERE user_id = ?", (user_id,)) as cursor:
            total_count = (await cursor.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM vocabulary WHERE user_id = ? AND is_learned = 1", (user_id,)) as cursor:
            learned_count = (await cursor.fetchone())[0]
        return (learned_count, total_count)


# ==============================================================================
# HOMEWORKS
# ==============================================================================

async def add_homework(user_id: int, topic_title: str, tasks_text: str) -> int:
    async with get_db() as db:
        cursor = await db.execute(
            """
            INSERT INTO homeworks (user_id, topic_title, tasks_text, is_completed)
            VALUES (?, ?, ?, 0)
            """,
            (user_id, topic_title, tasks_text),
        )
        await db.commit()
        return cursor.lastrowid or 0


async def get_active_homework(user_id: int) -> Optional[Dict[str, Any]]:
    async with get_db() as db:
        async with db.execute(
            "SELECT * FROM homeworks WHERE user_id = ? AND is_completed = 0 ORDER BY id DESC LIMIT 1",
            (user_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def mark_homework_completed(homework_id: int) -> None:
    async with get_db() as db:
        await db.execute("UPDATE homeworks SET is_completed = 1 WHERE id = ?", (homework_id,))
        await db.commit()


# ==============================================================================
# MANDATORY CHANNELS
# ==============================================================================

async def get_mandatory_channels() -> List[Dict[str, Any]]:
    async with get_db() as db:
        async with db.execute("SELECT * FROM mandatory_channels ORDER BY id ASC") as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def add_mandatory_channel(channel_id: str, channel_title: str, invite_link: str) -> None:
    async with get_db() as db:
        await db.execute(
            """
            INSERT INTO mandatory_channels (channel_id, channel_title, invite_link)
            VALUES (?, ?, ?)
            ON CONFLICT(channel_id) DO UPDATE SET
                channel_title=excluded.channel_title,
                invite_link=excluded.invite_link
            """,
            (channel_id, channel_title, invite_link),
        )
        await db.commit()


async def delete_mandatory_channel(channel_id: str) -> None:
    async with get_db() as db:
        await db.execute("DELETE FROM mandatory_channels WHERE channel_id = ?", (channel_id,))
        await db.commit()


# ==============================================================================
# PAYMENTS & SETTINGS
# ==============================================================================

async def create_payment_request(
    user_id: int, tariff_requested: str, amount: int, receipt_file_id: str
) -> int:
    now_str = datetime.now().isoformat()
    async with get_db() as db:
        cursor = await db.execute(
            """
            INSERT INTO payment_requests (user_id, tariff_requested, amount, receipt_file_id, status, created_at)
            VALUES (?, ?, ?, ?, 'pending', ?)
            """,
            (user_id, tariff_requested, amount, receipt_file_id, now_str),
        )
        await db.commit()
        return cursor.lastrowid or 0


async def get_payment_request(req_id: int) -> Optional[Dict[str, Any]]:
    async with get_db() as db:
        async with db.execute("SELECT * FROM payment_requests WHERE id = ?", (req_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def update_payment_request_status(req_id: int, status: str) -> None:
    async with get_db() as db:
        await db.execute("UPDATE payment_requests SET status = ? WHERE id = ?", (status, req_id))
        await db.commit()


async def get_pending_payment_requests() -> List[Dict[str, Any]]:
    async with get_db() as db:
        async with db.execute("SELECT * FROM payment_requests WHERE status = 'pending' ORDER BY id ASC") as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_setting(key: str, default: str = "") -> str:
    async with get_db() as db:
        async with db.execute("SELECT value FROM bot_settings WHERE key = ?", (key,)) as cursor:
            row = await cursor.fetchone()
            return row["value"] if row else default


async def set_setting(key: str, value: str) -> None:
    async with get_db() as db:
        await db.execute(
            """
            INSERT INTO bot_settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )
        await db.commit()
