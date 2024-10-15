# handlers/transaction_handlers.py

import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)
from services.transaction_service import (
    create_transaction,
    get_transaction_by_id,
    update_transaction_status,
    get_user_transactions
)
from services.user_service import get_user_by_telegram_id
from services.admin_service import get_settings
from utils.helpers import is_admin
from keyboards.user_keyboards import main_menu_keyboard

logger = logging.getLogger(__name__)

# تعریف حالات ConversationHandler مربوط به تراکنش‌ها
(
    SELECT_TRANSACTION_TYPE, TRANSACTION_AMOUNT_TYPE, AMOUNT, CONFIRM_TRANSACTION,
    SEND_PAYMENT_PROOF
) = range(5)

# هندلر انتخاب نوع وارد کردن مقدار
async def transaction_amount_type_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == 'amount_toman':
        context.user_data['amount_type'] = 'toman'
        await query.edit_message_text("🔢 لطفاً مقدار تومان را وارد کنید:")
    elif data == 'amount_lira':
        context.user_data['amount_type'] = 'lira'
        await query.edit_message_text("🔢 لطفاً مقدار لیر را وارد کنید:")
    else:
        await query.edit_message_text("⚠️ گزینه نامعتبری انتخاب شده است.")
        return ConversationHandler.END
    return AMOUNT

