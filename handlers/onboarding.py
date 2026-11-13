import logging
from typing import Optional
from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from database import create_user, get_user

logger = logging.getLogger(__name__)
router = Router()


class OnboardingStates(StatesGroup):
    waiting_for_phone = State()
    waiting_for_level = State()
    waiting_for_persona = State()
    waiting_for_gender = State()
    waiting_for_tariff = State()


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Returns the persistent 2x2 + wide top button Main Menu."""
    kb = [
        [KeyboardButton(text="📖 Darsni boshlash")],
        [
            KeyboardButton(text="👤 Profil va Tarif"),
            KeyboardButton(text="💳 Tarifni o'zgartirish"),
        ],
        [
            KeyboardButton(text="📊 O'zlashtirish va Daraja"),
            KeyboardButton(text="📚 Uyga vazifa va So'z yodlash"),
        ],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, is_persistent=True)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    user = await get_user(user_id)

    if user:
        await state.clear()
        full_name = user.get("full_name") or message.from_user.full_name
        text = (
            f"Assalomu alaykum, **{full_name}**! 👋\n\n"
            f"Xush kelibsiz! Darsni boshlash uchun quyidagi **'📖 Darsni boshlash'** tugmasini bosing."
        )
        await message.answer(text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")
        return

    # Start onboarding flow
    await state.clear()
    await state.set_state(OnboardingStates.waiting_for_phone)

    phone_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    welcome_text = (
        "🇺🇿 **Assalomu alaykum! AI Ingliz tili repetitoringizga xush kelibsiz!**\n\n"
        "Bu yerda siz o'zingiz tanlagan sun'iy intellekt ustozingiz bilan jonli muloqot qilib, "
        "ingliz tilini noldan IELTS darajasigacha chuqur va interaktiv o'rganasiz.\n\n"
        "Ro'yxatdan o'tish uchun telefon raqamingizni yuboring:"
    )
    await message.answer(welcome_text, reply_markup=phone_kb, parse_mode="Markdown")


# Phone handler (Contact or Text)
@router.message(OnboardingStates.waiting_for_phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext) -> None:
    phone = message.contact.phone_number
    await state.update_data(phone=phone)
    await ask_level(message, state)


@router.message(OnboardingStates.waiting_for_phone, F.text)
async def process_phone_text(message: Message, state: FSMContext) -> None:
    phone = message.text.strip()
    await state.update_data(phone=phone)
    await ask_level(message, state)


async def ask_level(message: Message, state: FSMContext) -> None:
    await state.set_state(OnboardingStates.waiting_for_level)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🟢 Beginner (A1)", callback_data="lvl_Beginner")],
            [InlineKeyboardButton(text="🟡 Elementary (A2)", callback_data="lvl_Elementary")],
            [InlineKeyboardButton(text="🟠 Pre-Intermediate (B1)", callback_data="lvl_Pre-Intermediate")],
            [InlineKeyboardButton(text="🔵 Intermediate (B2)", callback_data="lvl_Intermediate")],
            [InlineKeyboardButton(text="🟣 Upper-Intermediate (B2+)", callback_data="lvl_Upper-Intermediate")],
            [InlineKeyboardButton(text="🎯 IELTS (C1)", callback_data="lvl_IELTS")],
        ]
    )
    # Remove reply keyboard temporarily
    temp_msg = await message.answer(
        "Qabul qilindi! Endi o'zingizning hozirgi **Ingliz tili darajangizni** tanlang:",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


@router.callback_query(OnboardingStates.waiting_for_level, F.data.startswith("lvl_"))
async def process_level(callback: CallbackQuery, state: FSMContext) -> None:
    level = callback.data.replace("lvl_", "")
    await state.update_data(level=level)
    await state.set_state(OnboardingStates.waiting_for_persona)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❤️ Romantik va Mehribon", callback_data="prs_romantic")],
            [InlineKeyboardButton(text="😡 Asabiy va Qattiqqo'l", callback_data="prs_angry")],
            [InlineKeyboardButton(text="😂 Hazilkash va Prikolchi", callback_data="prs_funny")],
        ]
    )
    await callback.message.edit_text(
        f"Tanlangan daraja: **{level}**\n\n"
        "Endi sizga dars beradigan **Ustoz xarakterini (psixologiyasini)** tanlang:\n\n"
        "• **❤️ Romantik:** Sizni sevib qoladi, rashk qiladi, erkalaydi.\n"
        "• **😡 Asabiy:** Qattiqqo'l, xatolarga chidamaydi, po'stagini qoqadi.\n"
        "• **😂 Hazilkash:** Memlar, hazillar bilan dars o'tadi, lekin mensimasangiz qattiq arazlaydi.",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(OnboardingStates.waiting_for_persona, F.data.startswith("prs_"))
async def process_persona(callback: CallbackQuery, state: FSMContext) -> None:
    persona = callback.data.replace("prs_", "")
    await state.update_data(persona=persona)
    await state.set_state(OnboardingStates.waiting_for_gender)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👦 O'g'il bola", callback_data="gnd_male"),
                InlineKeyboardButton(text="👧 Qiz bola", callback_data="gnd_female"),
            ]
        ]
    )
    await callback.message.edit_text(
        "Jinsingizni tanlang (Ustozingiz sizga **qarama-qarshi jinsda** bo'ladi):",
        reply_markup=keyboard,
    )
    await callback.answer()


@router.callback_query(OnboardingStates.waiting_for_gender, F.data.startswith("gnd_"))
async def process_gender(callback: CallbackQuery, state: FSMContext) -> None:
    gender = callback.data.replace("gnd_", "")
    ai_gender = "female" if gender == "male" else "male"
    await state.update_data(gender=gender, ai_gender=ai_gender)
    await state.set_state(OnboardingStates.waiting_for_tariff)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🆓 Tekin (10 daqiqa dars)", callback_data="trf_free")],
            [InlineKeyboardButton(text="💳 Standard — 100 000 so'm/oy (25 daqiqa)", callback_data="trf_standard_100k")],
            [InlineKeyboardButton(text="💎 Pro — 200 000 so'm/oy (60 daqiqa)", callback_data="trf_pro_200k")],
        ]
    )
    await callback.message.edit_text(
        "O'zingizga ma'qul **Dars tarifini** tanlang:\n\n"
        "• **🆓 Tekin:** 10 daqiqalik qisqa dars, 5 ta yangi so'z.\n"
        "• **💳 Standard (100k so'm):** 25 daqiqa dars, 12 ta so'z, 2 ta uyga vazifa.\n"
        "• **💎 Pro (200k so'm):** 60 daqiqalik professional to'liq dars, 25 ta so'z, chuqur tahlil va uy ishlari.",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(OnboardingStates.waiting_for_tariff, F.data.startswith("trf_"))
async def process_tariff(callback: CallbackQuery, state: FSMContext) -> None:
    tariff = callback.data.replace("trf_", "")
    data = await state.get_data()

    user_id = callback.from_user.id
    full_name = callback.from_user.full_name
    username = callback.from_user.username
    phone = data.get("phone", "+998900000000")
    level = data.get("level", "Beginner")
    persona = data.get("persona", "romantic")
    gender = data.get("gender", "male")
    ai_gender = data.get("ai_gender", "female")

    from datetime import datetime, timedelta
    expires_at = (datetime.now() + timedelta(days=30)).strftime("%d.%m.%Y")

    await create_user(
        user_id=user_id,
        full_name=full_name,
        username=username,
        phone=phone,
        gender=gender,
        ai_gender=ai_gender,
        level=level,
        persona=persona,
        tariff=tariff,
        tariff_expires_at=expires_at,
    )

    await state.clear()
    await callback.answer("Tabriklaymiz! Ro'yxatdan o'tish muvaffaqiyatli yakunlandi.", show_alert=True)

    try:
        await callback.message.delete()
    except Exception:
        pass

    persona_names = {
        "romantic": "❤️ Romantik va rashkchi sevgilingiz",
        "angry": "😡 Qattiqqo'l va asabiy ustoz",
        "funny": "😂 Hazilkash va arazchi do'stingiz",
    }
    tariff_names = {
        "free": "🆓 Tekin (10 daqiqa)",
        "standard_100k": "💳 Standard (25 daqiqa)",
        "pro_200k": "💎 Pro (60 daqiqa)",
    }

    congrats_text = (
        f"🎉 **Tabriklaymiz, {full_name}!** Siz muvaffaqiyatli ro'yxatdan o'tdingiz.\n\n"
        f"• **Darajangiz:** {level}\n"
        f"• **Ustozingiz:** {persona_names.get(persona, persona)}\n"
        f"• **Tarifingiz:** {tariff_names.get(tariff, tariff)}\n\n"
        f"Darsni boshlash uchun quyidagi **'📖 Darsni boshlash'** tugmasini bosing!"
    )
    await callback.message.answer(
        congrats_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown",
    )
