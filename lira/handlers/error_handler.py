# handlers/error_handler.py

import logging
from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_IDS

logger = logging.getLogger(__name__)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    # ارسال پیام خطا به کاربر
    if isinstance(update, Update) and update.effective_chat:
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="⚠️ خطایی در سرور رخ داده است. لطفاً بعداً تلاش کنید."
            )
        except Exception as e:
            logger.error(f"Error sending error message to user: {e}")
    # ارسال پیام خطا به ادمین‌ها
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"⚠️ یک خطا در ربات رخ داده است:\n{context.error}"
            )
        except Exception as e:
            logger.error(f"Error sending error message to admin {admin_id}: {e}")
