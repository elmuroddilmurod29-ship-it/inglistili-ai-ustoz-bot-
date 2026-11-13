import asyncio
from datetime import datetime, timedelta
import logging
from typing import Any, Dict, List, Optional
from aiogram import F, Router
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram.filters import Command
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
    add_mandatory_channel,
    add_syllabus_lesson,
    count_syllabus_lessons,
    delete_mandatory_channel,
    get_all_users,
    get_mandatory_channels,
    get_payment_request,
    get_pending_payment_requests,
    get_setting,
    get_stats,
    get_user,
    search_user,
    set_setting,
    update_payment_request_status,
    update_user,
)

logger = logging.getLogger(__name__)
router = Router()

# Security filter: Only ADMIN_ID can trigger handlers in this router
router.message.filter(F.from_user.id == ADMIN_ID)
router.callback_query.filter(F.from_user.id == ADMIN_ID)


class AdminStates(StatesGroup):
    waiting_for_broadcast = State()
    waiting_for_add_channel = State()
    waiting_for_user_search = State()
    waiting_for_new_card = State()
    waiting_for_new_card_owner = State()
    waiting_for_new_shop_id = State()
    waiting_for_new_shop_key = State()
    # Syllabus addition states
    syllabus_level = State()
    syllabus_order = State()
    syllabus_title = State()
    syllabus_grammar = State()
    syllabus_words = State()


def get_admin_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Statistika", callback_data="adm_stats"),
                InlineKeyboardButton(text="📢 Xabar yuborish", callback_data="adm_broadcast"),
            ],
            [
                InlineKeyboardButton(text="📢 Majburiy kanallar", callback_data="adm_channels"),
                InlineKeyboardButton(text="💳 To'lovlar (Cheklar)", callback_data="adm_payments"),
            ],
            [
                InlineKeyboardButton(text="🔍 Foydalanuvchini boshqarish", callback_data="adm_user_mgmt"),
                InlineKeyboardButton(text="💳 Kartani o'zgartirish", callback_data="adm_card_settings"),
            ],
            [
                InlineKeyboardButton(text="📚 Darslik qo'shish", callback_data="adm_add_syllabus"),
            ],
        ]
    )


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "🛠 **BOSH ADMIN BOSHQARUV PANELI**\n\nKerakli bo'limni tanlang:",
        reply_markup=get_admin_main_keyboard(),
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "adm_back_main")
async def callback_back_main(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        "🛠 **BOSH ADMIN BOSHQARUV PANELI**\n\nKerakli bo'limni tanlang:",
        reply_markup=get_admin_main_keyboard(),
        parse_mode="Markdown",
    )
    await callback.answer()


# ==============================================================================
# 1. STATISTIKA
# ==============================================================================

@router.callback_query(F.data == "adm_stats")
async def show_admin_stats(callback: CallbackQuery) -> None:
    stats = await get_stats()
    text = (
        "📊 **BOT STATISTIKASI VA ANALITIKASI**\n\n"
        f"• **Jami foydalanuvchilar:** {stats['total_users']:,} nafar\n"
        f"• **Bugun faol foydalanuvchilar:** {stats['active_today']:,} nafar\n"
        f"• **Tugatilgan umumiy darslar:** {stats['total_lessons']:,} ta\n"
        f"• **Kutilayotgan to'lov cheklari:** {stats['pending_payments']} ta\n\n"
        "💳 **Tariflar bo'yicha taqsimot:**\n"
        f"• 🆓 Tekin (Free): {stats['free_count']} nafar\n"
        f"• 💳 Standard (100k): {stats['standard_count']} nafar\n"
        f"• 💎 Pro (200k): {stats['pro_count']} nafar\n"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Orqaga", callback_data="adm_back_main")]]
    )
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


# ==============================================================================
# 2. HAMMAGA XABAR YUBORISH (BROADCAST)
# ==============================================================================

