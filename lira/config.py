# config.py

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS").split(',')))  # فرض بر این است که ادمین‌ها با کاما جدا شده‌اند
DATABASE_URL = os.getenv("DATABASE_URL")
