# utils/helpers.py

from config import ADMIN_IDS

def is_admin(user_id):
    return user_id in ADMIN_IDS