@router.callback_query(F.data == "adm_broadcast")
async def start_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminStates.waiting_for_broadcast)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor qilish", callback_data="adm_back_main")]]
    )
    await callback.message.edit_text(
        "📢 **HAMMAGA XABAR YUBORISH**\n\n"
        "Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yuboring.\n"
        "Matn, rasm, video, ovozli xabar yoki forward qilingan post bo'lishi mumkin:",
        reply_markup=kb,
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(AdminStates.waiting_for_broadcast)
async def process_broadcast(message: Message, state: FSMContext) -> None:
    await state.clear()
    status_msg = await message.answer("⏳ Xabar tarqatilmoqda, iltimos kuting...")

    users = await get_all_users()
    delivered = 0
    blocked = 0

    for user in users:
        u_id = user["user_id"]
        try:
            await message.copy_to(chat_id=u_id)
            delivered += 1
            await asyncio.sleep(0.05)  # safe rate limit
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            try:
                await message.copy_to(chat_id=u_id)
                delivered += 1
            except Exception:
                blocked += 1
        except TelegramForbiddenError:
            blocked += 1
        except Exception:
            blocked += 1

    report = (
        "📢 **XABAR TARQATISH YAKUNLANDI!**\n\n"
        f"• **Yetkazildi:** {delivered:,} nafar\n"
        f"• **Yetib bormadi (bloklagan):** {blocked:,} nafar\n"
        f"• **Jami urinish:** {len(users):,} ta"
    )
    await status_msg.edit_text(report, parse_mode="Markdown")


# ==============================================================================
# 3. MAJBURIY KANALLAR (FORCE-SUB)
# ==============================================================================

@router.callback_query(F.data == "adm_channels")
async def list_mandatory_channels(callback: CallbackQuery) -> None:
    channels = await get_mandatory_channels()
    buttons = []

    text = "📢 **MAJBURIY HOMIY KANALLAR**\n\n"
    if channels:
        for idx, ch in enumerate(channels, 1):
            text += f"{idx}. **{ch['channel_title']}** (`{ch['channel_id']}`)\nLink: {ch['invite_link']}\n\n"
            buttons.append([
                InlineKeyboardButton(
                    text=f"🗑 O'chirish: {ch['channel_title']}",
                    callback_data=f"adm_del_ch_{ch['channel_id']}",
                )
            ])
    else:
        text += "Hozircha majburiy kanallar qo'shilmagan.\n\n"

    buttons.append([InlineKeyboardButton(text="➕ Yangi kanal qo'shish", callback_data="adm_add_channel")])
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="adm_back_main")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "adm_add_channel")
async def ask_channel_info(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminStates.waiting_for_add_channel)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor qilish", callback_data="adm_channels")]]
    )
    await callback.message.edit_text(
        "➕ **YANGI KANAL QO'SHISH**\n\n"
        "Kanal ma'lumotlarini quyidagi formatda yuboring:\n"
        "`@kanal_username | Kanal Nomi | https://t.me/kanal_link`\n\n"
        "⚠️ **Muhim:** Botni o'sha kanalda ADMIN qilib qo'yganingizga ishonch hosil qiling!",
        reply_markup=kb,
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(AdminStates.waiting_for_add_channel)
async def process_add_channel(message: Message, state: FSMContext) -> None:
    parts = message.text.split("|")
    if len(parts) < 3:
        await message.answer(
            "Xatolik! Format: `@kanal_username | Kanal Nomi | https://t.me/kanal_link`\nQayta urinib ko'ring:"
        )
        return

    channel_id = parts[0].strip()
    title = parts[1].strip()
    invite_link = parts[2].strip()

    # Verify bot has admin rights
    try:
        member = await message.bot.get_chat_member(chat_id=channel_id, user_id=message.bot.id)
        if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
            await message.answer(f"❌ Xatolik: Bot `{channel_id}` kanalida ADMIN emas! Avval botga adminlik bering.")
            return
    except Exception as e:
        await message.answer(f"❌ Kanalni tekshirib bo'lmadi: {e}\nUsername yoki ID to'g'riligini tekshiring.")
        return

    await add_mandatory_channel(channel_id, title, invite_link)
    await state.clear()
    await message.answer(
        f"✅ **{title}** kanali majburiy a'zolik ro'yxatiga muvaffaqiyatli qo'shildi!",
        parse_mode="Markdown",
    )


@router.callback_query(F.data.startswith("adm_del_ch_"))
async def process_delete_channel(callback: CallbackQuery) -> None:
    ch_id = callback.data.replace("adm_del_ch_", "")
    await delete_mandatory_channel(ch_id)
    await callback.answer("Kanal o'chirildi! ✅", show_alert=True)
    await list_mandatory_channels(callback)


# ==============================================================================
# 4. TO'LOVLAR VA CHEKLAR BOSHQARUVI
# ==============================================================================

@router.callback_query(F.data == "adm_payments")
async def list_pending_payments(callback: CallbackQuery) -> None:
    reqs = await get_pending_payment_requests()
    if not reqs:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="⬅️ Orqaga", callback_data="adm_back_main")]]
        )
        await callback.message.edit_text(
            "💳 **KUTILAYOTGAN TO'LOV CHEKLARI YO'Q.**\n\nBarcha to'lovlar ko'rib chiqilgan.",
            reply_markup=kb,
            parse_mode="Markdown",
        )
        await callback.answer()
        return

    # Render first pending request
    req = reqs[0]
    user = await get_user(req["user_id"]) or {}
    user_name = user.get("full_name") or f"ID: {req['user_id']}"

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"adm_pay_ok_{req['id']}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"adm_pay_no_{req['id']}"),
            ],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="adm_back_main")],
        ]
    )

    caption = (
        f"💳 **TO'LOV CHEKI #{req['id']}**\n\n"
        f"• **Foydalanuvchi:** {user_name} (`{req['user_id']}`)\n"
        f"• **So'ralgan tarif:** {req['tariff_requested']}\n"
        f"• **Summa:** {req['amount']:,} so'm\n"
        f"• **Sana:** {req['created_at']}\n\n"
        f"Navbatda yana {len(reqs) - 1} ta chek bor."
    )

    try:
        await callback.message.delete()
        await callback.message.bot.send_photo(
            chat_id=callback.from_user.id,
            photo=req["receipt_file_id"],
            caption=caption,
            reply_markup=kb,
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error(f"Error displaying payment request: {e}")
    await callback.answer()


@router.callback_query(F.data.startswith("adm_pay_ok_"))
async def approve_payment(callback: CallbackQuery) -> None:
    req_id = int(callback.data.replace("adm_pay_ok_", ""))
    req = await get_payment_request(req_id)
    if not req or req["status"] != "pending":
        await callback.answer("Ushbu so'rov allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    user_id = req["user_id"]
    tariff = req["tariff_requested"]
    expires_at = (datetime.now() + timedelta(days=30)).strftime("%d.%m.%Y")

    await update_payment_request_status(req_id, "approved")
    await update_user(user_id, tariff=tariff, tariff_expires_at=expires_at)

    tariff_titles = {
        "standard_100k": "Standard (25 daqiqa dars)",
        "pro_200k": "Pro (60 daqiqa dars)",
    }
    # Notify user
    try:
        await callback.bot.send_message(
            chat_id=user_id,
            text=(
                f"🎉 **To'lovingiz muvaffaqiyatli tasdiqlandi!**\n\n"
                f"Sizga **{tariff_titles.get(tariff, tariff)}** tarifi 30 kunga faollashtirildi.\n"
                f"Muddati: {expires_at} gacha.\n\n"
                "Endi darsni boshlashingiz mumkin: **'📖 Darsni boshlash'** tugmasini bosing!"
            ),
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.warning(f"Could not notify user {user_id}: {e}")

    await callback.answer("To'lov tasdiqlandi va foydalanuvchiga xabar berildi! ✅", show_alert=True)
    try:
        await callback.message.edit_caption(
            caption=f"✅ To'lov #{req_id} muvaffaqiyatli TASDIQLANDI.\nTarif: {tariff}",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="⬅️ Bosh menyuga", callback_data="adm_back_main")]]
            ),
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("adm_pay_no_"))
async def reject_payment(callback: CallbackQuery) -> None:
    req_id = int(callback.data.replace("adm_pay_no_", ""))
    req = await get_payment_request(req_id)
    if not req or req["status"] != "pending":
        await callback.answer("Ushbu so'rov allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    await update_payment_request_status(req_id, "rejected")

    # Notify user
    try:
        await callback.bot.send_message(
            chat_id=req["user_id"],
            text=(
                "❌ **Afsuski, to'lov chekingiz tasdiqlanmadi.**\n\n"
                "Iltimos, haqiqiy to'lov skrinshotini yuborganingizga ishonch hosil qiling "
                "yoki ma'muriyat bilan bog'laning."
            ),
            parse_mode="Markdown",
        )
    except Exception:
        pass

    await callback.answer("To'lov rad etildi! ❌", show_alert=True)
    try:
        await callback.message.edit_caption(
            caption=f"❌ To'lov #{req_id} RAD ETILDI.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="⬅️ Bosh menyuga", callback_data="adm_back_main")]]
            ),
        )
    except Exception:
        pass


