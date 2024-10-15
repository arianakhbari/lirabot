# main.py

import logging
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)
from config import BOT_TOKEN, ADMIN_IDS, DATABASE_URL
from database import engine, Base
from models import User, BankAccount, Transaction, Settings
from handlers.user_handlers import (
    start, get_name, get_family_name, get_country, get_phone, get_id_card,
    cancel, main_menu
)
from handlers.admin_handlers import (
    admin_panel, set_buy_rate, save_buy_rate, set_sell_rate, save_sell_rate,
    toggle_buy, toggle_sell, set_admin_bank_info, approve_transaction
)
from handlers.transaction_handlers import (
    transaction_amount_type_handler, handle_amount, confirm_transaction,
    send_payment_proof_handler, receive_payment_proof
)
from handlers.error_handler import error_handler

# تنظیمات لاگینگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ایجاد جداول در دیتابیس
Base.metadata.create_all(engine)

def main():
    # ایجاد application
    application = Application.builder().token(BOT_TOKEN).build()

    # حذف وبهوک (در صورت استفاده از polling)
    application.bot.delete_webhook(drop_pending_updates=True)

    # تعریف ConversationHandler برای کاربران
    user_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            0: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_family_name)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_country)],
            3: [MessageHandler(filters.CONTACT, get_phone)],
            4: [MessageHandler(filters.PHOTO & ~filters.COMMAND, get_id_card)],
            # اضافه کردن مراحل مربوط به تراکنش‌ها در صورت نیاز
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_user=True,
    )

    # تعریف ConversationHandler برای ادمین‌ها
    admin_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('admin', admin_panel)],
        states={
            100: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_buy_rate)],
            101: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_sell_rate)],
            # اضافه کردن مراحل مربوط به تنظیمات بانکی در صورت نیاز
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_user=True,
    )

    # اضافه کردن ConversationHandlerها به application
    application.add_handler(user_conv_handler)
    application.add_handler(admin_conv_handler)

    # اضافه کردن CallbackQueryHandler برای تایید یا رد کاربران
    application.add_handler(CallbackQueryHandler(approve_transaction, pattern='^(approve|reject)_user_\d+$'))

    # اضافه کردن CallbackQueryHandler برای مدیریت تراکنش‌ها
    # می‌توانید این قسمت را بسته به نیاز پروژه اضافه کنید

    # اضافه کردن هندلر خطا به اپلیکیشن
    application.add_error_handler(error_handler)

    # شروع polling
    application.run_polling()

if __name__ == '__main__':
    main()
