# handlers/user_handlers.py

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
from services.user_service import register_user
from config import ADMIN_IDS
import logging

logger = logging.getLogger(__name__)

# مراحل ConversationHandler
(
    NAME,
    FAMILY_NAME,
    COUNTRY,
    PHONE,
    ID_CARD,
) = range(5)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! لطفاً نام خود را وارد کنید:")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("لطفاً نام خانوادگی خود را وارد کنید:")
    return FAMILY_NAME

async def get_family_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['family_name'] = update.message.text
    await update.message.reply_text("لطفاً کشور خود را وارد کنید:")
    return COUNTRY

async def get_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['country'] = update.message.text
    await update.message.reply_text("لطفاً شماره تلفن خود را وارد کنید:")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.text
    await update.message.reply_text("لطفاً عکس کارت شناسایی خود را ارسال کنید:")
    return ID_CARD

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
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=f"کاربر جدید {user.name} {user.family_name} نیاز به تأیید دارد."
                )
            except Exception as e:
                logger.error(f"Error sending message to admin {admin_id}: {e}")
    else:
        await update.message.reply_text("⚠️ خطا در ذخیره‌سازی اطلاعات شما. لطفاً دوباره تلاش کنید.")

    return ConversationHandler.END