# ==============================================================================
# 5. FOYDALANUVCHINI BOSHQARISH (USER MANAGEMENT)
# ==============================================================================

@router.callback_query(F.data == "adm_user_mgmt")
async def start_user_mgmt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminStates.waiting_for_user_search)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor qilish", callback_data="adm_back_main")]]
    )
    await callback.message.edit_text(
        "🔍 **FOYDALANUVCHINI QIDIRISH**\n\n"
        "Foydalanuvchining **Telegram ID** raqamini yoki **@username**ini yuboring:",
        reply_markup=kb,
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(AdminStates.waiting_for_user_search)
async def process_user_search(message: Message, state: FSMContext) -> None:
    query = message.text.strip()
    user = await search_user(query)

    if not user:
        await message.answer(f"❌ `{query}` bo'yicha foydalanuvchi topilmadi. Qayta urinib ko'ring:")
        return

    await state.clear()
    u_id = user["user_id"]
    blocked_status = "⛔ Bloklangan" if user.get("is_blocked") else "✅ Faol"

    text = (
        f"👤 **FOYDALANUVCHI PROFILI:**\n\n"
        f"• **Ism:** {user.get('full_name')}\n"
        f"• **Username:** @{user.get('username') or 'yoq'}\n"
        f"• **ID:** `{u_id}`\n"
        f"• **Telefon:** {user.get('phone')}\n"
        f"• **Darajasi:** {user.get('level')} (Mavzu #{user.get('current_lesson_order')})\n"
        f"• **Tarifi:** {user.get('tariff')} ({user.get('tariff_expires_at') or 'muddatsiz'})\n"
        f"• **Xarakteri:** {user.get('persona')}\n"
        f"• **Holat:** {blocked_status}\n"
        f"• **Emotsional xotira:** _{user.get('emotional_memory')}_\n"
    )

    block_btn_text = "🟢 Blokdan chiqarish" if user.get("is_blocked") else "⛔ Bloklash"
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎁 Standard berish", callback_data=f"adm_give_std_{u_id}"),
                InlineKeyboardButton(text="💎 Pro berish", callback_data=f"adm_give_pro_{u_id}"),
            ],
            [
                InlineKeyboardButton(text="🔄 1-mavzuga qaytarish", callback_data=f"adm_reset_order_{u_id}"),
                InlineKeyboardButton(text=block_btn_text, callback_data=f"adm_toggle_block_{u_id}"),
            ],
            [InlineKeyboardButton(text="⬅️ Bosh menyuga", callback_data="adm_back_main")],
        ]
    )
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")


