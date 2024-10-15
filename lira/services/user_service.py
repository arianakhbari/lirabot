# services/user_service.py

import os
import logging
from sqlalchemy.exc import SQLAlchemyError
from database import SessionLocal
from models import User
from utils.helpers import is_admin

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
            is_verified=False
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        logger.info(f"User registered: {user}")
        return user
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error registering user: {e}")
        return None
    finally:
        session.close()

def get_user_by_telegram_id(telegram_id):
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        return user
    except SQLAlchemyError as e:
        logger.error(f"Error fetching user: {e}")
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
        return False
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error verifying user: {e}")
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
        return False
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error rejecting user: {e}")
        return False
    finally:
        session.close()
