from datetime import datetime, timedelta
import logging
from typing import Optional
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from config import ADMIN_ID
from database import (
    count_syllabus_lessons,
    create_payment_request,
    get_active_homework,
    get_setting,
    get_user,
    get_user_lesson_history,
    mark_homework_completed,
    update_user,
)
from ai_engine import evaluate_homework_submission
from payments.tolov_api import (
    activate_user_paid_tariff,
    cancel_tolov_payment,
    create_tolov_payment,
    get_tolov_status,
    start_payment_monitor_task,
)

logger = logging.getLogger(__name__)
router = Router()


class PaymentStates(StatesGroup):
    waiting_for_receipt = State()


class HomeworkStates(StatesGroup):
    waiting_for_answer = State()


# ==============================================================================
# BUTTON 1: PROFIL VA TARIF
# ==============================================================================

@router.message(F.text == "👤 Profil va Tarif")
async def show_profile(message: Message) -> None:
    user_id = message.from_user.id
    user = await get_user(user_id)
    if not user:
        await message.answer("Iltimos, avval /start buyrug'i orqali ro'yxatdan o'ting.")
        return

    persona_map = {
        "romantic": "❤️ Romantik va Rashkchi",
        "angry": "😡 Asabiy va Qattiqqo'l",
        "funny": "😂 Hazilkash va Prikolchi",
    }
    tariff_map = {
        "free": "🆓 Tekin (10 daqiqa dars)",
        "standard_100k": "💳 Standard (25 daqiqa dars)",
        "pro_200k": "💎 Pro (60 daqiqa dars)",
    }
    gender_map = {
        "male": "👦 O'g'il bola",
        "female": "👧 Qiz bola",
    }
    ai_gender_map = {
        "male": "👨 Ustoz (Erkak)",
        "female": "👩 Ustoz (Ayol)",
    }

    text = (
        "👤 **SIZNING PROFILINGIZ**\n\n"
        f"• **Ism:** {user.get('full_name') or 'Noma`lum'}\n"
        f"• **Telefon:** {user.get('phone') or 'Kiritilmagan'}\n"
        f"• **Jinsingiz:** {gender_map.get(user.get('gender'), 'Belgilanmagan')}\n"
        f"• **Ingliz tili darajangiz:** {user.get('level', 'Beginner')}\n"
        f"• **Ustozingiz:** {ai_gender_map.get(user.get('ai_gender'))} — {persona_map.get(user.get('persona'), user.get('persona'))}\n"
        f"• **Joriy tarif:** {tariff_map.get(user.get('tariff'), 'Tekin')}\n"
        f"• **Tarif amal qilish muddati:** {user.get('tariff_expires_at') or 'Cheksiz'}\n"
        f"• **Emotsional xotira:** _{user.get('emotional_memory') or 'Holat: Oddiy, yangi tanishuv.'}_\n"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Ustoz xarakterini o'zgartirish", callback_data="change_persona")],
            [InlineKeyboardButton(text="💳 Tarifni oshirish", callback_data="open_tariff_menu")],
        ]
    )
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")


