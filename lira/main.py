# main.py

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
) = range(5)

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # حذف Webhook (اگر قبلاً تنظیم شده باشد)
    application.bot.delete_webhook(drop_pending_updates=True)

    # تعریف ConversationHandler برای ثبت نام کاربر
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            FAMILY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_family_name)],
            COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_country)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            ID_CARD: [MessageHandler(filters.PHOTO & ~filters.COMMAND, get_id_card)],
        },
        fallbacks=[],
    )

    # اضافه کردن هندلرها به application
    application.add_handler(conv_handler)

    # تنظیم هندلرهای ادمین
    setup_admin_handlers(application)

    # شروع Polling
    application.run_polling()

if __name__ == '__main__':
    main()
