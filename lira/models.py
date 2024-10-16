# models.py

from sqlalchemy import Column, Integer, String, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base

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

class Settings(Base):
    __tablename__ = 'settings'

    id = Column(Integer, primary_key=True, index=True)
    buy_rate = Column(Float, nullable=False)
    sell_rate = Column(Float, nullable=False)
    buy_enabled = Column(Boolean, default=True)
    sell_enabled = Column(Boolean, default=True)
    admin_bank_info = Column(String, nullable=True)
