# models.py

from sqlalchemy import Column, Integer, String, Boolean, Float, Text
from sqlalchemy.ext.declarative import declarative_base
import json

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

class BankAccount(Base):
    __tablename__ = 'bank_accounts'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)  # کلید خارجی به User.id
    bank_country = Column(String, nullable=False)
    bank_name = Column(String, nullable=False)
    account_number = Column(String, nullable=False)

class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)  # کلید خارجی به User.id
    transaction_type = Column(String, nullable=False)  # 'buy' یا 'sell'
    amount = Column(Float, nullable=False)  # مقدار لیر
    total_price = Column(Float, nullable=False)  # مبلغ کل به تومان
    status = Column(String, default='pending')  # 'pending', 'approved', 'rejected'

class Settings(Base):
    __tablename__ = 'settings'

    id = Column(Integer, primary_key=True, index=True)
    buy_rate = Column(Float, nullable=False)
    sell_rate = Column(Float, nullable=False)
    buy_enabled = Column(Boolean, default=True)
    sell_enabled = Column(Boolean, default=True)
    admin_bank_info = Column(String, nullable=True)
    admin_ids = Column(Text, nullable=False)  # تغییر نوع داده به Text
