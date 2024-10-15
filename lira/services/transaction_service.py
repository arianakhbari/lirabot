# services/transaction_service.py

import logging
from sqlalchemy.exc import SQLAlchemyError
from database import SessionLocal
from models import Transaction, User
from utils.helpers import is_admin

logger = logging.getLogger(__name__)

def create_transaction(user_id, transaction_type, amount, total_price):
    session = SessionLocal()
    try:
        transaction = Transaction(
            user_id=user_id,
            transaction_type=transaction_type,
            amount=amount,
            total_price=total_price,
            status='awaiting_payment'
        )
        session.add(transaction)
        session.commit()
        session.refresh(transaction)
        logger.info(f"Transaction created: {transaction}")
        return transaction
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error creating transaction: {e}")
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

def update_transaction_status(transaction_id, new_status):
    session = SessionLocal()
    try:
        transaction = session.query(Transaction).filter_by(id=transaction_id).first()
        if transaction:
            transaction.status = new_status
            session.commit()
            logger.info(f"Transaction {transaction_id} status updated to {new_status}")
            return True
        return False
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error updating transaction status: {e}")
        return False
    finally:
        session.close()

def get_user_transactions(user_id):
    session = SessionLocal()
    try:
        transactions = session.query(Transaction).filter_by(user_id=user_id).all()
        return transactions
    except SQLAlchemyError as e:
        logger.error(f"Error fetching user transactions: {e}")
        return []
    finally:
        session.close()

def get_all_transactions():
    session = SessionLocal()
    try:
        transactions = session.query(Transaction).all()
        return transactions
    except SQLAlchemyError as e:
        logger.error(f"Error fetching all transactions: {e}")
        return []
    finally:
        session.close()
