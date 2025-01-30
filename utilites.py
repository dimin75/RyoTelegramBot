# Utilities.py includes utility functions that don't 
# directly belong to the main logic but are used 
# in various parts of the project (e.g., 
# formatting responses, password validation, etc.).

# Main responsibilities:

#     Helper functions that support the core logic.
#     Logging, message formatting, validation, etc.

# Example contents:

#     Utility functions like delete_message, validate_password.

from logger import setup_logging
import bcrypt

logger = setup_logging()

def ryoval2user(ryo_val):
    return float(ryo_val / 1e9)

def user2ryoval(val):
    return int(float(val) * 1e9)

def hash_password(password: str) -> str:
    # Salt and hash generation
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')  # store password as string

def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

async def validate_password(password):
    logger.debug("Validating password")
    if len(password) < 8:
        logger.warning("Password too short")
    # Validation logic

async def delete_message(context, chat_id, message_id, delay=5):
    await asyncio.sleep(delay)
    await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
