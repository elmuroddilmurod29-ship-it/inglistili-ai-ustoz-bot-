import asyncio
import logging
import re
from typing import Dict, Set
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from config import TARIFF_DURATIONS
from database import (
    clear_active_messages,
    get_syllabus_lesson,
    get_user,
    save_active_message,
    update_user,
)
from ai_engine import clear_user_session, init_user_session, run_lesson_turn
from scheduler import cancel_user_lesson_jobs, finalize_lesson_results, schedule_lesson_timers

logger = logging.getLogger(__name__)
router = Router()

# In-memory locks to prevent race conditions and duplicate response spam
USER_LOCKS: Dict[int, asyncio.Lock] = {}

MENU_BUTTON_TEXTS = {
    "📖 Darsni boshlash",
    "👤 Profil va Tarif",
    "💳 Tarifni o'zgartirish",
    "📊 O'zlashtirish va Daraja",
    "📚 Uyga vazifa va So'z yodlash",
    "🛑 Darsni to'xtatish",
}


def get_user_lock(user_id: int) -> asyncio.Lock:
    if user_id not in USER_LOCKS:
        USER_LOCKS[user_id] = asyncio.Lock()
    return USER_LOCKS[user_id]


async def stop_lesson_internal(bot, user_id: int, chat_id: int) -> None:
    """Cancels active lesson timers, clears state, and notifies user."""
    cancel_user_lesson_jobs(user_id)
    clear_user_session(user_id)
    await clear_active_messages(user_id)
    await update_user(user_id, is_in_lesson=0, is_in_exam=0)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📖 Yangi darsni boshlash", callback_data="btn_start_lesson_again")]
        ]
    )
    await bot.send_message(
        chat_id=chat_id,
        text="🛑 **Dars to'xtatildi.**\n\nIstalgan vaqtda darsni qayta boshlashingiz mumkin.",
        reply_markup=kb,
        parse_mode="Markdown",
    )


@router.message(Command("stop_lesson"))
@router.message(F.text == "🛑 Darsni to'xtatish")
async def cmd_stop_lesson(message: Message) -> None:
    user_id = message.from_user.id
    user = await get_user(user_id)
    if not user or (not user.get("is_in_lesson") and not user.get("is_in_exam")):
        await message.answer("Sizda hozir faol dars mavjud emas.")
        return

    await stop_lesson_internal(message.bot, user_id, message.chat.id)


