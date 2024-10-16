# services/user_service.py

import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from database import SessionLocal
from models import User, Settings, Transaction

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

def update_user_bank_info(telegram_id, iran_bank_info=None, turkey_bank_info=None):
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if user:
            if iran_bank_info is not None:
                user.iran_bank_info = iran_bank_info
            if turkey_bank_info is not None:
                user.turkey_bank_info = turkey_bank_info
            session.commit()
            logger.info(f"User bank info updated: {user}")
            return True
        else:
            logger.warning(f"User with telegram_id {telegram_id} not found.")
            return False
    except SQLAlchemyError as e:
        logger.error(f"Error updating user bank info: {e}")
        session.rollback()
        return False
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
            # ایجاد تنظیمات پیش‌فرض
            settings = Settings()
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

def update_settings(buy_rate=None, sell_rate=None, buy_enabled=None, sell_enabled=None, admin_iran_bank_info=None, admin_turkey_bank_info=None):
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
            if admin_iran_bank_info is not None:
                settings.admin_iran_bank_info = admin_iran_bank_info
            if admin_turkey_bank_info is not None:
                settings.admin_turkey_bank_info = admin_turkey_bank_info
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

def create_transaction(user_id, transaction_type, amount, total_price):
    session = SessionLocal()
    try:
        transaction = Transaction(
            user_id=user_id,
            transaction_type=transaction_type,
            amount=amount,
            total_price=total_price,
            status='pending'
        )
        session.add(transaction)
        session.commit()
        session.refresh(transaction)
        logger.info(f"Transaction created: {transaction}")
        return transaction
    except SQLAlchemyError as e:
        logger.error(f"Error creating transaction: {e}")
        session.rollback()
        return None
    finally:
        session.close()

def get_transaction_by_id(transaction_id):
    session = SessionLocal()
    try:
        transaction = session.query(Transaction).filter_by(id=transaction_id).first()
        return transaction
    except SQLAlchemyError as e:
        logger.error(f"Error fetching transaction: {e}")
        return None
    finally:
        session.close()

def get_transactions_by_user_id(user_id):
    session = SessionLocal()
    try:
        transactions = session.query(Transaction).filter_by(user_id=user_id).order_by(Transaction.created_at.desc()).all()
        return transactions
    except SQLAlchemyError as e:
        logger.error(f"Error fetching transactions: {e}")
        return []
    finally:
        session.close()

def update_transaction(transaction_id, **kwargs):
    session = SessionLocal()
    try:
        transaction = session.query(Transaction).filter_by(id=transaction_id).first()
        if transaction:
            for key, value in kwargs.items():
                setattr(transaction, key, value)
            session.commit()
            logger.info(f"Transaction updated: {transaction}")
            return True
        else:
            logger.warning(f"Transaction with id {transaction_id} not found.")
            return False
    except SQLAlchemyError as e:
        logger.error(f"Error updating transaction: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def update_transaction_status(transaction_id, status):
    return update_transaction(transaction_id, status=status)
