# database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from models import Base

# ایجاد engine
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})  # اگر از SQLite استفاده می‌کنید

# ایجاد کلاس Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ایجاد جداول در پایگاه داده
Base.metadata.create_all(bind=engine)
