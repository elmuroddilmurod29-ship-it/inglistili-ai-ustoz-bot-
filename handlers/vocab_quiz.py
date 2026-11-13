import logging
import random
from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from database import (
    get_random_unlearned_word,
    get_vocab_distractors,
    get_vocab_stats,
    update_vocab_progress,
)

logger = logging.getLogger(__name__)
router = Router()


async def render_quiz_card(user_id: int) -> tuple[str, InlineKeyboardMarkup]:
    """Generates a 4-option flashcard question for an unlearned vocabulary word."""
    word = await get_random_unlearned_word(user_id)
    learned, total = await get_vocab_stats(user_id)

    if not word:
        if total == 0:
            text = (
                "📚 **Lug'atingizda hali so'zlar mavjud emas!**\n\n"
                "Har bir darsni muvaffaqiyatli yakunlaganingizdan so'ng, "
                "darslikdagi yangi so'zlar avtomatik ravishda lug'atingizga qo'shiladi.\n\n"
                "Buning uchun asosiy menyudan **'📖 Darsni boshlash'** tugmasini bosing!"
            )
        else:
            text = (
                "🎉 **Ajoyib natija!**\n\n"
                f"Siz lug'atingizdagi barcha **{total}** ta so'zni to'liq yodlab bo'ldingiz!\n"
                "Yangi so'zlar qo'shilishi uchun keyingi mavzularni o'rganing."
            )
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Qayta tekshirish", callback_data="start_vocab_quiz")]
            ]
        )
        return text, kb

    vocab_id = word["id"]
    word_en = word["word_en"]
    correct_uz = word["word_uz"]
    correct_count = word["correct_count"]

    # Pull 3 distractors
    distractors = await get_vocab_distractors(user_id=user_id, current_uz=correct_uz, count=3)

    # Combine options
    options = [(correct_uz, 1)] + [(d, 0) for d in distractors]
    random.shuffle(options)

    # Build 2x2 or 4x1 keyboard
    kb_rows = []
    for uz_text, is_corr in options:
        cb_data = f"vq_{vocab_id}_{is_corr}"
        kb_rows.append([InlineKeyboardButton(text=uz_text, callback_data=cb_data)])

    keyboard = InlineKeyboardMarkup(inline_keyboard=kb_rows)

    text = (
        f"🔤 **INTERAKTIV SO'Z YODLASH**\n\n"
        f"Inglizcha so'z: 🇬🇧 **{word_en.upper()}**\n\n"
        f"Ushbu so'zning to'g'ri o'zbekcha tarjimasini tanlang:\n"
        f"_(Yodlash darajasi: {correct_count}/4)_\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📊 **Yodlangan so'zlar:** {learned} / {total} ta"
    )
    return text, keyboard


@router.callback_query(F.data == "start_vocab_quiz")
async def start_quiz_callback(callback: CallbackQuery) -> None:
    text, keyboard = await render_quiz_card(callback.from_user.id)
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("vq_"))
async def handle_quiz_answer(callback: CallbackQuery) -> None:
    parts = callback.data.split("_")
    if len(parts) != 3:
        await callback.answer()
        return

    vocab_id = int(parts[1])
    is_correct = bool(int(parts[2]))
    user_id = callback.from_user.id

    new_count, became_learned = await update_vocab_progress(vocab_id, is_correct)
    learned, total = await get_vocab_stats(user_id)

    if is_correct:
        if became_learned:
            status_line = "🎉 **Ajoyib! Bu so'z to'liq yodlandi!** ✅"
        else:
            status_line = f"✅ **To'g'ri javob!** ({new_count}/4 marta to'g'ri topildi)"
    else:
        status_line = "❌ **Afsuski noto'g'ri!** Keyingi safar albatta topasiz."

    next_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➡️ Keyingi so'z", callback_data="start_vocab_quiz")]
        ]
    )

    result_text = (
        f"{status_line}\n\n"
        f"📊 **Yodlangan so'zlar:** {learned} / {total} ta\n\n"
        f"Davom etish uchun pastdagi tugmani bosing:"
    )

    try:
        await callback.message.edit_text(result_text, reply_markup=next_kb, parse_mode="Markdown")
    except Exception:
        await callback.message.answer(result_text, reply_markup=next_kb, parse_mode="Markdown")

    await callback.answer()
