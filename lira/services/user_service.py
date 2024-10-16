# services/user_service.py

import logging
from sqlalchemy.exc import SQLAlchemyError
from database import SessionLocal
from models import User, Settings

logger = logging.getLogger(__name__)

def register_user(telegram_id, name, family_name, country, phone, id_card_path):
    session = SessionLocal()
    try:
        user = User(
            telegram_id=telegram_id,
            name=name,
            family_name=family_name,
            country=country,
            phone=phone,
            is_verified=False,
            id_card_path=id_card_path
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        logger.info(f"User registered: {user}")
        return user
    except SQLAlchemyError as e:
        logger.error(f"Database error while registering user: {e}")
        session.rollback()
        return None
    except Exception as e:
        logger.error(f"Unexpected error while registering user: {e}")
        session.rollback()
        return None
    finally:
        session.close()

def get_user_by_telegram_id(telegram_id):
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        return user
    except SQLAlchemyError as e:
        logger.error(f"Error fetching user by telegram_id: {e}")
        return None
    finally:
        session.close()

def get_user_by_id(user_id):
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        return user
    except SQLAlchemyError as e:
        logger.error(f"Error fetching user by id: {e}")
        return None
    finally:
        session.close()

def verify_user(user_id):
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if user:
            user.is_verified = True
            session.commit()
            logger.info(f"User verified: {user}")
            return True
        else:
            logger.warning(f"User with id {user_id} not found for verification.")
            return False
    except SQLAlchemyError as e:
        logger.error(f"Error verifying user: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def reject_user(user_id):
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if user:
            session.delete(user)
            session.commit()
            logger.info(f"User rejected and deleted: {user}")
            return True
        else:
            logger.warning(f"User with id {user_id} not found for rejection.")
            return False
    except SQLAlchemyError as e:
        logger.error(f"Error rejecting user: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def get_settings():
    session = SessionLocal()
    try:
        settings = session.query(Settings).first()
        if settings is None:
            # اگر تنظیمات وجود نداشته باشد، تنظیمات پیش‌فرض را ایجاد کنید
            settings = Settings(
                buy_rate=0.0,
                sell_rate=0.0,
                buy_enabled=True,
                sell_enabled=True,
                admin_bank_info=""
            )
            session.add(settings)
            session.commit()
            session.refresh(settings)
            logger.info("Default settings created.")
        return settings
    except SQLAlchemyError as e:
        logger.error(f"Error fetching settings: {e}")
        return None
    finally:
        session.close()

def update_settings(buy_rate=None, sell_rate=None, buy_enabled=None, sell_enabled=None, admin_bank_info=None):
    session = SessionLocal()
    try:
        settings = session.query(Settings).first()
        if settings:
            if buy_rate is not None:
                settings.buy_rate = buy_rate
            if sell_rate is not None:
                settings.sell_rate = sell_rate
            if buy_enabled is not None:
                settings.buy_enabled = buy_enabled
            if sell_enabled is not None:
                settings.sell_enabled = sell_enabled
            if admin_bank_info is not None:
                settings.admin_bank_info = admin_bank_info
            session.commit()
            logger.info(f"Settings updated: {settings}")
            return True
        else:
            logger.warning("Settings not found to update.")
            return False
    except SQLAlchemyError as e:
        logger.error(f"Error updating settings: {e}")
        session.rollback()
        return False
    finally:
        session.close()
