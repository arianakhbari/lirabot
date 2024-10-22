# handlers/admin_handlers.py

import logging
from enum import Enum

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes, Application

from models import Transaction, User
from utils.helpers import is_admin
from config import ADMIN_IDS

logger = logging.getLogger(__name__)

# تعریف Enum برای وضعیت تراکنش‌ها
class TransactionStatus(Enum):
    AWAITING_PAYMENT = 'awaiting_payment'
    PAYMENT_RECEIVED = 'payment_received'
    CONFIRMED = 'confirmed'
    CANCELED = 'canceled'

async def approve_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    تایید پرداخت تراکنش توسط ادمین.
    """
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.edit_message_text("⚠️ شما دسترسی لازم را ندارید.")
        return

    data = query.data
    if not data.startswith('approve_payment_'):
        await query.edit_message_text("⚠️ درخواست نامعتبری دریافت شد.")
        return

    try:
        transaction_id = int(data.split('_')[-1])
    except ValueError:
        await query.edit_message_text("⚠️ شناسه تراکنش نامعتبر است.")
        return

    db = context.bot_data.get('db')
    if not db:
        logger.error("Database session not found in bot_data.")
        await query.edit_message_text("⚠️ خطا در اتصال به پایگاه داده.")
        return

    transaction = db.query(Transaction).filter_by(id=transaction_id).first()

    if not transaction or transaction.status != TransactionStatus.PAYMENT_RECEIVED.value:
        await query.edit_message_text("⚠️ تراکنش معتبر نیست یا در وضعیت مناسبی قرار ندارد.")
        return

    transaction.status = TransactionStatus.CONFIRMED.value
    db.commit()

    user = db.query(User).filter_by(id=transaction.user_id).first()
    if user:
        try:
            await context.bot.send_message(
                chat_id=user.telegram_id,
                text=(
                    f"✅ تراکنش شما با موفقیت تایید شد.\n"
                    f"💱 نوع تراکنش: {'خرید' if transaction.transaction_type == 'buy' else 'فروش'} لیر\n"
                    f"💰 مبلغ کل: {transaction.total_price:.2f} تومان"
                )
            )
        except Exception as e:
            logger.error(f"Failed to send confirmation message to user {user.telegram_id}: {e}")

    await query.edit_message_text(f"✅ تراکنش {transaction.id} تایید شد.")

async def reject_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    رد پرداخت تراکنش توسط ادمین.
    """
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.edit_message_text("⚠️ شما دسترسی لازم را ندارید.")
        return

    data = query.data
    if not data.startswith('reject_payment_'):
        await query.edit_message_text("⚠️ درخواست نامعتبری دریافت شد.")
        return

    try:
        transaction_id = int(data.split('_')[-1])
    except ValueError:
        await query.edit_message_text("⚠️ شناسه تراکنش نامعتبر است.")
        return

    db = context.bot_data.get('db')
    if not db:
        logger.error("Database session not found in bot_data.")
        await query.edit_message_text("⚠️ خطا در اتصال به پایگاه داده.")
        return

    transaction = db.query(Transaction).filter_by(id=transaction_id).first()

    if not transaction or transaction.status != TransactionStatus.PAYMENT_RECEIVED.value:
        await query.edit_message_text("⚠️ تراکنش معتبر نیست یا در وضعیت مناسبی قرار ندارد.")
        return

    transaction.status = TransactionStatus.CANCELED.value
    db.commit()

    user = db.query(User).filter_by(id=transaction.user_id).first()
    if user:
        try:
            await context.bot.send_message(
                chat_id=user.telegram_id,
                text=(
                    f"⛔️ تراکنش شما رد شد.\n"
                    f"💱 نوع تراکنش: {'خرید' if transaction.transaction_type == 'buy' else 'فروش'} لیر\n"
                    f"💰 مبلغ کل: {transaction.total_price:.2f} تومان\n"
                    f"⚠️ دلیل رد تراکنش: [در صورت وجود] "
                )
            )
        except Exception as e:
            logger.error(f"Failed to send rejection message to user {user.telegram_id}: {e}")

    await query.edit_message_text(f"⛔️ تراکنش {transaction.id} رد شد.")

def setup_admin_handlers(application: Application):
    """
    اضافه کردن هندلرهای ادمین به application.
    """
    application.add_handler(
        CallbackQueryHandler(approve_payment, pattern=r'^approve_payment_\d+$')
    )
    application.add_handler(
        CallbackQueryHandler(reject_payment, pattern=r'^reject_payment_\d+$')
    )
