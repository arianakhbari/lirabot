# main.py

import asyncio
import logging
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)
from config import BOT_TOKEN
from handlers.user_handlers import (
    start,
    get_name,
    get_family_name,
    get_country,
    get_phone,
    get_id_card,
    main_menu,
    buy_lira,
    sell_lira,
    account_info,
    help_command,
    set_bank_info,
    get_iran_bank_info,
    get_turkey_bank_info,
    get_transaction_amount,
    confirm_transaction,
    get_transaction_proof,
    track_transactions,
)
from handlers.admin_handlers import setup_admin_handlers

# تنظیمات لاگینگ
logging.basicConfig(
    filename='bot.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# تعریف مراحل ConversationHandler
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

async def error_handler(update: object, context: telegram.ext.ContextTypes.DEFAULT_TYPE) -> None:
    """لاگ کردن خطاها و ارسال پیام به کاربر."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

    # ارسال پیام به کاربر
    if isinstance(update, telegram.Update) and update.effective_user:
        try:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text="⚠️ مشکلی در پردازش درخواست شما به وجود آمد. لطفاً دوباره تلاش کنید."
            )
        except Exception as e:
            logger.error(f"Failed to send error message to user: {e}")

async def main():
    # ساخت Application
    application = Application.builder().token(BOT_TOKEN).build()

    # حذف Webhook (اگر قبلاً تنظیم شده باشد)
    await application.bot.delete_webhook(drop_pending_updates=True)

    # تعریف ConversationHandler برای ثبت نام کاربر
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            FAMILY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_family_name)],
            COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_country)],
            PHONE: [MessageHandler((filters.TEXT | filters.CONTACT) & ~filters.COMMAND, get_phone)],
            ID_CARD: [MessageHandler(filters.PHOTO & ~filters.COMMAND, get_id_card)],
        },
        fallbacks=[],
    )

    # تعریف ConversationHandler برای تنظیم حساب‌های بانکی
    bank_info_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^💳 تنظیم حساب‌های بانکی$'), set_bank_info)],
        states={
            IRAN_BANK_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_iran_bank_info)],
            TURKEY_BANK_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_turkey_bank_info)],
        },
        fallbacks=[],
    )

    # تعریف ConversationHandler برای خرید و فروش
    transaction_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex('^💰 خرید لیر$'), buy_lira),
            MessageHandler(filters.Regex('^💵 فروش لیر$'), sell_lira),
        ],
        states={
            TRANSACTION_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_transaction_amount)],
            TRANSACTION_CONFIRM: [MessageHandler(filters.Regex('^(✅ تأیید|❌ لغو)$'), confirm_transaction)],
            TRANSACTION_PROOF: [MessageHandler((filters.PHOTO | filters.TEXT) & ~filters.COMMAND, get_transaction_proof)],
        },
        fallbacks=[],
    )

    # اضافه کردن هندلرها به application
    application.add_handler(conv_handler)
    application.add_handler(bank_info_handler)
    application.add_handler(transaction_handler)

    # هندلرهای منوی اصلی
    application.add_handler(CommandHandler('menu', main_menu))
    application.add_handler(MessageHandler(filters.Regex('^📊 پیگیری تراکنش‌ها$'), track_transactions))
    application.add_handler(MessageHandler(filters.Regex('^ℹ️ اطلاعات حساب$'), account_info))
    application.add_handler(MessageHandler(filters.Regex('^❓ راهنما$'), help_command))

    # تنظیم هندلرهای ادمین
    setup_admin_handlers(application)

    # اضافه کردن هندلر خطا
    application.add_error_handler(error_handler)

    # اجرای ربات با Polling
    await application.run_polling()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
