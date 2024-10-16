# models.py

from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    family_name = Column(String, nullable=False)
    country = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False)
    id_card_path = Column(String, nullable=True)
    iran_bank_info = Column(String, nullable=True)
    turkey_bank_info = Column(String, nullable=True)

class Settings(Base):
    __tablename__ = 'settings'

    id = Column(Integer, primary_key=True, index=True)
    buy_rate = Column(Float, nullable=False, default=0.0)  # نرخ خرید از کاربر
    sell_rate = Column(Float, nullable=False, default=0.0)  # نرخ فروش به کاربر
    buy_enabled = Column(Boolean, default=True)
    sell_enabled = Column(Boolean, default=True)
    admin_iran_bank_info = Column(String, nullable=True)
    admin_turkey_bank_info = Column(String, nullable=True)

class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    transaction_type = Column(String, nullable=False)  # 'buy' یا 'sell'
    amount = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    status = Column(String, default='pending')  # وضعیت تراکنش
    created_at = Column(DateTime, default=datetime.utcnow)
    proof_path = Column(String, nullable=True)  # فیش واریزی کاربر
    admin_proof_path = Column(String, nullable=True)  # فیش واریزی ادمین
