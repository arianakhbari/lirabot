# handlers/admin_handlers.py

import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)
from services.user_service import (
    get_settings,
    update_settings,
    verify_user,
    reject_user,
    get_user_by_id,
    get_transaction_by_id,
    update_transaction,
    update_transaction_status,
)
from utils.helpers import is_admin
from config import CHANNEL_ID
import os

logger = logging.getLogger(__name__)

# تعریف مراحل
SELECT_ACTION, SET_BUY_RATE, SET_SELL_RATE, SET_ADMIN_BANK_INFO_IRAN, SET_ADMIN_BANK_INFO_TURKEY, ADMIN_SEND_PROOF = range(6)

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ شما دسترسی لازم برای انجام این عمل را ندارید.")
        return ConversationHandler.END

    keyboard = [
        [KeyboardButton("تنظیم نرخ خرید"), KeyboardButton("تنظیم نرخ فروش")],
        [KeyboardButton("فعال/غیرفعال کردن خرید"), KeyboardButton("فعال/غیرفعال کردن فروش")],
        [KeyboardButton("تنظیم حساب بانکی ایران"), KeyboardButton("تنظیم حساب بانکی ترکیه")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("⚙️ **پنل مدیریت:**\nلطفاً یکی از گزینه‌ها را انتخاب کنید:", reply_markup=reply_markup, parse_mode='Markdown')

    return SELECT_ACTION

async def admin_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "تنظیم نرخ خرید":
        await update.message.reply_text("📈 لطفاً نرخ خرید جدید را وارد کنید (تومان به ازای هر لیر):", reply_markup=ReplyKeyboardRemove())
        return SET_BUY_RATE
    elif text == "تنظیم نرخ فروش":
        await update.message.reply_text("📉 لطفاً نرخ فروش جدید را وارد کنید (تومان به ازای هر لیر):", reply_markup=ReplyKeyboardRemove())
        return SET_SELL_RATE
    elif text == "فعال/غیرفعال کردن خرید":
        settings = get_settings()
        if settings:
            new_status = not settings.buy_enabled
            update_settings(buy_enabled=new_status)
            status_text = "فعال" if new_status else "غیرفعال"
            await update.message.reply_text(f"📥 قابلیت خرید به {status_text} تغییر یافت.")
        else:
            await update.message.reply_text("⚠️ خطا در بازیابی تنظیمات.")
        return ConversationHandler.END
    elif text == "فعال/غیرفعال کردن فروش":
        settings = get_settings()
        if settings:
            new_status = not settings.sell_enabled
            update_settings(sell_enabled=new_status)
            status_text = "فعال" if new_status else "غیرفعال"
            await update.message.reply_text(f"📤 قابلیت فروش به {status_text} تغییر یافت.")
        else:
            await update.message.reply_text("⚠️ خطا در بازیابی تنظیمات.")
        return ConversationHandler.END
    elif text == "تنظیم حساب بانکی ایران":
        await update.message.reply_text("🏦 لطفاً اطلاعات حساب بانکی ایران را وارد کنید:", reply_markup=ReplyKeyboardRemove())
        return SET_ADMIN_BANK_INFO_IRAN
    elif text == "تنظیم حساب بانکی ترکیه":
        await update.message.reply_text("🏦 لطفاً اطلاعات حساب بانکی ترکیه را وارد کنید:", reply_markup=ReplyKeyboardRemove())
        return SET_ADMIN_BANK_INFO_TURKEY
    else:
        await update.message.reply_text("⚠️ گزینه نامعتبر انتخاب شده است.")
        return ConversationHandler.END

async def save_buy_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        new_rate = float(update.message.text.strip())
        if new_rate <= 0:
            raise ValueError("نرخ باید بزرگ‌تر از صفر باشد.")
        success = update_settings(buy_rate=new_rate)
        if success:
            await update.message.reply_text(f"📈 نرخ خرید جدید تنظیم شد: {new_rate} تومان به ازای هر لیر.")
        else:
            await update.message.reply_text("⚠️ خطا در تنظیم نرخ خرید. لطفاً دوباره تلاش کنید.")
    except ValueError as ve:
        await update.message.reply_text(f"⚠️ خطا: {ve}\nلطفاً یک عدد معتبر وارد کنید:")
        return SET_BUY_RATE
    return ConversationHandler.END

async def save_sell_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        new_rate = float(update.message.text.strip())
        if new_rate <= 0:
            raise ValueError("نرخ باید بزرگ‌تر از صفر باشد.")
        success = update_settings(sell_rate=new_rate)
        if success:
            await update.message.reply_text(f"📉 نرخ فروش جدید تنظیم شد: {new_rate} تومان به ازای هر لیر.")
        else:
            await update.message.reply_text("⚠️ خطا در تنظیم نرخ فروش. لطفاً دوباره تلاش کنید.")
    except ValueError as ve:
        await update.message.reply_text(f"⚠️ خطا: {ve}\nلطفاً یک عدد معتبر وارد کنید:")
        return SET_SELL_RATE
    return ConversationHandler.END

async def save_admin_bank_info_iran(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bank_info = update.message.text.strip()
    success = update_settings(admin_iran_bank_info=bank_info)
    if success:
        await update.message.reply_text("🏦 اطلاعات حساب بانکی ایران ذخیره شد.")
    else:
        await update.message.reply_text("⚠️ خطا در ذخیره اطلاعات بانکی. لطفاً دوباره تلاش کنید.")
    return ConversationHandler.END

async def save_admin_bank_info_turkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bank_info = update.message.text.strip()
    success = update_settings(admin_turkey_bank_info=bank_info)
    if success:
        await update.message.reply_text("🏦 اطلاعات حساب بانکی ترکیه ذخیره شد.")
    else:
        await update.message.reply_text("⚠️ خطا در ذخیره اطلاعات بانکی. لطفاً دوباره تلاش کنید.")
    return ConversationHandler.END

async def handle_admin_transactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.startswith('تأیید'):
        try:
            transaction_id = int(text.split(' ')[1])
            transaction = get_transaction_by_id(transaction_id)
            if transaction and transaction.status == 'pending':
                # به‌روزرسانی وضعیت تراکنش
                update_transaction_status(transaction_id, 'admin_approved')

                user = get_user_by_id(transaction.user_id)
                settings = get_settings()
                if transaction.transaction_type == 'buy':
                    bank_info = settings.admin_iran_bank_info
                else:
                    bank_info = settings.admin_turkey_bank_info

                if not bank_info:
                    await update.message.reply_text("⚠️ اطلاعات حساب ادمین موجود نیست.")
                    return ConversationHandler.END

                await context.bot.send_message(
                    chat_id=user.telegram_id,
                    text=f"✅ ادمین تراکنش شما را تأیید کرد.\nلطفاً مبلغ را به حساب زیر واریز کنید:\n{bank_info}\nسپس فیش واریزی را ارسال کنید."
                )

                # ذخیره آیدی تراکنش در user_data کاربر
                context.user_data['transaction_id'] = transaction_id

                # اطلاع‌رسانی به ادمین
                await update.message.reply_text(f"تراکنش {transaction_id} تأیید شد.")

                return ConversationHandler.END
            else:
                await update.message.reply_text("⚠️ تراکنش معتبر نیست یا قبلاً پردازش شده است.")
                return ConversationHandler.END
        except Exception as e:
            logger.error(f"Error processing transaction approval: {e}")
            await update.message.reply_text("⚠️ خطا در پردازش درخواست.")
            return ConversationHandler.END
    elif text.startswith('رد'):
        try:
            transaction_id = int(text.split(' ')[1])
            transaction = get_transaction_by_id(transaction_id)
            if transaction and transaction.status == 'pending':
                # به‌روزرسانی وضعیت تراکنش
                update_transaction_status(transaction_id, 'admin_rejected')

                # اطلاع‌رسانی به کاربر
                user = get_user_by_id(transaction.user_id)
                await context.bot.send_message(
                    chat_id=user.telegram_id,
                    text="❌ تراکنش شما توسط ادمین رد شد."
                )

                await update.message.reply_text(f"تراکنش {transaction_id} رد شد.")
                return ConversationHandler.END
            else:
                await update.message.reply_text("⚠️ تراکنش معتبر نیست یا قبلاً پردازش شده است.")
                return ConversationHandler.END
        except Exception as e:
            logger.error(f"Error processing transaction rejection: {e}")
            await update.message.reply_text("⚠️ خطا در پردازش درخواست.")
            return ConversationHandler.END
    else:
        await update.message.reply_text("⚠️ دستور نامعتبر است. لطفاً از فرمت صحیح استفاده کنید.")
        return ConversationHandler.END

async def admin_send_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    transaction_id = context.user_data.get('transaction_id')
    if not transaction_id:
        await update.message.reply_text("⚠️ خطا: آیدی تراکنش یافت نشد.")
        return ConversationHandler.END

    if update.message.photo:
        photo = update.message.photo[-1]
        os.makedirs('admin_proofs', exist_ok=True)
        file_path = f"admin_proofs/{transaction_id}_admin_proof.jpg"
        await photo.get_file().download(file_path)

        # به‌روزرسانی تراکنش با فیش واریزی ادمین
        success = update_transaction(
            transaction_id,
            admin_proof_path=file_path,
            status='completed'  # تراکنش تکمیل شده
        )

        if success:
            transaction = get_transaction_by_id(transaction_id)
            user = get_user_by_id(transaction.user_id)

            # ارسال فیش واریزی به کاربر
            await context.bot.send_message(
                chat_id=user.telegram_id,
                text="✅ ادمین مبلغ را به حساب شما واریز کرد. فیش واریزی را در زیر مشاهده کنید."
            )
            await context.bot.send_photo(
                chat_id=user.telegram_id,
                photo=open(file_path, 'rb')
            )

            # اطلاع‌رسانی به ادمین
            await update.message.reply_text("✅ فیش واریزی ارسال شد و تراکنش تکمیل گردید.")

            # بایگانی در کانال خصوصی
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=f"📁 تراکنش تکمیل شده:\n{transaction}"
            )

        else:
            await update.message.reply_text("⚠️ خطا در به‌روزرسانی تراکنش.")
    else:
        await update.message.reply_text("⚠️ لطفاً یک عکس ارسال کنید.")

    return ConversationHandler.END

def setup_admin_handlers(application):
    admin_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('admin', admin_panel)],
        states={
            SELECT_ACTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_options),
            ],
            SET_BUY_RATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_buy_rate),
            ],
            SET_SELL_RATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_sell_rate),
            ],
            SET_ADMIN_BANK_INFO_IRAN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_admin_bank_info_iran),
            ],
            SET_ADMIN_BANK_INFO_TURKEY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_admin_bank_info_turkey),
            ],
            ADMIN_SEND_PROOF: [
                MessageHandler(filters.PHOTO & ~filters.COMMAND, admin_send_proof),
            ],
        },
        fallbacks=[],
    )

    application.add_handler(admin_conv_handler)

    # هندلر برای تأیید یا رد تراکنش‌ها
    application.add_handler(MessageHandler(filters.TEXT & filters.User(ADMIN_IDS), handle_admin_transactions))
