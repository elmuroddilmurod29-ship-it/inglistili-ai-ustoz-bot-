import asyncio
from datetime import datetime, timedelta
import logging
import re
from typing import Dict, List, Optional
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import TARIFF_DURATIONS, TARIFF_WORDS_COUNT
from database import (
    add_homework,
    add_lesson_history,
    add_vocabulary_words,
    clear_active_messages,
    get_active_messages,
    get_syllabus_lesson,
    get_user,
    update_user,
)

logger = logging.getLogger(__name__)

# Single instance of AsyncIOScheduler
scheduler = AsyncIOScheduler()

# Store active job IDs per user: {user_id: [job_id1, job_id2]}
USER_SCHEDULED_JOBS: Dict[int, List[str]] = {}


def start_scheduler() -> None:
    if not scheduler.running:
        scheduler.start()
        logger.info("APScheduler started successfully.")


def shutdown_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped.")


def cancel_user_lesson_jobs(user_id: int) -> None:
    """Cancels any pending scheduler jobs for this user."""
    job_ids = USER_SCHEDULED_JOBS.pop(user_id, [])
    for jid in job_ids:
        try:
            scheduler.remove_job(jid)
        except Exception:
            pass


async def wipe_active_messages_for_user(bot: Bot, user_id: int) -> None:
    """Deletes all active messages from the chat in batches of up to 100."""
    try:
        active_msgs = await get_active_messages(user_id)
        if not active_msgs:
            return

        chat_id = active_msgs[0][0]
        all_ids = [m[1] for m in active_msgs]

        # Batch delete in chunks of 100
        chunk_size = 100
        for i in range(0, len(all_ids), chunk_size):
            chunk = all_ids[i:i + chunk_size]
            try:
                await bot.delete_messages(chat_id=chat_id, message_ids=chunk)
            except TelegramAPIError as api_err:
                logger.warning(f"Batch delete failed for user {user_id}, falling back to single deletes: {api_err}")
                for msg_id in chunk:
                    try:
                        await bot.delete_message(chat_id=chat_id, message_id=msg_id)
                    except Exception:
                        pass
            except Exception as e:
                logger.warning(f"Unexpected error deleting messages: {e}")

        await clear_active_messages(user_id)
        logger.info(f"Auto-wiped {len(all_ids)} messages for user {user_id} before exam.")
    except Exception as e:
        logger.error(f"Error in wipe_active_messages_for_user: {e}")


async def trigger_wipe_and_start_exam(bot: Bot, user_id: int) -> None:
    """Triggered at (duration - 5 minutes). Wipes chat messages and starts exam."""
    try:
        user = await get_user(user_id)
        if not user or not user.get("is_in_lesson") or user.get("is_in_exam"):
            return

        chat_id = user_id

        # 1. Wipe chat messages
        await wipe_active_messages_for_user(bot, user_id)

        # 2. Update status to in exam
        await update_user(user_id, is_in_exam=1)

        # 3. Send warning announcement
        await bot.send_message(
            chat_id=chat_id,
            text=(
                "⚠️ **DIQQAT: DARSLIK TUGADI!**\n\n"
                "Shpargalkalar va darsdagi barcha xabarlar o'chirildi.\n"
                "Endi **IMTIHON** boshlanadi! Savollarga birma-bir javob bering."
            ),
            parse_mode="Markdown",
        )

        # 4. Trigger Gemini with [START_EXAM]
        from ai_engine import run_lesson_turn
        lesson_order = user.get("current_lesson_order", 1)
        syllabus_lesson = await get_syllabus_lesson(user.get("level", "Beginner"), lesson_order) or {}

        await run_lesson_turn(
            bot=bot,
            chat_id=chat_id,
            user_data=user,
            syllabus_lesson=syllabus_lesson,
            user_message="[START_EXAM]",
            is_hidden_trigger=True,
        )

    except Exception as e:
        logger.error(f"Error triggering wipe and exam for user {user_id}: {e}")


async def trigger_finish_lesson_time_up(bot: Bot, user_id: int) -> None:
    """Triggered when lesson timer reaches 100% duration."""
    try:
        user = await get_user(user_id)
        if not user or (not user.get("is_in_lesson") and not user.get("is_in_exam")):
            return

        chat_id = user_id
        from ai_engine import clear_user_session, run_lesson_turn

        lesson_order = user.get("current_lesson_order", 1)
        syllabus_lesson = await get_syllabus_lesson(user.get("level", "Beginner"), lesson_order) or {}

        # Send [TIME_UP] to Gemini
        reply = await run_lesson_turn(
            bot=bot,
            chat_id=chat_id,
            user_data=user,
            syllabus_lesson=syllabus_lesson,
            user_message="[TIME_UP]",
            is_hidden_trigger=True,
        )

        # Finalize lesson
        await finalize_lesson_results(
            bot=bot,
            user=user,
            syllabus_lesson=syllabus_lesson,
            raw_reply=reply,
        )

    except Exception as e:
        logger.error(f"Error in trigger_finish_lesson_time_up for user {user_id}: {e}")


