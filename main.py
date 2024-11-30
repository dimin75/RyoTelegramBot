#  Main.py will serve as the entry point of the bot. 
#  It initializes the bot, registers the command and 
#  message handlers, and starts the bot polling.

# Main responsibilites:
# Initialize the application.
# Define command handlers and 
# register them to the bot.
# Start polling.
# Define conversation states
from constants import (
    CREATE_WALLET, DELETE_WALLET, 
    RESTORE_WALLET, SEED_PROCESS, 
    BLOCKHEIGHT_TAKE, ADDRESS_REQUEST, 
    BALANCE, SEND_ADDR, SEND_SUM, SEND_TRANSFER, SEED_REQUEST
    )
#CREATE_WALLET, DELETE_WALLET, RESTORE_WALLET, BALANCE, SEND = range(5)

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from handlers import start, cvh_new_wallet, test_base, restore_wallet_password 
from handlers import create_wallet_password, ryo_rates_handler, restore_wallet_seed
#, handle_message, send_funds
from db import init_db

from logger import setup_logging
from telegram.ext import Application
#, ApplicationBuilder
from config import TELEGRAM_BOT_TOKEN
from rpc import start_wallet_rpc, is_wallet_running
from handlers import (
    cvh_handle_delete, delete_wallet_password, 
    cvh_restore_wallet, req_seed, get_seed_psw
    )
from handlers import (
    balance_check, send_address_input, 
    proc_wallet_bh, address_info, 
    check_address, cvh_check_balance,
    cvh_send_funds, send_ryo_sum, send_ryo_confirm
    )


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


    # Conversation handler for commands needing multiple steps
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("ryo_rates",ryo_rates_handler),
            CommandHandler("test_base", test_base),
            CommandHandler("create_wallet", cvh_new_wallet),
            CommandHandler("delete_wallet", cvh_handle_delete),
            CommandHandler("restore_wallet", cvh_restore_wallet),
            CommandHandler("check_address", check_address),
            CommandHandler("balance", cvh_check_balance),
            CommandHandler("send", cvh_send_funds),
            CommandHandler("seed_request", req_seed),
        ],
        states={
            CREATE_WALLET: [
                MessageHandler(filters.TEXT, create_wallet_password),
            ],
            DELETE_WALLET: [
                MessageHandler(filters.TEXT, delete_wallet_password),
            ],
            RESTORE_WALLET: [
                MessageHandler(filters.TEXT, restore_wallet_password),
            ],
            SEED_PROCESS: [
                MessageHandler(filters.TEXT, restore_wallet_seed),
            ],
            BLOCKHEIGHT_TAKE: [
                MessageHandler(filters.TEXT , proc_wallet_bh),
                #CommandHandler("address", address_info)
            ],
            ADDRESS_REQUEST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, address_info),
                CommandHandler("address", address_info),
            ],
            SEED_REQUEST: [
                MessageHandler(filters.TEXT, get_seed_psw),
            ],
            BALANCE: [
                MessageHandler(filters.TEXT, balance_check),
            ],
            SEND_ADDR: [
                MessageHandler(filters.TEXT, send_address_input),
            ],
            SEND_SUM: [
                MessageHandler(filters.TEXT, send_ryo_sum),
            ],
            SEND_TRANSFER: [
                MessageHandler(filters.TEXT, send_ryo_confirm),
            ]
        },
        fallbacks=[CommandHandler("cancel", start)]
    )

    # Adding the handlers to the application
    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)

    # # Register handlers for commands
    # application.add_handler(CommandHandler("start", start))
    # application.add_handler(CommandHandler("ryo_rates",ryo_rates_handler))
    # application.add_handler(CommandHandler("create_wallet", new_wallet))
    # application.add_handler(CommandHandler("restore_wallet", restore_wallet))
    # #application.add_handler(CommandHandler("delete_wallet", start))
    # application.add_handler(CommandHandler("test_base", test_base))
    # # application.add_handler(CommandHandler("balance", q_check_balance))
    # # application.add_handler(CommandHandler("send", send_funds))
    # application.add_handler(CallbackQueryHandler(button_handler))
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    # print("Adding /delete command handler...")
    # application.add_handler(CommandHandler("delete_wallet", handle_delete))
    # # application.add_handler(CallbackQueryHandler(handle_delete_confirmation, pattern="^confirm_delete$|^cancel_delete$"))
    # #application.add_handler(CallbackQueryHandler(handle_delete_confirmation))

    logger.info("Bot started successfully")
    # Start the bot (polling mode)
    # application.run_polling()
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()