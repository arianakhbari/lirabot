# handlers/user_handlers.py

from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CommandHandler
from services.user_service import (
    register_user,
    get_user_by_telegram_id,
    update_user_bank_info,
    create_transaction,
    get_transaction_by_id,
    get_transactions_by_user_id,
    update_transaction,
    get_settings,
)
from config import ADMIN_IDS, CHANNEL_ID
import logging
import os

logger = logging.getLogger(__name__)

# مراحل ConversationHandler
(
    NAME,
    FAMILY_NAME,
    COUNTRY,
    PHONE,
    ID_CARD,
    IRAN_BANK_INFO,
    TURKEY_BANK_INFO,
    TRANSACTION_AMOUNT,
    TRANSACTION_CONFIRM,
    TRANSACTION_PROOF,
) = range(10)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user_by_telegram_id(update.effective_user.id)
    if user:
        await update.message.reply_text("شما قبلاً ثبت‌نام کرده‌اید. از /menu برای دسترسی به منو استفاده کنید.")
        return ConversationHandler.END
    await update.message.reply_text("سلام! لطفاً نام خود را وارد کنید:")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text.strip()
    await update.message.reply_text("لطفاً نام خانوادگی خود را وارد کنید:")
    return FAMILY_NAME

async def get_family_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['family_name'] = update.message.text.strip()
    # انتخاب کشور با استفاده از دکمه‌های کیبورد
    keyboard = [
        [KeyboardButton("ایران 🇮🇷"), KeyboardButton("ترکیه 🇹🇷")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("لطفاً کشور خود را انتخاب کنید:", reply_markup=reply_markup)
    return COUNTRY

async def get_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['country'] = update.message.text.strip()
    # درخواست شماره تلفن با استفاده از دکمه تماس
    keyboard = [[KeyboardButton("ارسال شماره تلفن 📱", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("لطفاً شماره تلفن خود را ارسال کنید:", reply_markup=reply_markup)
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        phone_number = update.message.contact.phone_number
    else:
        phone_number = update.message.text.strip()
    context.user_data['phone'] = phone_number
    await update.message.reply_text("لطفاً عکس کارت شناسایی خود را ارسال کنید:", reply_markup=ReplyKeyboardRemove())
    return ID_CARD

async def get_id_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    photo = update.message.photo[-1]
    os.makedirs('user_data', exist_ok=True)
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

# منوی اصلی برای کاربر
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user_by_telegram_id(update.effective_user.id)
    if not user or not user.is_verified:
        await update.message.reply_text("❌ شما هنوز تأیید نشده‌اید. لطفاً منتظر تأیید ادمین باشید.")
        return

    keyboard = [
        [KeyboardButton("💰 خرید لیر"), KeyboardButton("💵 فروش لیر")],
        [KeyboardButton("💳 تنظیم حساب‌های بانکی"), KeyboardButton("📊 پیگیری تراکنش‌ها")],
        [KeyboardButton("ℹ️ اطلاعات حساب"), KeyboardButton("❓ راهنما")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("به منوی اصلی خوش آمدید. لطفاً یکی از گزینه‌ها را انتخاب کنید:", reply_markup=reply_markup)

# تنظیم حساب‌های بانکی
async def set_bank_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("لطفاً اطلاعات حساب بانکی ایران خود را وارد کنید (یا بنویسید 'ندارم'):")
    return IRAN_BANK_INFO

async def get_iran_bank_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    iran_bank_info = update.message.text.strip()
    context.user_data['iran_bank_info'] = iran_bank_info
    await update.message.reply_text("لطفاً اطلاعات حساب بانکی ترکیه خود را وارد کنید (یا بنویسید 'ندارم'):")
    return TURKEY_BANK_INFO

async def get_turkey_bank_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    turkey_bank_info = update.message.text.strip()
    context.user_data['turkey_bank_info'] = turkey_bank_info

    # به‌روزرسانی اطلاعات بانکی کاربر
    success = update_user_bank_info(
        telegram_id=update.effective_user.id,
        iran_bank_info=context.user_data['iran_bank_info'],
        turkey_bank_info=context.user_data['turkey_bank_info']
    )

    if success:
        await update.message.reply_text("✅ اطلاعات حساب‌های بانکی شما با موفقیت ذخیره شد.", reply_markup=ReplyKeyboardRemove())
    else:
        await update.message.reply_text("⚠️ خطا در ذخیره اطلاعات. لطفاً دوباره تلاش کنید.", reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END

# خرید لیر
async def buy_lira(update: Update, context: ContextTypes.DEFAULT_TYPE):
    settings = get_settings()
    if not settings.sell_enabled:
        await update.message.reply_text("❌ خرید لیر در حال حاضر غیرفعال است.")
        return ConversationHandler.END

    await update.message.reply_text("مقدار لیر مورد نظر برای خرید را وارد کنید:")
    context.user_data['transaction_type'] = 'buy'
    return TRANSACTION_AMOUNT

# فروش لیر
async def sell_lira(update: Update, context: ContextTypes.DEFAULT_TYPE):
    settings = get_settings()
    if not settings.buy_enabled:
        await update.message.reply_text("❌ فروش لیر در حال حاضر غیرفعال است.")
        return ConversationHandler.END

    await update.message.reply_text("مقدار لیر مورد نظر برای فروش را وارد کنید:")
    context.user_data['transaction_type'] = 'sell'
    return TRANSACTION_AMOUNT

async def get_transaction_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.strip())
        if amount <= 0:
            raise ValueError("مقدار باید بزرگ‌تر از صفر باشد.")
        context.user_data['amount'] = amount

        # محاسبه مبلغ کل
        settings = get_settings()
        if context.user_data['transaction_type'] == 'buy':
            rate = settings.sell_rate
            total_price = amount * rate
        else:
            rate = settings.buy_rate
            total_price = amount * rate

        context.user_data['total_price'] = total_price
        context.user_data['rate'] = rate

        # ارسال خلاصه تراکنش به کاربر
        summary = f"""
💰 **خلاصه تراکنش:**
- نوع تراکنش: {'خرید' if context.user_data['transaction_type'] == 'buy' else 'فروش'}
- مقدار لیر: {amount}
- نرخ تبدیل: {rate} تومان
- مبلغ کل: {total_price} تومان

آیا تأیید می‌کنید؟
"""
        keyboard = [
            [KeyboardButton("✅ تأیید"), KeyboardButton("❌ لغو")],
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(summary, parse_mode='Markdown', reply_markup=reply_markup)
        return TRANSACTION_CONFIRM
    except ValueError as ve:
        await update.message.reply_text(f"⚠️ خطا: {ve}\nلطفاً مقدار معتبر وارد کنید:")
        return TRANSACTION_AMOUNT

async def confirm_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "✅ تأیید":
        # ایجاد تراکنش
        user = get_user_by_telegram_id(update.effective_user.id)
        transaction = create_transaction(
            user_id=user.id,
            transaction_type=context.user_data['transaction_type'],
            amount=context.user_data['amount'],
            total_price=context.user_data['total_price']
        )

        if transaction:
            context.user_data['transaction_id'] = transaction.id

            # ارسال خلاصه تراکنش به ادمین
            summary = f"""
📥 **درخواست تراکنش جدید:**
- کاربر: {user.name} {user.family_name}
- نوع تراکنش: {'خرید' if transaction.transaction_type == 'buy' else 'فروش'}
- مقدار لیر: {transaction.amount}
- نرخ تبدیل: {context.user_data['rate']} تومان
- مبلغ کل: {transaction.total_price} تومان

آیا مایل به انجام این معامله هستید؟
(لطفاً با ارسال 'تأیید {transaction.id}' یا 'رد {transaction.id}' پاسخ دهید.)
"""
            for admin_id in ADMIN_IDS:
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=summary,
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logger.error(f"Error sending message to admin {admin_id}: {e}")

            await update.message.reply_text("درخواست شما ارسال شد. لطفاً منتظر تأیید ادمین باشید.", reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END
        else:
            await update.message.reply_text("⚠️ خطا در ایجاد تراکنش. لطفاً دوباره تلاش کنید.")
            return ConversationHandler.END
    else:
        await update.message.reply_text("❌ تراکنش لغو شد.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

async def get_transaction_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    transaction_id = context.user_data['transaction_id']
    if update.message.text == "لغو":
        # لغو تراکنش توسط کاربر
        update_transaction_status(transaction_id, 'canceled')
        await update.message.reply_text("❌ تراکنش لغو شد.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    if update.message.photo:
        photo = update.message.photo[-1]
        os.makedirs('transaction_proofs', exist_ok=True)
        file_path = f"transaction_proofs/{update.message.from_user.id}_{transaction_id}.jpg"
        await photo.get_file().download(file_path)

        # به‌روزرسانی تراکنش با فیش واریزی
        success = update_transaction(
            transaction_id,
            proof_path=file_path,
            status='waiting_for_admin_confirmation'
        )

        if success:
            # ارسال به ادمین‌ها برای تأیید
            for admin_id in ADMIN_IDS:
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=f"کاربر {update.effective_user.full_name} فیش واریزی خود را ارسال کرد برای تراکنش {transaction_id}. لطفاً بررسی کنید."
                    )
                    # ارسال فیش واریزی
                    await context.bot.send_photo(
                        chat_id=admin_id,
                        photo=open(file_path, 'rb')
                    )
                except Exception as e:
                    logger.error(f"Error sending message to admin {admin_id}: {e}")

            await update.message.reply_text("📥 فیش واریزی دریافت شد و در انتظار تأیید ادمین است.", reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END
        else:
            await update.message.reply_text("⚠️ خطا در ذخیره تراکنش. لطفاً دوباره تلاش کنید.")
            return ConversationHandler.END
    else:
        await update.message.reply_text("⚠️ لطفاً یک عکس ارسال کنید یا 'لغو' را تایپ کنید.")
        return TRANSACTION_PROOF

# پیگیری تراکنش‌ها
async def track_transactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user_by_telegram_id(update.effective_user.id)
    transactions = get_transactions_by_user_id(user.id)
    if transactions:
        message = "📊 **وضعیت تراکنش‌های شما:**\n"
        for tx in transactions:
            message += f"\n- آیدی: {tx.id}\n  نوع: {'خرید' if tx.transaction_type == 'buy' else 'فروش'}\n  مقدار: {tx.amount}\n  مبلغ کل: {tx.total_price} تومان\n  وضعیت: {tx.status}\n  تاریخ: {tx.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        await update.message.reply_text(message, parse_mode='Markdown')
    else:
        await update.message.reply_text("شما هیچ تراکنشی ندارید.")

# اطلاعات حساب
async def account_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user_by_telegram_id(update.effective_user.id)
    if user:
        info = f"""
👤 نام: {user.name} {user.family_name}
🌍 کشور: {user.country}
📞 شماره تلفن: {user.phone}
✅ وضعیت تأیید: {'تأیید شده' if user.is_verified else 'در انتظار تأیید'}
💳 حساب بانکی ایران: {user.iran_bank_info if user.iran_bank_info else 'وارد نشده'}
💳 حساب بانکی ترکیه: {user.turkey_bank_info if user.turkey_bank_info else 'وارد نشده'}
"""
        await update.message.reply_text(info)
    else:
        await update.message.reply_text("❌ اطلاعات حساب شما یافت نشد.")

# راهنما
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
❓ **راهنما**

با استفاده از این ربات می‌توانید لیر ترکیه را خرید و فروش کنید.

**دستورات:**
- 💰 **خرید لیر**: خرید لیر از ما
- 💵 **فروش لیر**: فروش لیر به ما
- 💳 **تنظیم حساب‌های بانکی**: وارد کردن اطلاعات حساب‌های بانکی شما
- 📊 **پیگیری تراکنش‌ها**: مشاهده وضعیت تراکنش‌های شما
- ℹ️ **اطلاعات حساب**: مشاهده اطلاعات حساب کاربری شما
- ❓ **راهنما**: نمایش این راهنما
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')
