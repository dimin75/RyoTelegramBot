# Utilities.py includes utility functions that don't 
# directly belong to the main logic but are used 
# in various parts of the project (e.g., 
# formatting responses, password validation, etc.).

# Main responsibilities:

#     Helper functions that support the core logic.
#     Logging, message formatting, validation, etc.

# Example contents:

#     Utility functions like delete_message, validate_password.

from config import setup_logging

logger = setup_logging()

async def validate_password(password):
    logger.debug("Validating password")
    if len(password) < 8:
        logger.warning("Password too short")
    # Validation logic

async def delete_message(context, chat_id, message_id, delay=5):
    await asyncio.sleep(delay)
    await context.bot.delete_message(chat_id=chat_id, message_id=message_id)