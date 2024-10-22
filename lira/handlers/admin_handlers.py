# handlers/admin_handlers.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes
from models import Transaction, User
from utils.helpers import is_admin
from config import ADMIN_IDS

async def approve_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.edit_message_text("⚠️ شما دسترسی لازم را ندارید.")
        return

    data = query.data
    if not data.startswith('approve_payment_'):
        await query.edit_message_text("⚠️ درخواست نامعتبری دریافت شد.")
        return

    transaction_id = int(data.split('_')[-1])
    db = context.bot_data['db']
    transaction = db.query(Transaction).filter_by(id=transaction_id).first()

    if not transaction or transaction.status != 'payment_received':
        await query.edit_message_text("⚠️ تراکنش معتبر نیست یا در وضعیت مناسبی قرار ندارد.")
        return

    transaction.status = 'confirmed'
    db.commit()

    user = db.query(User).filter_by(id=transaction.user_id).first()
    if user:
        await context.bot.send_message(
            chat_id=user.telegram_id,
            text=f"✅ تراکنش شما با موفقیت تایید شد.\n💱 نوع تراکنش: {'خرید' if transaction.transaction_type == 'buy' else 'فروش'} لیر\n💰 مبلغ کل: {transaction.total_price:.2f} تومان"
        )

    await query.edit_message_text(f"✅ تراکنش {transaction.id} تایید شد.")

async def reject_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.edit_message_text("⚠️ شما دسترسی لازم را ندارید.")
        return

    data = query.data
    if not data.startswith('reject_payment_'):
        await query.edit_message_text("⚠️ درخواست نامعتبری دریافت شد.")
        return

    transaction_id = int(data.split('_')[-1])
    db = context.bot_data['db']
    transaction = db.query(Transaction).filter_by(id=transaction_id).first()

    if not transaction or transaction.status != 'payment_received':
        await query.edit_message_text("⚠️ تراکنش معتبر نیست یا در وضعیت مناسبی قرار ندارد.")
        return

    transaction.status = 'canceled'
    db.commit()

    user = db.query(User).filter_by(id=transaction.user_id).first()
    if user:
        await context.bot.send_message(
            chat_id=user.telegram_id,
            text=f"⛔️ تراکنش شما رد شد.\n💱 نوع تراکنش: {'خرید' if transaction.transaction_type == 'buy' else 'فروش'} لیر\n💰 مبلغ کل: {transaction.total_price:.2f} تومان\n⚠️ دلیل رد تراکنش: [در صورت وجود] "
        )

    await query.edit_message_text(f"⛔️ تراکنش {transaction.id} رد شد.")

def setup_admin_handlers(application: Application):
    application.add_handler(CallbackQueryHandler(approve_payment, pattern=r'^approve_payment_\d+$'))
    application.add_handler(CallbackQueryHandler(reject_payment, pattern=r'^reject_payment_\d+$'))