@router.callback_query(F.data == "change_persona")
async def change_persona_menu(callback: CallbackQuery) -> None:
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❤️ Romantik", callback_data="set_p_romantic")],
            [InlineKeyboardButton(text="😡 Asabiy", callback_data="set_p_angry")],
            [InlineKeyboardButton(text="😂 Hazilkash", callback_data="set_p_funny")],
        ]
    )
    await callback.message.edit_text(
        "Yangi **Ustoz xarakterini** tanlang:\n\n"
        "• ❤️ Romantik: Rashkchi, nozli, mehrli va sevgilisidek muloqot qiladi.\n"
        "• 😡 Asabiy: Qattiqqo'l, sabrsiz va intizomli.\n"
        "• 😂 Hazilkash: Quvnoq, memchi, lekin hurmatsizlikka arazchi.",
        reply_markup=kb,
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_p_"))
async def save_new_persona(callback: CallbackQuery) -> None:
    new_persona = callback.data.replace("set_p_", "")
    await update_user(callback.from_user.id, persona=new_persona)
    await callback.answer("Ustoz xarakteri yangilandi! ✅", show_alert=True)
    try:
        await callback.message.delete()
    except Exception:
        pass


# ==============================================================================
# BUTTON 2: TARIFNI O'ZGARTIRISH (AUTOMATED TOLOVAPI + MANUAL FALLBACK)
# ==============================================================================

@router.message(F.text == "💳 Tarifni o'zgartirish")
async def show_tariffs(message: Message) -> None:
    text = (
        "💳 **DARSLIK TARIFLARI VA AFZALLIKLARI**\n\n"
        "**1. 🆓 Tekin (Free)**\n"
        "• Dars davomiyligi: 10 daqiqa\n"
        "• O'qitish chuqurligi: Yuzaki, 2-3 misol\n"
        "• Yangi so'zlar: 5 ta\n"
        "• Narxi: 0 so'm\n\n"
        "**2. 💳 Standard — 100 000 so'm / oy**\n"
        "• Dars davomiyligi: 25 daqiqa\n"
        "• O'qitish chuqurligi: 60% qoida va amaliyot\n"
        "• Yangi so'zlar: 12 ta\n"
        "• Uyga vazifalar: 2 ta mashq (AI tekshiruvi bilan)\n\n"
        "**3. 💎 Pro — 200 000 so'm / oy**\n"
        "• Dars davomiyligi: 60 daqiqa (to'liq dars)\n"
        "• O'qitish chuqurligi: 100% professional chuqur tahlil, barcha nozik qoidalar\n"
        "• Yangi so'zlar: 25 ta to'liq lug'at\n"
        "• Uyga vazifalar: 3-4 ta chuqur mashq\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "To'lov qilish uchun kerakli tarifni tanlang:"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Standard (100 000 so'm) sotib olish", callback_data="buy_standard_100k")],
            [InlineKeyboardButton(text="💎 Pro (200 000 so'm) sotib olish", callback_data="buy_pro_200k")],
        ]
    )
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")


@router.callback_query(F.data == "open_tariff_menu")
async def open_tariff_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Standard (100k)", callback_data="buy_standard_100k")],
            [InlineKeyboardButton(text="💎 Pro (200k)", callback_data="buy_pro_200k")],
        ]
    )
    await callback.message.answer("O'zingizga ma'qul tarifni tanlang:", reply_markup=kb)


@router.callback_query(F.data.startswith("buy_"))
async def buy_tariff_handler(callback: CallbackQuery, state: FSMContext) -> None:
    tariff_key = callback.data.replace("buy_", "")
    amount = 100_000 if tariff_key == "standard_100k" else 200_000
    tariff_title = "Standard (100 000 so'm)" if tariff_key == "standard_100k" else "Pro (200 000 so'm)"
    user_id = callback.from_user.id

    order_id = f"ord_{user_id}_{int(datetime.now().timestamp())}"

    # Call TolovAPI to create payment
    pay = await create_tolov_payment(order_id=order_id, amount=amount)

    if pay.get("ok"):
        payment_id = pay["payment_id"]
        pay_amount = pay.get("amount", amount)
        card_number = pay.get("card_number", "5614 6835 1125 2157")
        card_owner = await get_setting("payment_card_owner", "TolovAPI / Admin")

        # Save record in database
        req_db_id = await create_payment_request(
            user_id=user_id,
            tariff_requested=tariff_key,
            amount=pay_amount,
            receipt_file_id=f"tolov_{payment_id}",
        )

        # Launch background auto-monitor task
        start_payment_monitor_task(
            bot=callback.bot,
            payment_id=payment_id,
            user_id=user_id,
            tariff=tariff_key,
            amount=pay_amount,
            req_db_id=req_db_id,
        )

        text = (
            f"💳 **AVTOMATIK KARTA ORQALI TO'LOV**\n\n"
            f"• **Tarif:** {tariff_title}\n"
            f"• **To'lov summasi:** `{pay_amount:,}` so'm\n\n"
            f"Quyidagi kartaga to'lovni o'tkazing:\n"
            f"💳 Karta raqami: `{card_number}`\n"
            f"👤 Egasi: **{card_owner}**\n\n"
            f"⏳ **Amal qilish vaqti:** 5 daqiqa.\n\n"
            f"⚡ _Pul kartaga tushishi bilanoq tizim to'lovingizni **avtomatik aniqlaydi** "
            f"va tarifingizni darhol yoqadi!_"
        )

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔄 To'lovni tekshirish", callback_data=f"chk_pay_{payment_id}_{tariff_key}_{pay_amount}")],
                [InlineKeyboardButton(text="📸 Chek yuborish (qo'lda)", callback_data=f"manual_pay_{tariff_key}_{pay_amount}")],
                [InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"cancel_pay_{payment_id}")],
            ]
        )
        await callback.message.answer(text, reply_markup=kb, parse_mode="Markdown")
        await callback.answer()
        return

    # Fallback to manual card display if TolovAPI is unavailable
    card_number = await get_setting("payment_card_number", "8600 0000 0000 0000")
    card_owner = await get_setting("payment_card_owner", "Admin")

    await state.update_data(tariff_requested=tariff_key, amount=amount, tariff_title=tariff_title)
    await state.set_state(PaymentStates.waiting_for_receipt)

    text = (
        f"💳 **TO'LOV KARTASI MA'LUMOTLARI**\n\n"
        f"• **Tarif:** {tariff_title}\n"
        f"• **Summa:** {amount:,} so'm\n"
        f"• **Karta raqami:** `{card_number}`\n"
        f"• **Karta egasi:** **{card_owner}**\n\n"
        f"To'lovni amalga oshirgach, **to'lov chekining rasmini (skrinshot)** shu yerga yuboring:"
    )
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("chk_pay_"))
async def check_tolov_callback(callback: CallbackQuery) -> None:
    parts = callback.data.split("_")
    # Format: chk_pay_{payment_id}_{tariff_key}_{amount}
    if len(parts) < 5:
        await callback.answer("Noto'g'ri so'rov.", show_alert=True)
        return

    payment_id = parts[2]
    tariff = parts[3]
    amount = int(parts[4])
    user_id = callback.from_user.id

    status_data = await get_tolov_status(payment_id)
    status = status_data.get("status")

    if status == "paid":
        await activate_user_paid_tariff(
            bot=callback.bot,
            user_id=user_id,
            tariff=tariff,
            amount=amount,
            payment_id=payment_id,
        )
        await callback.answer("✅ To'lov tasdiqlandi va tarifingiz yoqildi!", show_alert=True)
        try:
            await callback.message.delete()
        except Exception:
            pass
    elif status == "pending":
        await callback.answer(
            "⏳ To'lov hali qabul qilinmadi.\nIltimos, pulni kartaga o'tkazganingizdan so'ng 10-15 soniya kuting va qayta tekshiring.",
            show_alert=True,
        )
    else:
        await callback.answer(
            f"❌ To'lov holati: {status or 'muddati tugagan'}. Qayta to'lov yaratishingiz mumkin.",
            show_alert=True,
        )