# دریافت مقدار تراکنش
async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    amount_text = update.message.text.strip()
    try:
        amount = float(amount_text)
        if amount <= 0:
            raise ValueError("مقدار باید بزرگ‌تر از صفر باشد.")
        if amount > 100000:  # مثال: حداکثر مقدار تراکنش
            await update.message.reply_text("⚠️ مقدار وارد شده بیش از حد مجاز است. لطفاً مقدار کمتری وارد کنید:")
            return AMOUNT
        if amount < 10:  # مثال: حداقل مقدار تراکنش
            await update.message.reply_text("⚠️ مقدار وارد شده کمتر از حد مجاز است. لطفاً مقدار بیشتری وارد کنید:")
            return AMOUNT
        context.user_data['amount'] = amount

        # ارسال پیام تأیید نهایی به کاربر
        transaction_type = context.user_data['transaction_type']
        amount_type = context.user_data['amount_type']
        settings = get_settings()
        user = get_user_by_telegram_id(update.effective_user.id)

        if transaction_type == 'buy':
            rate = settings.buy_rate
            if amount_type == 'toman':
                lira_amount = amount / rate
                total_price = amount
                summary = (
                    f"💰 **خرید لیر**\n"
                    f"🔢 مقدار: {lira_amount:.2f} لیر\n"
                    f"💵 نرخ خرید: {rate} تومان به ازای هر لیر\n"
                    f"💸 مبلغ کل: {total_price:.2f} تومان\n\n"
                    f"آیا از انجام این تراکنش مطمئن هستید؟"
                )
            else:
                lira_amount = amount
                total_price = amount * rate
                summary = (
                    f"💰 **خرید لیر**\n"
                    f"🔢 مقدار: {lira_amount} لیر\n"
                    f"💵 نرخ خرید: {rate} تومان به ازای هر لیر\n"
                    f"💸 مبلغ کل: {total_price:.2f} تومان\n\n"
                    f"آیا از انجام این تراکنش مطمئن هستید؟"
                )
        else:
            rate = settings.sell_rate
            if amount_type == 'toman':
                lira_amount = amount / rate
                total_price = amount
                summary = (
                    f"💸 **فروش لیر**\n"
                    f"🔢 مقدار: {lira_amount:.2f} لیر\n"
                    f"💵 نرخ فروش: {rate} تومان به ازای هر لیر\n"
                    f"💰 مبلغ کل: {total_price:.2f} تومان\n\n"
                    f"آیا از انجام این تراکنش مطمئن هستید؟"
                )
            else:
                lira_amount = amount
                total_price = amount * rate
                summary = (
                    f"💸 **فروش لیر**\n"
                    f"🔢 مقدار: {lira_amount} لیر\n"
                    f"💵 نرخ فروش: {rate} تومان به ازای هر لیر\n"
                    f"💰 مبلغ کل: {total_price:.2f} تومان\n\n"
                    f"آیا از انجام این تراکنش مطمئن هستید؟"
                )

        keyboard = [
            [InlineKeyboardButton("✅ تایید", callback_data='confirm_transaction')],
            [InlineKeyboardButton("❌ لغو", callback_data='cancel_transaction')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            summary,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        return CONFIRM_TRANSACTION
    except ValueError as ve:
        await update.message.reply_text(f"⚠️ خطا: {ve}. لطفاً یک مقدار معتبر وارد کنید.")
        return AMOUNT
    except Exception as e:
        logger.error(f"❌ خطا در handle_amount: {e}")
        await update.message.reply_text("⚠️ خطایی رخ داده است. لطفاً دوباره تلاش کنید.")
        return AMOUNT

# تایید نهایی تراکنش توسط کاربر
async def confirm_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'confirm_transaction':
        transaction_type = context.user_data['transaction_type']
        amount = context.user_data['amount']
        amount_type = context.user_data['amount_type']  # 'toman' یا 'lira'
        settings = get_settings()
        user = get_user_by_telegram_id(query.from_user.id)

        if not user:
            await query.edit_message_text("❌ شما هنوز ثبت‌نام نکرده‌اید.")
            return ConversationHandler.END

        # محاسبه مبلغ بر اساس نوع وارد کردن
        if amount_type == 'toman':
            if transaction_type == 'buy':
                # کاربر مبلغ تومانی را وارد کرده و می‌خواهد لیر بخرد
                rate = settings.buy_rate  # نرخ خرید
                lira_amount = amount / rate
                total_price = amount  # مبلغ تومان
            else:
                # کاربر مبلغ تومانی را وارد کرده و می‌خواهد لیر بفروشد
                rate = settings.sell_rate  # نرخ فروش
                lira_amount = amount / rate
                total_price = amount  # مبلغ تومان
        else:
            if transaction_type == 'buy':
                # کاربر مبلغ لیری را وارد کرده و می‌خواهد لیر بخرد
                rate = settings.buy_rate
                lira_amount = amount
                total_price = amount * rate  # مبلغ تومان
            else:
                # کاربر مبلغ لیری را وارد کرده و می‌خواهد لیر بفروشد
                rate = settings.sell_rate
                lira_amount = amount
                total_price = amount * rate  # مبلغ تومان

        # ایجاد تراکنش
        transaction = create_transaction(
            user_id=user.id,
            transaction_type=transaction_type,
            amount=lira_amount,
            total_price=total_price
        )
        if not transaction:
            await query.edit_message_text("⚠️ خطا در ثبت تراکنش. لطفاً دوباره تلاش کنید.")
            return ConversationHandler.END

        # ارسال اطلاعات بانکی ادمین به مشتری
        if transaction_type == 'buy':
            # ارسال شماره ایبان ترکیه و نام صاحب حساب بانکی ترکیه ادمین
            admin_bank_info = settings.admin_turkey_bank_account or "🔸 شماره ایبان ترکیه: TRXXXXXXXXXXXXXX\n🔸 نام صاحب حساب: ادمین"
            payment_instruction = (
                f"📥 **دستورالعمل پرداخت:**\n\n"
                f"لطفاً مبلغ **{total_price:.2f} تومان** را به شماره ایبان زیر واریز کنید:\n\n"
                f"{admin_bank_info}\n\n"
                f"📸 پس از واریز، لطفاً فیش پرداخت خود را ارسال کنید."
            )
        else:
            # ارسال شماره شبا، شماره کارت و صاحب حساب بانکی ایران ادمین
            admin_bank_info = settings.admin_iran_bank_account or "🔸 شماره شبا ایران: IRXXXXXXXXXXXXXX\n🔸 شماره کارت: XXXXXXXXXXXXXXXX\n🔸 نام صاحب حساب: ادمین"
            payment_instruction = (
                f"📥 **دستورالعمل پرداخت:**\n\n"
                f"لطفاً مبلغ **{total_price:.2f} تومان** را به شماره شبا زیر واریز کنید:\n\n"
                f"{admin_bank_info}\n\n"
                f"📸 پس از واریز، لطفاً فیش پرداخت خود را ارسال کنید."
            )

        await query.edit_message_text(
            payment_instruction,
            parse_mode='Markdown'
        )

        # ارسال پیام به ادمین‌ها برای بررسی فیش پرداخت
        for admin_id in settings.admin_ids:
            transaction_details = (
                f"🔔 **تراکنش جدید:**\n\n"
                f"👤 **کاربر:** {user.name} {user.family_name} (ID: {user.id})\n"
                f"🌍 **کشور:** {'ایران' if user.country == 'Iran' else 'ترکیه'}\n"
                f"📞 **شماره تلفن:** {user.phone}\n\n"
                f"💱 **نوع تراکنش:** {'خرید' if transaction_type == 'buy' else 'فروش'} لیر\n"
                f"🔢 **مقدار:** {transaction.amount} لیر\n"
                f"💰 **مبلغ کل:** {transaction.total_price:.2f} تومان\n"
                f"🔄 **وضعیت:** {transaction.status.capitalize()}.\n\n"
                f"📥 **دستورالعمل پرداخت:**\n{payment_instruction}"
            )
            keyboard = [
                [InlineKeyboardButton("📸 ارسال فیش پرداخت", callback_data=f'send_payment_proof_{transaction.id}')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(
                chat_id=admin_id,
                text=transaction_details,
                reply_markup=reply_markup
            )
        return ConversationHandler.END

# ارسال فیش پرداخت توسط کاربر
async def send_payment_proof_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    settings = get_settings()
    if data.startswith('send_payment_proof_'):
        transaction_id = int(data.split('_')[-1])
        # درخواست فیش پرداخت از کاربر
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="📸 لطفاً فیش پرداخت خود را ارسال کنید."
        )
        # ذخیره تراکنش در context برای مرحله بعد
        context.user_data['current_transaction_id'] = transaction_id
        return SEND_PAYMENT_PROOF
    else:
        await query.edit_message_text("⚠️ گزینه نامعتبری انتخاب شده است.")
    return ConversationHandler.END

# دریافت فیش پرداخت
async def receive_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    transaction_id = context.user_data.get('current_transaction_id')
    transaction = get_transaction_by_id(transaction_id)
    if not transaction or transaction.user_id != user_id:
        await update.message.reply_text("⚠️ تراکنش یافت نشد.")
        return ConversationHandler.END

    if not update.message.photo:
        await update.message.reply_text("⚠️ لطفاً یک تصویر فیش پرداخت ارسال کنید.")
        return SEND_PAYMENT_PROOF

    photo = update.message.photo[-1]
    file_size = photo.file_size
    if file_size > 5 * 1024 * 1024:
        await update.message.reply_text("⚠️ اندازه فایل بیش از حد مجاز است (حداکثر 5 مگابایت). لطفاً فیش کوچکتری ارسال کنید.")
        return SEND_PAYMENT_PROOF

    # دانلود فیش پرداخت
    photo_file = await photo.get_file()
    if not os.path.exists('payment_proofs'):
        os.makedirs('payment_proofs')
    photo_path = f"payment_proofs/{transaction_id}_payment.jpg"
    await photo_file.download_to_drive(custom_path=photo_path)
    update_transaction_status(transaction_id, 'payment_received')

    # به‌روزرسانی تراکنش با مسیر فیش پرداخت
    session = SessionLocal()
    try:
        transaction = session.query(Transaction).filter_by(id=transaction_id).first()
        if transaction:
            transaction.payment_proof = photo_path
            transaction.status = 'payment_received'
            session.commit()
    except Exception as e:
        logger.error(f"❌ خطا در به‌روزرسانی تراکنش: {e}")
        session.rollback()
    finally:
        session.close()

    await update.message.reply_text("✅ فیش پرداخت شما دریافت شد و در انتظار بررسی ادمین است.")

    # اطلاع رسانی به ادمین‌ها
    user = get_user_by_telegram_id(transaction.user_id)
    settings = get_settings()
    for admin_id in settings.admin_ids:
        transaction_details = (
            f"🔔 **فیش پرداخت برای تراکنش {transaction.id} ارسال شده است.**\n\n"
            f"👤 **کاربر:** {user.name} {user.family_name} (ID: {user.id})\n"
            f"💱 **نوع تراکنش:** {'خرید' if transaction.transaction_type == 'buy' else 'فروش'} لیر\n"
            f"🔢 **مقدار:** {transaction.amount} لیر\n"
            f"💰 **مبلغ کل:** {transaction.total_price:.2f} تومان\n"
            f"🔄 **وضعیت:** {transaction.status.capitalize()}.\n\n"
            f"📸 **فیش پرداخت کاربر:**"
        )
        keyboard = [
            [InlineKeyboardButton("✅ تایید پرداخت", callback_data=f'approve_payment_{transaction.id}'),
             InlineKeyboardButton("❌ رد پرداخت", callback_data=f'reject_payment_{transaction.id}')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=admin_id,
            text=transaction_details,
            reply_markup=reply_markup
        )
        with open(photo_path, 'rb') as photo_file_obj:
            await context.bot.send_photo(chat_id=admin_id, photo=photo_file_obj)
    return ConversationHandler.END
