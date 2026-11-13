import asyncio
from datetime import datetime, timedelta
import logging
from typing import Any, Dict, Optional
import aiohttp
from aiogram import Bot

from config import (
    ADMIN_ID,
    DEFAULT_TOLOV_SHOP_ID,
    DEFAULT_TOLOV_SHOP_KEY,
    TOLOV_API_URL,
)
from database import get_setting, update_payment_request_status, update_user

logger = logging.getLogger(__name__)

# Keep track of active background monitor tasks: {payment_id: asyncio.Task}
ACTIVE_PAYMENT_TASKS: Dict[str, asyncio.Task] = {}


async def get_tolov_credentials() -> tuple[str, str]:
    """Retrieves dynamic TolovAPI credentials from bot_settings or defaults."""
    shop_id = await get_setting("tolov_shop_id", DEFAULT_TOLOV_SHOP_ID)
    shop_key = await get_setting("tolov_shop_key", DEFAULT_TOLOV_SHOP_KEY)
    return str(shop_id).strip(), str(shop_key).strip()


async def create_tolov_payment(order_id: str, amount: int) -> Dict[str, Any]:
    """Creates a payment on TolovAPI.

    Automatically handles 'amount_busy' with suggested_amount retry.
    """
    shop_id, shop_key = await get_tolov_credentials()
    url = f"{TOLOV_API_URL}payment/create"
    headers = {"X-Shop-Key": shop_key}

    curr_amount = amount
    for attempt in range(2):
        payload = {
            "shop_id": shop_id,
            "amount": curr_amount,
            "order_id": order_id,
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    data = await resp.json()
                    if data.get("error_code") == "amount_busy" and "suggested_amount" in data:
                        logger.info(f"Amount {curr_amount} busy, retrying with suggested {data['suggested_amount']}")
                        curr_amount = data["suggested_amount"]
                        continue
                    return data
        except Exception as e:
            logger.error(f"Error creating TolovAPI payment: {e}")
            return {"ok": False, "error": str(e)}

    return {"ok": False, "error": "To'lov summasi band, qayta urinib ko'ring."}


async def get_tolov_status(payment_id: str) -> Dict[str, Any]:
    """Checks the status of a payment on TolovAPI."""
    shop_id, shop_key = await get_tolov_credentials()
    url = f"{TOLOV_API_URL}payment/status"
    headers = {"X-Shop-Key": shop_key}
    params = {"shop_id": shop_id, "payment_id": payment_id}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                return await resp.json()
    except Exception as e:
        logger.error(f"Error checking TolovAPI status: {e}")
        return {"ok": False, "error": str(e), "status": "error"}


async def cancel_tolov_payment(payment_id: str) -> Dict[str, Any]:
    """Cancels a pending payment on TolovAPI."""
    shop_id, shop_key = await get_tolov_credentials()
    url = f"{TOLOV_API_URL}payment/cancel"
    headers = {"X-Shop-Key": shop_key}
    payload = {"shop_id": shop_id, "payment_id": payment_id}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                return await resp.json()
    except Exception as e:
        logger.error(f"Error cancelling TolovAPI payment: {e}")
        return {"ok": False, "error": str(e)}


async def activate_user_paid_tariff(
    bot: Bot,
    user_id: int,
    tariff: str,
    amount: int,
    payment_id: str,
    req_db_id: Optional[int] = None,
) -> None:
    """Activates the user's 30-day tariff upon successful payment detection."""
    expires_at = (datetime.now() + timedelta(days=30)).strftime("%d.%m.%Y")
    await update_user(user_id, tariff=tariff, tariff_expires_at=expires_at)

    if req_db_id:
        await update_payment_request_status(req_db_id, "approved")

    tariff_titles = {
        "standard_100k": "Standard (25 daqiqa dars)",
        "pro_200k": "Pro (60 daqiqa dars)",
    }
    title = tariff_titles.get(tariff, tariff)

    # 1. Notify user
    user_text = (
        "🎉 **TO'LOVINGIZ MUVAFFAQIYATLI TASDIQLANDI!**\n\n"
        f"Karta orqali **{amount:,} so'm** to'lov qabul qilindi.\n"
        f"Sizga **{title}** tarifi 30 kunga ({expires_at} gacha) faollashtirildi!\n\n"
        "Darsni boshlash uchun quyidagi **'📖 Darsni boshlash'** tugmasini bosing!"
    )
    try:
        await bot.send_message(chat_id=user_id, text=user_text, parse_mode="Markdown")
    except Exception as e:
        logger.warning(f"Could not notify user {user_id}: {e}")

    # 2. Notify ADMIN_ID
    admin_text = (
        "💰 **AVTOMATIK TO'LOV QABUL QILINDI!**\n\n"
        f"• **Foydalanuvchi ID:** `{user_id}`\n"
        f"• **Tarif:** {title}\n"
        f"• **Summa:** {amount:,} so'm\n"
        f"• **Payment ID:** `{payment_id}`\n"
        f"• **Amal qilish muddati:** {expires_at} gacha\n"
        f"Tizim foydalanuvchi tarifini avtomatik faollashtirdi. ✅"
    )
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="Markdown")
    except Exception as e:
        logger.warning(f"Could not notify admin: {e}")


async def monitor_payment_loop(
    bot: Bot,
    payment_id: str,
    user_id: int,
    tariff: str,
    amount: int,
    req_db_id: Optional[int] = None,
    max_duration_seconds: int = 300,
) -> None:
    """Background polling loop that checks TolovAPI payment status every 3 seconds for up to 5 minutes."""
    start_time = datetime.now()
    logger.info(f"Started TolovAPI monitor for payment {payment_id} (user {user_id}).")

    try:
        while (datetime.now() - start_time).total_seconds() < max_duration_seconds:
            await asyncio.sleep(3)
            status_data = await get_tolov_status(payment_id)

            if status_data.get("ok") and status_data.get("status") == "paid":
                logger.info(f"Payment {payment_id} confirmed as PAID!")
                await activate_user_paid_tariff(
                    bot=bot,
                    user_id=user_id,
                    tariff=tariff,
                    amount=amount,
                    payment_id=payment_id,
                    req_db_id=req_db_id,
                )
                break
            elif status_data.get("status") in ["cancel", "expired"]:
                logger.info(f"Payment {payment_id} was cancelled or expired.")
                break
    except asyncio.CancelledError:
        logger.info(f"Payment monitor for {payment_id} cancelled.")
    except Exception as e:
        logger.error(f"Error in payment monitor loop: {e}")
    finally:
        ACTIVE_PAYMENT_TASKS.pop(payment_id, None)


def start_payment_monitor_task(
    bot: Bot,
    payment_id: str,
    user_id: int,
    tariff: str,
    amount: int,
    req_db_id: Optional[int] = None,
) -> None:
    """Launches an asynchronous monitoring task for the given payment."""
    task = asyncio.create_task(
        monitor_payment_loop(
            bot=bot,
            payment_id=payment_id,
            user_id=user_id,
            tariff=tariff,
            amount=amount,
            req_db_id=req_db_id,
        )
    )
    ACTIVE_PAYMENT_TASKS[payment_id] = task
