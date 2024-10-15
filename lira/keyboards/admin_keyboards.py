# keyboards/admin_keyboards.py

from telegram import KeyboardButton, ReplyKeyboardMarkup

def admin_panel_keyboard():
    keyboard = [
        ["👥 مدیریت کاربران"],
        ["📈 تنظیم نرخ‌ها"],
        ["🔄 مدیریت خرید و فروش"],
        ["📋 تنظیم اطلاعات بانکی ادمین"],
        ["↩️ بازگشت به منوی اصلی"]
    ]
    return keyboard
