# keyboards/user_keyboards.py

from telegram import KeyboardButton, ReplyKeyboardMarkup

def main_menu_keyboard(is_admin=False):
    keyboard = [
        ["💱 لیر"],
        ["🏦 مدیریت حساب‌های بانکی"],
        ["📜 تاریخچه تراکنش‌ها"],
        ["📞 پشتیبانی"]
    ]
    if is_admin:
        keyboard.append(["⚙️ پنل مدیریت"])
    return keyboard
