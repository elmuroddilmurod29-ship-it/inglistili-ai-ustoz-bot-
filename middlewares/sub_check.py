import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware, Bot
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, TelegramObject
from aiogram.enums import ChatMemberStatus
from config import ADMIN_ID
from database import get_mandatory_channels, get_user

logger = logging.getLogger(__name__)


class SubscriptionAndBlockMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        bot: Bot = data.get("bot")

        user_id = None
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id

        if not user_id:
            return await handler(event, data)

        # 1. Admin bypass
        if user_id == ADMIN_ID:
            return await handler(event, data)

        # 2. Check if user is blocked in database
        try:
            db_user = await get_user(user_id)
            if db_user and db_user.get("is_blocked"):
                if isinstance(event, Message):
                    await event.answer("⛔ Siz botdan bloklangansiz. Ma'muriyat bilan bog'laning.")
                elif isinstance(event, CallbackQuery):
                    await event.answer("⛔ Siz botdan bloklangansiz.", show_alert=True)
                return
        except Exception as e:
            logger.error(f"Error checking user block status: {e}")

        # 3. Check mandatory channel subscription
        try:
            channels = await get_mandatory_channels()
            if not channels:
                return await handler(event, data)

            unsubscribed_channels = []
            for ch in channels:
                ch_id = ch["channel_id"]
                try:
                    chat_member = await bot.get_chat_member(chat_id=ch_id, user_id=user_id)
                    if chat_member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]:
                        unsubscribed_channels.append(ch)
                except Exception as ex:
                    logger.warning(f"Could not verify subscription for {ch_id}: {ex}")

            # If user has unsubscribed channels
            if unsubscribed_channels:
                # If this is the 'check_sub' callback
                if isinstance(event, CallbackQuery) and event.data == "check_sub":
                    await event.answer(
                        "⚠️ Hali barcha kanallarga a'zo bo'lmadingiz. Iltimos, a'zo bo'lib qayta bosing!",
                        show_alert=True,
                    )
                    return

                # Build inline keyboard for unsubscribed channels
                buttons = []
                for idx, ch in enumerate(unsubscribed_channels, 1):
                    title = ch["channel_title"] or f"Kanal #{idx}"
                    link = ch["invite_link"] or f"https://t.me/{str(ch['channel_id']).lstrip('@')}"
                    buttons.append([InlineKeyboardButton(text=f"📢 {title}", url=link)])

                buttons.append([InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_sub")])
                sub_keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

                text = (
                    "⚠️ **Botdan to'liq foydalanish uchun quyidagi homiy kanallarga a'zo bo'ling!**\n\n"
                    "A'zo bo'lgach, **'✅ Obunani tekshirish'** tugmasini bosing."
                )

                if isinstance(event, Message):
                    await event.answer(text, reply_markup=sub_keyboard, parse_mode="Markdown")
                elif isinstance(event, CallbackQuery):
                    await event.message.answer(text, reply_markup=sub_keyboard, parse_mode="Markdown")
                    await event.answer()
                return

            # If the user pressed check_sub and is now subscribed to all
            if isinstance(event, CallbackQuery) and event.data == "check_sub":
                await event.answer("✅ Rahmat! Barcha kanallarga a'zo bo'ldingiz.", show_alert=True)
                try:
                    await event.message.delete()
                except Exception:
                    pass
                return

        except Exception as e:
            logger.error(f"Error in subscription middleware: {e}")

        return await handler(event, data)
