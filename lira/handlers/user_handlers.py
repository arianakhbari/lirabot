# handlers/user_handlers.py

import logging
import os
from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)
from services.user_service import register_user, get_user_by_telegram_id
from services.admin_service import get_settings
from keyboards.user_keyboards import main_menu_keyboard
from utils.helpers import is_admin

logger = logging.getLogger(__name__)

# تعریف حالات ConversationHandler مربوط به کاربران
(
    NAME, FAMILY_NAME, COUNTRY, PHONE, ID_CARD,

    SELECT_TRANSACTION_TYPE, TRANSACTION_AMOUNT_TYPE, AMOUNT, CONFIRM_TRANSACTION,
    SEND_PAYMENT_PROOF,

    BANK_COUNTRY, BANK_NAME, BANK_ACCOUNT_NUMBER,

    SET_BUY_RATE, SET_SELL_RATE, TOGGLE_BUY, TOGGLE_SELL, SET_ADMIN_BANK_INFO
) = range(18)

# تابع شروع
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user = get_user_by_telegram_id(user_id)
    if user:
        if user.is_verified:
            await update.message.reply_text(
                "✅ شما قبلاً ثبت‌نام کرده‌اید و حساب شما تأیید شده است.",
                reply_markup=ReplyKeyboardRemove()
            )
            await main_menu(update, context)
        else:
            await update.message.reply_text(
                "⏳ حساب شما در انتظار تأیید است. لطفاً صبور باشید.",
                reply_markup=ReplyKeyboardRemove()
            )
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "👋 سلام! برای استفاده از ربات، لطفاً فرآیند احراز هویت را تکمیل کنید.\nلطفاً نام خود را وارد کنید:",
            reply_markup=ReplyKeyboardRemove()
        )
        return NAME

# دریافت نام
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if not name:
        await update.message.reply_text(
            "⚠️ نام نمی‌تواند خالی باشد. لطفاً دوباره وارد کنید:"
        )
        return NAME
    context.user_data['name'] = name
    await update.message.reply_text("👤 لطفاً نام خانوادگی خود را وارد کنید:")
    return FAMILY_NAME

# دریافت نام خانوادگی
async def get_family_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    family_name = update.message.text.strip()
    if not family_name:
        await update.message.reply_text(
            "⚠️ نام خانوادگی نمی‌تواند خالی باشد. لطفاً دوباره وارد کنید:"
        )
        return FAMILY_NAME
    context.user_data['family_name'] = family_name
    keyboard = [
        [KeyboardButton("🇮🇷 ایران"), KeyboardButton("🇹🇷 ترکیه")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "🌍 کشور محل سکونت خود را انتخاب کنید:",
        reply_markup=reply_markup
    )
    return COUNTRY

# دریافت کشور
async def get_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    country = update.message.text.strip()
    if country not in ["🇮🇷 ایران", "🇹🇷 ترکیه"]:
        await update.message.reply_text(
            "⚠️ لطفاً یکی از گزینه‌های موجود را انتخاب کنید.",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("🇮🇷 ایران"), KeyboardButton("🇹🇷 ترکیه")]],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return COUNTRY
    context.user_data['country'] = 'Iran' if country == "🇮🇷 ایران" else 'Turkey'
    keyboard = [
        [KeyboardButton("📞 ارسال شماره تلفن", request_contact=True)]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "📱 لطفاً شماره تلفن خود را به اشتراک بگذارید:",
        reply_markup=reply_markup
    )
    return PHONE

