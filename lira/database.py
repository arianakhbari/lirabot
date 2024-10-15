# database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from config import DATABASE_URL

# ایجاد اتصال به پایگاه داده
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})

# ایجاد SessionLocal برای مدیریت جلسات
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# پایه‌ی مدل‌ها
Base = declarative_base()