async def finalize_lesson_results(
    bot: Bot,
    user: Dict,
    syllabus_lesson: Dict,
    raw_reply: str,
) -> None:
    """Extracts score from [RESULT: XX], records history, adds vocabulary, creates homework."""
    user_id = user["user_id"]
    from ai_engine import clear_user_session
    cancel_user_lesson_jobs(user_id)
    clear_user_session(user_id)
    await clear_active_messages(user_id)

    # Parse [RESULT: XX]
    score = 75
    match = re.search(r"\[RESULT:\s*(\d+)\]", raw_reply)
    if match:
        try:
            score = int(match.group(1))
        except ValueError:
            score = 75

    level = user.get("level", "Beginner")
    topic_title = syllabus_lesson.get("topic_title", "General English")

    # Record history
    await add_lesson_history(
        user_id=user_id,
        level=level,
        topic_title=topic_title,
        score_percent=score,
    )

    # Slice vocabulary according to tariff
    tariff = user.get("tariff", "free")
    word_count = TARIFF_WORDS_COUNT.get(tariff, 5)
    all_words = syllabus_lesson.get("target_words", [])
    target_slice = all_words[:word_count]
    if target_slice:
        await add_vocabulary_words(user_id=user_id, words=target_slice)

    # Save homework tasks
    homework_tasks = (
        f"1. Bugungi o'tilgan '{topic_title}' mavzusi bo'yicha 3 ta inglizcha gap tuzing.\n"
        f"2. Bugungi yangi so'zlardan 3 tasini ishlatib dialog yozing.\n"
        f"3. Mavzu qoidasini o'z so'zlaringiz bilan qisqacha tushuntiring."
    )
    await add_homework(user_id=user_id, topic_title=topic_title, tasks_text=homework_tasks)

    # Increment lesson order if passed (>= 70%)
    current_order = user.get("current_lesson_order", 1)
    new_order = current_order
    if score >= 70:
        new_order = current_order + 1

    await update_user(
        user_id,
        is_in_lesson=0,
        is_in_exam=0,
        current_lesson_order=new_order,
    )

    # Inform user of completion and stats
    status_emoji = "🎉" if score >= 70 else "⚠️"
    msg_text = (
        f"{status_emoji} **Bugungi dars muvaffaqiyatli yakunlandi!**\n\n"
        f"📊 **Imtihon natijangiz:** {score}%\n"
        f"📚 **Lug'atga qo'shilgan yangi so'zlar:** {len(target_slice)} ta\n"
        f"📝 **Uyga vazifangiz:** '📚 Uyga vazifa va So'z yodlash' bo'limida tayyor.\n\n"
    )
    if score >= 70:
        msg_text += f"🚀 Tabriklaymiz! Keyingi mavzuga o'tdingiz (Mavzu #{new_order})."
    else:
        msg_text += "Qayta takrorlash tavsiya etiladi. Keyingi darsda ushbu mavzuni yanada mustahkamlaymiz!"

    try:
        await bot.send_message(chat_id=user_id, text=msg_text, parse_mode="Markdown")
    except Exception as e:
        logger.warning(f"Could not send completion message: {e}")


def schedule_lesson_timers(bot: Bot, user_id: int, tariff: str) -> None:
    """Schedules the 2 timer events:
    1. Exam & auto-wipe at (duration - 5) minutes
    2. Lesson finish at (duration) minutes
    """
    cancel_user_lesson_jobs(user_id)

    duration_minutes = TARIFF_DURATIONS.get(tariff, 10)
    exam_time_minutes = max(1, duration_minutes - 5)

    now = datetime.now()
    exam_date = now + timedelta(minutes=exam_time_minutes)
    finish_date = now + timedelta(minutes=duration_minutes)

    job_exam_id = f"exam_{user_id}_{int(now.timestamp())}"
    job_finish_id = f"finish_{user_id}_{int(now.timestamp())}"

    # Schedule exam trigger
    scheduler.add_job(
        trigger_wipe_and_start_exam,
        "date",
        run_date=exam_date,
        args=[bot, user_id],
        id=job_exam_id,
    )

    # Schedule time up trigger
    scheduler.add_job(
        trigger_finish_lesson_time_up,
        "date",
        run_date=finish_date,
        args=[bot, user_id],
        id=job_finish_id,
    )

    USER_SCHEDULED_JOBS[user_id] = [job_exam_id, job_finish_id]
    logger.info(
        f"Scheduled lesson for user {user_id} (tariff: {tariff}): "
        f"Exam at {exam_date.strftime('%H:%M:%S')}, Finish at {finish_date.strftime('%H:%M:%S')}."
    )