@router.callback_query(F.data.startswith("adm_give_std_"))
async def admin_give_standard(callback: CallbackQuery) -> None:
    u_id = int(callback.data.replace("adm_give_std_", ""))
    exp = (datetime.now() + timedelta(days=30)).strftime("%d.%m.%Y")
    await update_user(u_id, tariff="standard_100k", tariff_expires_at=exp)
    await callback.answer(f"Foydalanuvchi {u_id} ga Standard tarifi berildi! ✅", show_alert=True)


@router.callback_query(F.data.startswith("adm_give_pro_"))
async def admin_give_pro(callback: CallbackQuery) -> None:
    u_id = int(callback.data.replace("adm_give_pro_", ""))
    exp = (datetime.now() + timedelta(days=30)).strftime("%d.%m.%Y")
    await update_user(u_id, tariff="pro_200k", tariff_expires_at=exp)
    await callback.answer(f"Foydalanuvchi {u_id} ga Pro tarifi berildi! 💎", show_alert=True)


@router.callback_query(F.data.startswith("adm_reset_order_"))
async def admin_reset_order(callback: CallbackQuery) -> None:
    u_id = int(callback.data.replace("adm_reset_order_", ""))
    await update_user(u_id, current_lesson_order=1)
    await callback.answer(f"Foydalanuvchi {u_id} ning mavzusi 1-darsga qaytarildi! 🔄", show_alert=True)


