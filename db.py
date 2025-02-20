# Db.py module handles all database interactions. 
# It manages creating user wallets, storing wallet 
# details, and retrieving information from the 
# database. It also encapsulates database session 
# handling.

# Main responsibilities:

#     Interfacing with the database (SQLite).
#     Creating, reading, updating, and deleting wallet records.

# Contents:

#     SQLAlchemy model for user wallets.
#     Functions for initializing the database, creating user wallets, and retrieving data.

import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from datetime import datetime

from logger import setup_logging
from config import DATABASE_URL, USER_DB_PATH

from telegram import Update
from telegram.ext import CallbackContext

logger = setup_logging()


Base = declarative_base()



# UserWallet table to store Telegram user-to-wallet mapping
class UserWallet(Base):
    __tablename__ = 'user_wallets'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, unique=True, nullable=False)  # Telegram User ID
    user_psw = Column(String(60), nullable=False)
    wallet_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    # address = Column(String, nullable=False)
    # view_key = Column(String, nullable=False)
    # mnemonic = Column(String, nullable=False)


# Function to initialize the database (creates tables if they don't exist)
def init_db():
    # Ensure that the directory for user database exists
    #if not os.path.exists(os.path.dirname(USER_DB_PATH)):
        #os.makedirs(os.path.dirname(USER_DB_PATH))
        #logger.info(f"Created directory for user database: {os.path.dirname(USER_DB_PATH)}")
    #Docker volumes path to DB-checking:
    if not os.path.exists(os.path.dirname(DATABASE_URL.replace("sqlite:///", ""))):
        os.makedirs(os.path.dirname(DATABASE_URL.replace("sqlite:///", "")), exist_ok=True)
        logger.info(f"Created directory for database: {os.path.dirname(DATABASE_URL.replace('sqlite:///', ''))}")

    if not os.path.exists(USER_DB_PATH):
        os.makedirs(os.path.dirname(USER_DB_PATH), exist_ok=True)
        logger.info(f"Created directory for user database: {os.path.dirname(USER_DB_PATH)}")
    
    # Initialize database engine
    engine = create_engine(DATABASE_URL)
    
    # Bind the session to the engine
    Session = sessionmaker(bind=engine)

    # Create all tables (if they don't already exist)
    Base.metadata.create_all(engine)
    logger.info("Database initialized with all tables created.")
    
    return Session

def delete_user_wallet_record(session, wallet_record) -> bool:
    session.delete(wallet_record)
    session.commit()
    return True 

def add2db_wallet(session, user_id, user_psw, wallet_name):
    wallet = UserWallet(user_id=user_id, user_psw=user_psw, wallet_name=wallet_name)
    session.add(wallet)
    session.commit()
    logger.info(f"Added wallet for user {user_id} to database.")

