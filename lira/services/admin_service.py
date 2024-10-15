# services/admin_service.py

import logging
from sqlalchemy.exc import SQLAlchemyError
from database import SessionLocal
from models import Settings
from utils.helpers import is_admin

logger = logging.getLogger(__name__)

def get_settings():
    session = SessionLocal()
    try:
        settings = session.query(Settings).first()
        if not settings:
            # اگر تنظیمات وجود نداشته باشد، یک ردیف جدید ایجاد کنید
            settings = Settings()
            session.add(settings)
            session.commit()
            session.refresh(settings)
        return settings
    except SQLAlchemyError as e:
        logger.error(f"Error fetching settings: {e}")
        return None
    finally:
        session.close()

def update_buy_rate(new_rate):
    session = SessionLocal()
    try:
        settings = session.query(Settings).first()
        if not settings:
            settings = Settings(buy_rate=new_rate)
            session.add(settings)
        else:
            settings.buy_rate = new_rate
        session.commit()
        logger.info(f"Buy rate updated to: {new_rate}")
        return True
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error updating buy rate: {e}")
        return False
    finally:
        session.close()

def update_sell_rate(new_rate):
    session = SessionLocal()
    try:
        settings = session.query(Settings).first()
        if not settings:
            settings = Settings(sell_rate=new_rate)
            session.add(settings)
        else:
            settings.sell_rate = new_rate
        session.commit()
        logger.info(f"Sell rate updated to: {new_rate}")
        return True
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error updating sell rate: {e}")
        return False
    finally:
        session.close()

def toggle_buy_enabled():
    session = SessionLocal()
    try:
        settings = session.query(Settings).first()
        if not settings:
            settings = Settings(buy_enabled=True)
            session.add(settings)
        else:
            settings.buy_enabled = not settings.buy_enabled
        session.commit()
        status = "enabled" if settings.buy_enabled else "disabled"
        logger.info(f"Buy enabled status toggled to: {status}")
        return settings.buy_enabled
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error toggling buy enabled: {e}")
        return None
    finally:
        session.close()

def toggle_sell_enabled():
    session = SessionLocal()
    try:
        settings = session.query(Settings).first()
        if not settings:
            settings = Settings(sell_enabled=True)
            session.add(settings)
        else:
            settings.sell_enabled = not settings.sell_enabled
        session.commit()
        status = "enabled" if settings.sell_enabled else "disabled"
        logger.info(f"Sell enabled status toggled to: {status}")
        return settings.sell_enabled
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error toggling sell enabled: {e}")
        return None
    finally:
        session.close()

def update_admin_bank_info(country, bank_info):
    session = SessionLocal()
    try:
        settings = session.query(Settings).first()
        if not settings:
            settings = Settings()
            session.add(settings)
        if country == 'Iran':
            settings.admin_iran_bank_account = bank_info
            logger.info("Admin Iran bank account updated.")
        elif country == 'Turkey':
            settings.admin_turkey_bank_account = bank_info
            logger.info("Admin Turkey bank account updated.")
        else:
            logger.warning(f"Unknown country for bank info update: {country}")
            return False
        session.commit()
        return True
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error updating admin bank info: {e}")
        return False
    finally:
        session.close()