@router.callback_query(F.data.startswith("adm_toggle_block_"))
async def admin_toggle_block(callback: CallbackQuery) -> None:
    u_id = int(callback.data.replace("adm_toggle_block_", ""))
    user = await get_user(u_id)
    if not user:
        return
    new_blocked = 0 if user.get("is_blocked") else 1
    await update_user(u_id, is_blocked=new_blocked)
    status_str = "bloklandi" if new_blocked else "blokdan chiqarildi"
    await callback.answer(f"Foydalanuvchi {status_str}! ✅", show_alert=True)


# ==============================================================================
# 6. KARTANI O'ZGARTIRISH VA TO'LOV TIZIMI SOZLAMALARI
# ==============================================================================

@router.callback_query(F.data == "adm_card_settings")
async def show_card_settings(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    card_number = await get_setting("payment_card_number", "5614 6835 1125 2157")
    card_owner = await get_setting("payment_card_owner", "TolovAPI / Admin")
    shop_id = await get_setting("tolov_shop_id", "339")
    shop_key = await get_setting("tolov_shop_key", "cFpP7PdwqrDsVAdX")

    text = (
        "💳 **TO'LOV KARTASI VA TOLOVAPI SOZLAMALARI**\n\n"
        f"• **Karta raqami:** `{card_number}`\n"
        f"• **Karta egasi:** **{card_owner}**\n"
        f"• **TolovAPI Shop ID:** `{shop_id}`\n"
        f"• **TolovAPI Shop Key:** `{shop_key[:4]}...{shop_key[-4:]}`\n\n"
        "O'zgartirmoqchi bo'lgan ma'lumotingizni tanlang:"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Karta raqamini o'zgartirish", callback_data="adm_edit_card")],
            [InlineKeyboardButton(text="🔑 Shop ID ni o'zgartirish", callback_data="adm_edit_shop_id")],
            [InlineKeyboardButton(text="🔐 Shop Key ni o'zgartirish", callback_data="adm_edit_shop_key")],
            [InlineKeyboardButton(text="⬅️ Bosh menyuga", callback_data="adm_back_main")],
        ]
    )
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "adm_edit_card")
async def edit_card_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminStates.waiting_for_new_card)
    await callback.message.edit_text(
        "Yangi karta raqamini kiriting (masalan: `8600 1234 5678 9000`):",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(AdminStates.waiting_for_new_card)
async def process_new_card(message: Message, state: FSMContext) -> None:
    card_number = message.text.strip()
    await set_setting("payment_card_number", card_number)
    await state.set_state(AdminStates.waiting_for_new_card_owner)
    await message.answer(
        f"Karta raqami `{card_number}` saqlandi.\nEndi karta egasining ism-familiyasini kiriting:",
        parse_mode="Markdown",
    )


@router.message(AdminStates.waiting_for_new_card_owner)
async def process_new_card_owner(message: Message, state: FSMContext) -> None:
    owner = message.text.strip()
    await set_setting("payment_card_owner", owner)
    await state.clear()
    await message.answer(
        f"✅ To'lov kartasi muvaffaqiyatli yangilandi!\nEgasi: **{owner}**",
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "adm_edit_shop_id")
async def edit_shop_id_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminStates.waiting_for_new_shop_id)
    await callback.message.edit_text("Yangi **TolovAPI Shop ID** ni kiriting (masalan: `339`):", parse_mode="Markdown")
    await callback.answer()


@router.message(AdminStates.waiting_for_new_shop_id)
async def process_new_shop_id(message: Message, state: FSMContext) -> None:
    shop_id = message.text.strip()
    await set_setting("tolov_shop_id", shop_id)
    await state.clear()
    await message.answer(f"✅ TolovAPI Shop ID saqlandi: `{shop_id}`", parse_mode="Markdown")


@router.callback_query(F.data == "adm_edit_shop_key")
async def edit_shop_key_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminStates.waiting_for_new_shop_key)
    await callback.message.edit_text("Yangi **TolovAPI Shop Key** ni kiriting:", parse_mode="Markdown")
    await callback.answer()


@router.message(AdminStates.waiting_for_new_shop_key)
async def process_new_shop_key(message: Message, state: FSMContext) -> None:
    shop_key = message.text.strip()
    await set_setting("tolov_shop_key", shop_key)
    await state.clear()
    await message.answer("✅ TolovAPI Shop Key muvaffaqiyatli yangilandi!", parse_mode="Markdown")