@router.callback_query(F.data.startswith("cancel_pay_"))
async def cancel_tolov_callback(callback: CallbackQuery) -> None:
    payment_id = callback.data.replace("cancel_pay_", "")
    await cancel_tolov_payment(payment_id)
    await callback.answer("To'lov bekor qilindi.", show_alert=True)
    try:
        await callback.message.delete()
    except Exception:
        pass


@router.callback_query(F.data.startswith("manual_pay_"))
async def manual_pay_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split("_")
    tariff_key = parts[2]
    amount = int(parts[3])
    tariff_title = "Standard (100 000 so'm)" if tariff_key == "standard_100k" else "Pro (200 000 so'm)"

    await state.update_data(tariff_requested=tariff_key, amount=amount, tariff_title=tariff_title)
    await state.set_state(PaymentStates.waiting_for_receipt)

    await callback.message.answer(
        "To'lov chekining (skrinshot) rasmini shu yerga yuboring:",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(PaymentStates.waiting_for_receipt, F.photo)
async def process_manual_receipt(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    tariff_requested = data.get("tariff_requested", "standard_100k")
    amount = data.get("amount", 100_000)
    tariff_title = data.get("tariff_title", "Standard")

    photo = message.photo[-1]
    receipt_file_id = photo.file_id
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    username = f"@{message.from_user.username}" if message.from_user.username else "yo'q"

    req_id = await create_payment_request(
        user_id=user_id,
        tariff_requested=tariff_requested,
        amount=amount,
        receipt_file_id=receipt_file_id,
    )

    await state.clear()
    await message.answer(
        "✅ **To'lov chekingiz qabul qilindi!**\n\n"
        "Tez orada ma'muriyat chekni tekshiradi va tarifingiz yoqiladi.",
        parse_mode="Markdown",
    )

    admin_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"adm_pay_ok_{req_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"adm_pay_no_{req_id}"),
            ]
        ]
    )
    caption = (
        f"💳 **YANGI QO'LDA YUBORILGAN CHEK #{req_id}**\n\n"
        f"• **Foydalanuvchi:** {user_name} ({username})\n"
        f"• **ID:** `{user_id}`\n"
        f"• **Tarif:** {tariff_title}\n"
        f"• **Summa:** {amount:,} so'm"
    )
    try:
        await message.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=receipt_file_id,
            caption=caption,
            reply_markup=admin_kb,
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error(f"Failed to forward payment to admin: {e}")


