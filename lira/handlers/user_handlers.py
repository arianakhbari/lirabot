# handlers/user_handlers.py

from telegram import Update
from telegram.ext import ContextTypes
from services.user_service import register_user, get_settings
import logging

logger = logging.getLogger(__name__)

async def get_id_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    photo = update.message.photo[-1]
    file_path = f"user_data/{update.message.from_user.id}_id_card.jpg"
    await photo.get_file().download(file_path)
    user_data['id_card_path'] = file_path

    # ثبت کاربر در پایگاه داده
    user = register_user(
        telegram_id=update.message.from_user.id,
        name=user_data['name'],
        family_name=user_data['family_name'],
        country=user_data['country'],
        phone=user_data['phone'],
        id_card_path=file_path
    )

    if user:
        await update.message.reply_text("📥 اطلاعات شما دریافت شد و در انتظار تأیید ادمین است.")

        # ارسال پیام به ادمین‌ها برای اطلاع‌رسانی
        settings = get_settings()
        if settings and settings.admin_ids:
            for admin_id in settings.admin_ids:
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=f"کاربر جدید {user.name} {user.family_name} نیاز به تأیید دارد."
                    )
                except Exception as e:
                    logger.error(f"Error sending message to admin {admin_id}: {e}")
        else:
            logger.warning("No admin IDs found in settings.")
    else:
        await update.message.reply_text("⚠️ خطا در ذخیره‌سازی اطلاعات شما. لطفاً دوباره تلاش کنید.")

    return ConversationHandler.END