# ==============================================================================
# 7. DARSLIK QO'SHISH (SYLLABUS MANAGER)
# ==============================================================================

@router.callback_query(F.data == "adm_add_syllabus")
async def start_add_syllabus(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminStates.syllabus_level)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Beginner", callback_data="syl_Beginner")],
            [InlineKeyboardButton(text="Elementary", callback_data="syl_Elementary")],
            [InlineKeyboardButton(text="Pre-Intermediate", callback_data="syl_Pre-Intermediate")],
            [InlineKeyboardButton(text="Intermediate", callback_data="syl_Intermediate")],
            [InlineKeyboardButton(text="Upper-Intermediate", callback_data="syl_Upper-Intermediate")],
            [InlineKeyboardButton(text="IELTS", callback_data="syl_IELTS")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="adm_back_main")],
        ]
    )
    await callback.message.edit_text(
        "📚 **YANGI DARSLIK QO'SHISH**\n\nQaysi darajaga yangi dars qo'shmoqchisiz?",
        reply_markup=kb,
    )
    await callback.answer()


@router.callback_query(AdminStates.syllabus_level, F.data.startswith("syl_"))
async def select_syllabus_level(callback: CallbackQuery, state: FSMContext) -> None:
    level = callback.data.replace("syl_", "")
    await state.update_data(level=level)
    await state.set_state(AdminStates.syllabus_order)
    current_count = await count_syllabus_lessons(level)
    suggested_order = current_count + 1

    await callback.message.edit_text(
        f"Tanlangan daraja: **{level}** (Hozirda {current_count} ta dars mavjud).\n\n"
        f"Dars tartib raqamini (lesson_order) kiriting (Tavsiya: `{suggested_order}`):",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(AdminStates.syllabus_order)
async def process_syllabus_order(message: Message, state: FSMContext) -> None:
    if not message.text.isdigit():
        await message.answer("Iltimos, faqat musbat son kiriting (masalan, 11):")
        return
    order = int(message.text)
    await state.update_data(order=order)
    await state.set_state(AdminStates.syllabus_title)
    await message.answer("Mavzu nomini kiriting (masalan: `Future Perfect Continuous`):")


@router.message(AdminStates.syllabus_title)
async def process_syllabus_title(message: Message, state: FSMContext) -> None:
    title = message.text.strip()
    await state.update_data(title=title)
    await state.set_state(AdminStates.syllabus_grammar)
    await message.answer("Mavzuning o'zbek tilidagi grammatika xulosasini kiriting:")


@router.message(AdminStates.syllabus_grammar)
async def process_syllabus_grammar(message: Message, state: FSMContext) -> None:
    grammar = message.text.strip()
    await state.update_data(grammar=grammar)
    await state.set_state(AdminStates.syllabus_words)
    await message.answer(
        "Ushbu darsning yangi so'zlarini quyidagi formatda kiriting (har bir qatorda `inglizcha - o'zbekcha`):\n\n"
        "Masalan:\n`achievement - yutuq`\n`struggle - kurash`\n`persevere - sabot qilmoq`",
        parse_mode="Markdown",
    )


@router.message(AdminStates.syllabus_words)
async def process_syllabus_words(message: Message, state: FSMContext) -> None:
    raw_words = message.text.strip().split("\n")
    words_list = []
    for line in raw_words:
        if "-" in line:
            parts = line.split("-", 1)
            en = parts[0].strip()
            uz = parts[1].strip()
            if en and uz:
                words_list.append({"en": en, "uz": uz})

    if not words_list:
        await message.answer("Hech qanday so'z topilmadi! Format: `inglizcha - o'zbekcha` ko'rinishida yuboring:")
        return

    data = await state.get_data()
    level = data["level"]
    order = data["order"]
    title = data["title"]
    grammar = data["grammar"]

    await add_syllabus_lesson(
        level=level,
        lesson_order=order,
        topic_title=title,
        grammar_notes=grammar,
        target_words=words_list,
    )
    await state.clear()
    await message.answer(
        f"🎉 **Darslik muvaffaqiyatli saqlandi!**\n\n"
        f"• Daraja: {level}\n"
        f"• Dars tartibi: #{order}\n"
        f"• Mavzu: {title}\n"
        f"• Yangi so'zlar soni: {len(words_list)} ta",
        parse_mode="Markdown",
    )
