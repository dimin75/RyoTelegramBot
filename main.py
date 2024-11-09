#  Main.py will serve as the entry point of the bot. 
#  It initializes the bot, registers the command and 
#  message handlers, and starts the bot polling.

# Main responsibilites:
# Initialize the application.
# Define command handlers and 
# register them to the bot.
# Start polling.

from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from handlers import start, new_wallet, button_handler, test_base, handle_message 
from handlers import ryo_rates_handler
#, handle_message, send_funds
from db import init_db

from logger import setup_logging
from telegram.ext import Application
#, ApplicationBuilder
from config import TELEGRAM_BOT_TOKEN
from rpc import start_wallet_rpc, is_wallet_running
from handlers import handle_delete, handle_delete_confirmation, restore_wallet

logger = setup_logging()

async def check_bot_alive(context):
    logger.info("Bot is alive and running")


def main() -> None:
    # Initialize the database
    init_db()

    # Check if wallet server is running and start it if necessary
    if not is_wallet_running():
        start_wallet_rpc()

    # Create the Updater and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()


    # Register handlers for commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ryo_rates",ryo_rates_handler))
    application.add_handler(CommandHandler("create_wallet", new_wallet))
    application.add_handler(CommandHandler("restore_wallet", restore_wallet))
    #application.add_handler(CommandHandler("delete_wallet", start))
    application.add_handler(CommandHandler("test_base", test_base))
    # application.add_handler(CommandHandler("balance", q_check_balance))
    # application.add_handler(CommandHandler("send", send_funds))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Adding /delete command handler...")
    application.add_handler(CommandHandler("delete_wallet", handle_delete))
    # application.add_handler(CallbackQueryHandler(handle_delete_confirmation, pattern="^confirm_delete$|^cancel_delete$"))
    #application.add_handler(CallbackQueryHandler(handle_delete_confirmation))

    logger.info("Bot started successfully")
    # Start the bot (polling mode)
    application.run_polling()


if __name__ == '__main__':
    main()