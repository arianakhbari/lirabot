# handlers/admin_handlers.py

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from services.user_service import (
    get_settings,
    update_settings,
    verify_user,
    reject_user,
)
from utils.helpers import is_admin

logger = logging.getLogger(__name__)

# تعریف مراحل ConversationHandler
(
    SELECT_ACTION,
    SET_BUY_RATE,
    SET_SELL_RATE,
    SET_ADMIN_BANK_INFO,
) = range(4)

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ شما دسترسی لازم برای انجام این عمل را ندارید.")
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton("تنظیم نرخ خرید", callback_data='set_buy_rate')],
        [InlineKeyboardButton("تنظیم نرخ فروش", callback_data='set_sell_rate')],
        [InlineKeyboardButton("فعال/غیرفعال کردن خرید", callback_data='toggle_buy')],
        [InlineKeyboardButton("فعال/غیرفعال کردن فروش", callback_data='toggle_sell')],
        [InlineKeyboardButton("تنظیم اطلاعات بانکی", callback_data='set_admin_bank_info')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("⚙️ **پنل مدیریت:**", reply_markup=reply_markup, parse_mode='Markdown')

    return SELECT_ACTION

async def admin_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    user_id = update.effective_user.id
    if not is_admin(user_id):
        await query.message.reply_text("❌ شما دسترسی لازم برای انجام این عمل را ندارید.")
        return ConversationHandler.END

    if data == 'set_buy_rate':
        await query.message.reply_text("📈 لطفاً نرخ خرید جدید را وارد کنید (تومان به ازای هر لیر):")
        return SET_BUY_RATE
    elif data == 'set_sell_rate':
        await query.message.reply_text("📉 لطفاً نرخ فروش جدید را وارد کنید (تومان به ازای هر لیر):")
        return SET_SELL_RATE
    elif data == 'toggle_buy':
        settings = get_settings()
        if settings:
            new_status = not settings.buy_enabled
            update_settings(buy_enabled=new_status)
            status_text = "فعال" if new_status else "غیرفعال"
            await query.message.reply_text(f"📥 قابلیت خرید به {status_text} تغییر یافت.")
        else:
            await query.message.reply_text("⚠️ خطا در بازیابی تنظیمات.")
        return SELECT_ACTION
    elif data == 'toggle_sell':
        settings = get_settings()
        if settings:
            new_status = not settings.sell_enabled
            update_settings(sell_enabled=new_status)
            status_text = "فعال" if new_status else "غیرفعال"
            await query.message.reply_text(f"📤 قابلیت فروش به {status_text} تغییر یافت.")
        else:
            await query.message.reply_text("⚠️ خطا در بازیابی تنظیمات.")
        return SELECT_ACTION
    elif data == 'set_admin_bank_info':
        await query.message.reply_text("🏦 لطفاً اطلاعات حساب بانکی ادمین را وارد کنید:")
        return SET_ADMIN_BANK_INFO
    else:
        await query.message.reply_text("⚠️ گزینه نامعتبر انتخاب شده است.")
        return SELECT_ACTION

async def save_buy_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ شما دسترسی لازم برای انجام این عمل را ندارید.")
        return ConversationHandler.END
    try:
        new_rate = float(update.message.text.strip())
        if new_rate <= 0:
            raise ValueError("نرخ باید بزرگ‌تر از صفر باشد.")
        success = update_settings(buy_rate=new_rate)
        if success:
            await update.message.reply_text(f"📈 نرخ خرید جدید تنظیم شد: {new_rate} تومان به ازای هر لیر.")
        else:
            await update.message.reply_text("⚠️ خطا در تنظیم نرخ خرید. لطفاً دوباره تلاش کنید.")
            return SET_BUY_RATE
    except ValueError as ve:
        await update.message.reply_text(f"⚠️ خطا: {ve}\nلطفاً یک عدد معتبر وارد کنید:")
        return SET_BUY_RATE
    return SELECT_ACTION

async def save_sell_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ شما دسترسی لازم برای انجام این عمل را ندارید.")
        return ConversationHandler.END
    try:
        new_rate = float(update.message.text.strip())
        if new_rate <= 0:
            raise ValueError("نرخ باید بزرگ‌تر از صفر باشد.")
        success = update_settings(sell_rate=new_rate)
        if success:
            await update.message.reply_text(f"📉 نرخ فروش جدید تنظیم شد: {new_rate} تومان به ازای هر لیر.")
        else:
            await update.message.reply_text("⚠️ خطا در تنظیم نرخ فروش. لطفاً دوباره تلاش کنید.")
            return SET_SELL_RATE
    except ValueError as ve:
        await update.message.reply_text(f"⚠️ خطا: {ve}\nلطفاً یک عدد معتبر وارد کنید:")
        return SET_SELL_RATE
    return SELECT_ACTION

async def save_admin_bank_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ شما دسترسی لازم برای انجام این عمل را ندارید.")
        return ConversationHandler.END
    bank_info = update.message.text.strip()
    success = update_settings(admin_bank_info=bank_info)
    if success:
        await update.message.reply_text("🏦 اطلاعات حساب بانکی ادمین ذخیره شد.")
    else:
        await update.message.reply_text("⚠️ خطا در ذخیره اطلاعات بانکی. لطفاً دوباره تلاش کنید.")
        return SET_ADMIN_BANK_INFO
    return SELECT_ACTION

def setup_admin_handlers(application):
    admin_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('admin', admin_panel)],
        states={
            SELECT_ACTION: [
                CallbackQueryHandler(admin_panel_callback),
            ],
            SET_BUY_RATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_buy_rate),
            ],
            SET_SELL_RATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_sell_rate),
            ],
            SET_ADMIN_BANK_INFO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_admin_bank_info),
            ],
        },
        fallbacks=[],
    )

    application.add_handler(admin_conv_handler)
