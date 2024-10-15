# handlers/admin_handlers.py

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
from services.admin_service import (
    get_settings,
    update_buy_rate,
    update_sell_rate,
    toggle_buy_enabled,
    toggle_sell_enabled,
    update_admin_bank_info
)
from services.user_service import verify_user, reject_user
from utils.helpers import is_admin
from keyboards.admin_keyboards import admin_panel_keyboard

logger = logging.getLogger(__name__)

# تعریف حالات ConversationHandler مربوط به ادمین‌ها
SET_ADMIN_BANK_INFO = 100  # حالت جداگانه برای تنظیم اطلاعات بانکی ادمین

# پنل مدیریت
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ شما دسترسی لازم برای انجام این عمل را ندارید.")
        return ConversationHandler.END
    keyboard = admin_panel_keyboard()
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("⚙️ **پنل مدیریت:**", reply_markup=reply_markup)

# تنظیم نرخ خرید
async def set_buy_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📈 لطفاً نرخ خرید جدید را وارد کنید (تومان به لیر):",
        reply_markup=ReplyKeyboardRemove()
    )
    return SET_BUY_RATE

# ذخیره نرخ خرید
async def save_buy_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        new_rate = float(update.message.text.strip())
        if new_rate <= 0:
            raise ValueError("نرخ باید بزرگ‌تر از صفر باشد.")
        success = update_buy_rate(new_rate)
        if success:
            await update.message.reply_text(f"📈 نرخ خرید جدید تنظیم شد: {new_rate} تومان به ازای هر لیر.")
        else:
            await update.message.reply_text("⚠️ خطا در تنظیم نرخ خرید. لطفاً دوباره تلاش کنید.")
            return SET_BUY_RATE
    except ValueError as ve:
        await update.message.reply_text(f"⚠️ خطا: {ve}. لطفاً یک عدد معتبر و بزرگ‌تر از صفر وارد کنید:")
        return SET_BUY_RATE
    await admin_panel(update, context)
    return ConversationHandler.END

# تنظیم نرخ فروش
async def set_sell_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📉 لطفاً نرخ فروش جدید را وارد کنید (لیر به تومان):",
        reply_markup=ReplyKeyboardRemove()
    )
    return SET_SELL_RATE

# ذخیره نرخ فروش
async def save_sell_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        new_rate = float(update.message.text.strip())
        if new_rate <= 0:
            raise ValueError("نرخ باید بزرگ‌تر از صفر باشد.")
        success = update_sell_rate(new_rate)
        if success:
            await update.message.reply_text(f"📉 نرخ فروش جدید تنظیم شد: {new_rate} تومان به ازای هر لیر.")
        else:
            await update.message.reply_text("⚠️ خطا در تنظیم نرخ فروش. لطفاً دوباره تلاش کنید.")
            return SET_SELL_RATE
    except ValueError as ve:
        await update.message.reply_text(f"⚠️ خطا: {ve}. لطفاً یک عدد معتبر و بزرگ‌تر از صفر وارد کنید:")
        return SET_SELL_RATE
    await admin_panel(update, context)
    return ConversationHandler.END

# غیرفعال یا فعال کردن خرید
async def toggle_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ شما دسترسی لازم برای انجام این عمل را ندارید.")
        return ConversationHandler.END
    new_status = toggle_buy_enabled()
    if new_status is not None:
        status_text = "✅ فعال" if new_status else "❌ غیرفعال"
        await update.message.reply_text(f"📈 قابلیت خرید لیر به حالت `{status_text}` تغییر یافت.", parse_mode='Markdown')
    else:
        await update.message.reply_text("⚠️ خطا در تغییر وضعیت خرید.")
    await admin_panel(update, context)
    return ConversationHandler.END

# غیرفعال یا فعال کردن فروش
async def toggle_sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ شما دسترسی لازم برای انجام این عمل را ندارید.")
        return ConversationHandler.END
    new_status = toggle_sell_enabled()
    if new_status is not None:
        status_text = "✅ فعال" if new_status else "❌ غیرفعال"
        await update.message.reply_text(f"📉 قابلیت فروش لیر به حالت `{status_text}` تغییر یافت.", parse_mode='Markdown')
    else:
        await update.message.reply_text("⚠️ خطا در تغییر وضعیت فروش.")
    await admin_panel(update, context)
    return ConversationHandler.END

# تنظیم اطلاعات بانکی ادمین
async def set_admin_bank_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ شما دسترسی لازم برای انجام این عمل را ندارید.")
        return ConversationHandler.END
    text = update.message.text.strip()
    # فرض بر این است که کاربر متن را به صورت "کشور: اطلاعات" وارد می‌کند
    try:
        country, bank_info = text.split(":", 1)
        country = country.strip()
        bank_info = bank_info.strip()
        if country not in ['Iran', 'Turkey']:
            raise ValueError("کشور باید 'Iran' یا 'Turkey' باشد.")
        success = update_admin_bank_info(country, bank_info)
        if success:
            await update.message.reply_text(f"🔸 اطلاعات حساب بانکی {country} ادمین ذخیره شد.")
        else:
            await update.message.reply_text("⚠️ خطا در ذخیره اطلاعات بانکی ادمین.")
    except ValueError as ve:
        await update.message.reply_text(f"⚠️ خطا: {ve}. لطفاً اطلاعات را به صورت 'کشور: اطلاعات' وارد کنید.")
        return SET_ADMIN_BANK_INFO
    await admin_panel(update, context)
    return ConversationHandler.END

# تایید یا رد کاربران توسط ادمین
async def approve_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    settings = get_settings()
    if data.startswith('approve_user_'):
        user_id = int(data.split('_')[-1])
        success = verify_user(user_id)
        if success:
            await context.bot.send_message(
                chat_id=user_id,
                text="✅ حساب شما تأیید شد! اکنون می‌توانید از امکانات ربات استفاده کنید."
            )
            await query.edit_message_text("✅ کاربر تأیید شد.")
        else:
            await query.edit_message_text("⚠️ خطا در تأیید کاربر.")
    elif data.startswith('reject_user_'):
        user_id = int(data.split('_')[-1])
        success = reject_user(user_id)
        if success:
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ حساب شما توسط ادمین رد شد."
            )
            await query.edit_message_text("❌ کاربر رد شد.")
        else:
            await query.edit_message_text("⚠️ خطا در رد کاربر.")
    else:
        await query.edit_message_text("⚠️ گزینه نامعتبری انتخاب شده است.")
    return ConversationHandler.END