# دریافت شماره تلفن
async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    if not contact:
        await update.message.reply_text(
            "⚠️ لطفاً شماره تلفن خود را ارسال کنید.",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("📞 ارسال شماره تلفن", request_contact=True)]],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return PHONE

    # حذف کاراکترهای غیرعددی
    phone_number = ''.join(filter(str.isdigit, contact.phone_number))
    logger.info(f"Received phone number: {contact.phone_number}")
    logger.info(f"Sanitized phone number: {phone_number}")

    # اعتبارسنجی شماره تلفن
    if not phone_number or len(phone_number) < 10 or len(phone_number) > 15:
        await update.message.reply_text(
            "⚠️ شماره تلفن نامعتبر است. لطفاً یک شماره تلفن معتبر ارسال کنید:"
        )
        return PHONE

    context.user_data['phone'] = phone_number
    await update.message.reply_text(
        "📄 لطفاً تصویر کارت ملی یا پاسپورت خود را ارسال کنید:",
        reply_markup=ReplyKeyboardRemove()
    )
    return ID_CARD

# دریافت تصویر کارت ملی یا پاسپورت
async def get_id_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not update.message.photo:
        await update.message.reply_text("⚠️ لطفاً یک تصویر ارسال کنید.")
        return ID_CARD
    photo = update.message.photo[-1]
    file_size = photo.file_size
    if file_size > 5 * 1024 * 1024:  # حداکثر 5 مگابایت
        await update.message.reply_text("⚠️ اندازه فایل بیش از حد مجاز است (حداکثر 5 مگابایت). لطفاً عکس کوچکتری ارسال کنید.")
        return ID_CARD
    # بررسی نوع فایل (مثلاً JPEG یا PNG)
    mime_type = photo.mime_type if hasattr(photo, 'mime_type') else 'image/jpeg'  # فرض بر JPEG
    if not mime_type.startswith('image/'):
        await update.message.reply_text("⚠️ فقط فایل‌های تصویری مجاز هستند. لطفاً یک تصویر ارسال کنید.")
        return ID_CARD
    photo_file = await photo.get_file()
    if not os.path.exists('user_data'):
        os.makedirs('user_data')
    photo_path = f"user_data/{user_id}_id.jpg"
    await photo_file.download_to_drive(custom_path=photo_path)
    context.user_data['id_card'] = photo_path
    await update.message.reply_text("📥 اطلاعات شما دریافت شد و در انتظار تأیید ادمین است.")

    # ذخیره اطلاعات کاربر در دیتابیس
    user = register_user(
        telegram_id=user_id,
        name=context.user_data['name'],
        family_name=context.user_data['family_name'],
        country=context.user_data['country'],
        phone=context.user_data['phone'],
        id_card_path=photo_path
    )
    if not user:
        await update.message.reply_text("⚠️ خطا در ذخیره‌سازی اطلاعات شما. لطفاً دوباره تلاش کنید.")
        return ConversationHandler.END

    # اطلاع رسانی به ادمین‌ها
    settings = get_settings()
    if not settings:
        logger.warning("Settings not found while notifying admins.")
    for admin_id in settings.admin_ids:
        await context.bot.send_message(
            chat_id=admin_id,
            text=(
                f"📋 کاربر جدید:\n"
                f"👤 نام: {user.name} {user.family_name}\n"
                f"🌍 کشور: {user.country}\n"
                f"📞 شماره تلفن: {user.phone}"
            )
        )
        with open(photo_path, 'rb') as photo_file_obj:
            await context.bot.send_photo(chat_id=admin_id, photo=photo_file_obj)
        keyboard = [
            [InlineKeyboardButton("✅ تأیید", callback_data=f'approve_user_{user.id}'),
             InlineKeyboardButton("❌ رد", callback_data=f'reject_user_{user.id}')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=admin_id,
            text=f"🔄 لطفاً کاربر {user.id} را تأیید یا رد کنید:",
            reply_markup=reply_markup
        )
    return ConversationHandler.END

# لغو فرآیند
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        '⛔️ فرآیند لغو شد.',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# منوی اصلی
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = main_menu_keyboard(is_admin=is_admin(user_id))
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "📂 به منوی اصلی خوش آمدید. لطفاً یکی از گزینه‌ها را انتخاب کنید:",
        reply_markup=reply_markup
    )
