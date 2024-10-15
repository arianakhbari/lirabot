# utils/helpers.py

from config import ADMIN_IDS
from services.user_service import get_user_by_telegram_id

def is_admin(user_id):
    return user_id in ADMIN_IDS

def get_user_by_id(user_id):
    # فرض بر این است که user_id همان telegram_id است
    return get_user_by_telegram_id(user_id)