@router.callback_query(F.data == "btn_stop_lesson")
async def callback_stop_lesson(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    await stop_lesson_internal(callback.bot, user_id, callback.message.chat.id)
    await callback.answer()


@router.callback_query(F.data == "btn_start_lesson_again")
async def callback_start_again(callback: CallbackQuery) -> None:
    await callback.answer()
    await start_lesson_logic(callback.bot, callback.from_user.id, callback.message.chat.id)


@router.message(F.text == "📖 Darsni boshlash")
async def start_lesson_handler(message: Message) -> None:
    await start_lesson_logic(message.bot, message.from_user.id, message.chat.id)


async def start_lesson_logic(bot, user_id: int, chat_id: int) -> None:
    lock = get_user_lock(user_id)
    if lock.locked():
        await bot.send_message(chat_id, "Ustozingiz yozmoqda, iltimos bir oz kuting... ⏳")
        return

    async with lock:
        user = await get_user(user_id)
        if not user:
            await bot.send_message(chat_id, "Iltimos, avval /start buyrug'i orqali ro'yxatdan o'ting.")
            return

        # Check if already genuinely in lesson or exam
        if user.get("is_in_lesson") or user.get("is_in_exam"):
            status = "imtihon" if user.get("is_in_exam") else "dars"
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🛑 Darsni to'xtatish", callback_data="btn_stop_lesson")]
                ]
            )
            await bot.send_message(
                chat_id=chat_id,
                text=(
                    f"⚠️ **Sizda allaqachon faol {status} davom etmoqda!**\n\n"
                    "Savollarga javob bering yoki darsni yakunlash uchun to'xtatish tugmasini bosing:"
                ),
                reply_markup=kb,
                parse_mode="Markdown",
            )
            return

        level = user.get("level", "Beginner")
        lesson_order = user.get("current_lesson_order", 1)
        tariff = user.get("tariff", "free")
        duration = TARIFF_DURATIONS.get(tariff, 10)

        syllabus_lesson = await get_syllabus_lesson(level, lesson_order)
        if not syllabus_lesson:
            await bot.send_message(
                chat_id,
                f"🎉 **Tabriklaymiz! Siz {level} darajasidagi barcha 10 ta darsni to'liq tugatdingiz!**\n\n"
                "Keyingi darajaga o'tish uchun profilingizdan darajangizni yangilang.",
                parse_mode="Markdown",
            )
            return

        # Update state in DB
        await update_user(user_id, is_in_lesson=1, is_in_exam=0)
        init_user_session(user_id)

        # Schedule timers
        schedule_lesson_timers(bot=bot, user_id=user_id, tariff=tariff)

        topic_title = syllabus_lesson.get("topic_title", "Ingliz tili darsi")
        start_info = (
            f"📖 **Dars boshlandi!**\n\n"
            f"• **Daraja:** {level} (Mavzu #{lesson_order})\n"
            f"• **Mavzu:** {topic_title}\n"
            f"• **Davomiyligi:** {duration} daqiqa\n\n"
            f"⚠️ _Dars tugashiga 5 daqiqa qolganda yozishmalar o'chiriladi va **IMTIHON** boshlanadi._\n\n"
            f"Ustozingiz yozmoqda... ✍️"
        )
        stop_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🛑 Darsni to'xtatish", callback_data="btn_stop_lesson")]
            ]
        )
        init_msg = await bot.send_message(chat_id=chat_id, text=start_info, reply_markup=stop_kb, parse_mode="Markdown")
        await save_active_message(user_id=user_id, chat_id=chat_id, message_id=init_msg.message_id)

        # Trigger opening greeting from AI
        opening_trigger = "Assalomu alaykum ustoz, bugungi darsimizni boshlaylik!"
        await run_lesson_turn(
            bot=bot,
            chat_id=chat_id,
            user_data=user,
            syllabus_lesson=syllabus_lesson,
            user_message=opening_trigger,
            is_hidden_trigger=False,
        )


@router.message(F.text)
async def lesson_chat_handler(message: Message) -> None:
    user_id = message.from_user.id
    user = await get_user(user_id)

    if not user or (not user.get("is_in_lesson") and not user.get("is_in_exam")):
        return

    # User pressed a main menu button while lesson is active
    if message.text in MENU_BUTTON_TEXTS:
        if message.text == "🛑 Darsni to'xtatish":
            await stop_lesson_internal(message.bot, user_id, message.chat.id)
            return

        status_name = "imtihon" if user.get("is_in_exam") else "dars"
        stop_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🛑 Darsni to'xtatish", callback_data="btn_stop_lesson")]
            ]
        )
        warn_msg = await message.answer(
            f"⚠️ **Hozir {status_name} davom etmoqda!**\n\n"
            "Iltimos, ustozingizning savoliga javob bering yoki to'xtatish tugmasini bosing:",
            reply_markup=stop_kb,
            parse_mode="Markdown",
        )
        if not user.get("is_in_exam"):
            await save_active_message(user_id=user_id, chat_id=message.chat.id, message_id=message.message_id)
            await save_active_message(user_id=user_id, chat_id=message.chat.id, message_id=warn_msg.message_id)
        return

    # Check per-user lock to prevent race conditions and queueing spam
    lock = get_user_lock(user_id)
    if lock.locked():
        await message.answer("Ustozingiz avvalgi gapingizga javob yozmoqda, iltimos kuting... ⏳")
        return

    async with lock:
        # Save user message ID before exam for wiping
        if not user.get("is_in_exam"):
            await save_active_message(user_id=user_id, chat_id=message.chat.id, message_id=message.message_id)

        level = user.get("level", "Beginner")
        lesson_order = user.get("current_lesson_order", 1)
        syllabus_lesson = await get_syllabus_lesson(level, lesson_order) or {}

        raw_reply = await run_lesson_turn(
            bot=message.bot,
            chat_id=message.chat.id,
            user_data=user,
            syllabus_lesson=syllabus_lesson,
            user_message=message.text,
            is_hidden_trigger=False,
        )

        # Check if exam finished with [RESULT: XX]
        if re.search(r"\[RESULT:\s*\d+\]", raw_reply):
            await finalize_lesson_results(
                bot=message.bot,
                user=user,
                syllabus_lesson=syllabus_lesson,
                raw_reply=raw_reply,
            )