# ==============================================================================
# BUTTON 3: O'ZLASHTIRISH VA DARAJA
# ==============================================================================

@router.message(F.text == "📊 O'zlashtirish va Daraja")
async def show_progress(message: Message) -> None:
    user_id = message.from_user.id
    user = await get_user(user_id)
    if not user:
        await message.answer("Iltimos, avval /start buyrug'i orqali ro'yxatdan o'ting.")
        return

    level = user.get("level", "Beginner")
    current_order = user.get("current_lesson_order", 1)
    total_lessons = await count_syllabus_lessons(level) or 10

    completed_count = min(current_order - 1, total_lessons)
    progress_percent = int((completed_count / total_lessons) * 100)

    filled_blocks = min(10, progress_percent // 10)
    bar = "■" * filled_blocks + "□" * (10 - filled_blocks)

    history = await get_user_lesson_history(user_id, limit=10)
    history_text = ""
    if history:
        for h in history:
            history_text += f"• `{h['completed_at']}` | **{h['topic_title']}** — {h['score_percent']}%\n"
    else:
        history_text = "Hozircha yakunlangan darslar tarixi mavjud emas."

    text = (
        f"📊 **O'ZLASHTIRISH VA DARAJA STATISTIKASI**\n\n"
        f"• **Joriy darajangiz:** {level}\n"
        f"• **Mavzular:** {completed_count}/{total_lessons} tugatildi — **{progress_percent}%**\n"
        f"• **Progress:** `[{bar}]`\n\n"
        f"📚 **Oxirgi darslar va imtihon natijalari:**\n"
        f"{history_text}\n"
        f"Darsni boshlash uchun **'📖 Darsni boshlash'** tugmasini bosing!"
    )
    await message.answer(text, parse_mode="Markdown")


# ==============================================================================
# BUTTON 4: UYGA VAZIFA VA SO'Z YODLASH
# ==============================================================================

@router.message(F.text == "📚 Uyga vazifa va So'z yodlash")
async def show_homework_and_vocab_menu(message: Message) -> None:
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔤 So'z yodlash (Interactive Quiz)", callback_data="start_vocab_quiz")],
            [InlineKeyboardButton(text="📝 Bugungi Uyga vazifa", callback_data="view_homework")],
        ]
    )
    text = (
        "📚 **UYGA VAZIFA VA SO'Z YODLASH BO'LIMI**\n\n"
        "• **🔤 So'z yodlash:** Darslarda o'tilgan yangi so'zlarni 4 ta variantli qiziqarli test orqali mustahkamlang.\n"
        "• **📝 Uyga vazifa:** Bugungi dars bo'yicha berilgan vazifalarni bajaring va ustozingizga tekshirtiring."
    )
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")


@router.callback_query(F.data == "view_homework")
async def view_homework_handler(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = callback.from_user.id
    hw = await get_active_homework(user_id)

    if not hw:
        await callback.message.answer(
            "🎉 **Sizda hozircha faol uyga vazifa yo'q!**\n\n"
            "Darsni yakunlaganingizdan so'ng, yangi mavzuning uyga vazifasi shu yerda paydo bo'ladi."
        )
        await callback.answer()
        return

    await state.update_data(homework_id=hw["id"], tasks_text=hw["tasks_text"])
    await state.set_state(HomeworkStates.waiting_for_answer)

    text = (
        f"📝 **BUGUNGI MAVZU BO'YICHA UYGA VAZIFA:**\n"
        f"Mavzu: **{hw['topic_title']}**\n\n"
        f"{hw['tasks_text']}\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Vazifa javoblarini bitta xabar shaklida yozib yuboring. Ustozingiz tekshirib baholaydi!"
    )
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()


@router.message(HomeworkStates.waiting_for_answer, F.text)
async def process_homework_answer(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    data = await state.get_data()
    hw_id = data.get("homework_id")
    tasks_text = data.get("tasks_text", "")

    user = await get_user(user_id) or {}
    persona = user.get("persona", "romantic")

    user_answer = message.text.strip()
    await message.answer("Ustozingiz javobingizni tekshirmoqda... ⏳")

    if hw_id:
        await mark_homework_completed(hw_id)
    await state.clear()

    evaluation = await evaluate_homework_submission(
        tasks_text=tasks_text,
        user_answer=user_answer,
        persona=persona,
    )
    await message.answer(evaluation)
