# Handlers.py contains all Telegram bot handler 
# functions (e.g., responding to 
# /start, 
# /create_wallet, 
# /balance commands, etc.). 
# It will interact with wallet.py for 
# operations and return messages to the user.

# Main responsibilities:

#     Handling user commands.
#     Processing Telegram updates and interacting with the wallet management logic.

# Contents:

#     start, 
#     new_wallet, 
#     check_balance, 
#     send_funds, 
#     handlers.

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackContext, ConversationHandler
from wallet import WalletManager

from logger import setup_logging
from config import RPC_URL
from db import init_db, UserWallet, add2db_wallet
from rpc import (
    create_wallet_via_rpc, restore_wallet_via_rpc, 
    open_wallet_rpc, get_address_wallet_rpc,
    close_wallet_rpc, get_balance_wallet_rpc,
    get_seed_mnemonic_rpc
    )

import asyncio
import requests
import aiohttp
from aiohttp import ClientSession, ClientResponseError
from concurrent.futures import ThreadPoolExecutor
from config import RYO_USD_RATE, RYO_BTC_RATE, RYO_RUB_RATE, BTC_USD_RATE, RUB_USD_RATE
from config import RPC_REQUEST_TIMEOUT, WALLET_DIR
import config

from rpc import delete_wallet_files
from db import delete_user_wallet_record
from constants import (
    CREATE_WALLET, DELETE_WALLET, RESTORE_WALLET, 
    SEED_PROCESS, BLOCKHEIGHT_TAKE, ADDRESS_REQUEST, 
    BALANCE, SEND_ADDR, SEND_SUM, SEND_TRANSFER, SEED_REQUEST,
    MAKE_SEND_TRANSACTION, MAKE_SEND_TRANSACTION_PAY_ID
    )

from utilites import hash_password, verify_password, ryoval2user, user2ryoval

logger = setup_logging()

# Initialize the session factory
Session = init_db()

async def handle_delete(update: Update, context: CallbackContext) -> None:
    # user_id = update.message.from_user.id
    user = update.message.from_user
    user_id = user.id
    logger.info(f"User {user_id} requested a wallet creation")
    context.user_data['user_id'] = user_id
    logger.info(f"pass user_id to handle_message section : {user_id}")    
    logger.info("Response on /delete key: inside handle_delete...")
    print("now in /delete command handler...")
    # session = Session()
    # Show confirmation receipt on wallet deletion
    keyboard = [
        [
            InlineKeyboardButton("Confirm", callback_data="confirm_delete"),
            InlineKeyboardButton("Cancel", callback_data="cancel_delete")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Are you sure to delete wallet? This action can't be undone.",
        reply_markup=reply_markup
    )

async def handle_delete_confirmation(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    if query.data == "confirm_delete":
        # Delete wallet and record from base
        user_id = query.from_user.id
        wallet_name = f"{user_id}_wallet"  # wallet file name
        await delete_wallet_files(wallet_name)  # file deletion
        Session = init_db()
        wallet_record = session.query(UserWallet).filter_by(user_id=user_id).first()
        with Session() as session: # Create instance of sesson
            wallet_deleted = await delete_user_wallet_record(session, wallet_record)  # Delete record from database
            if wallet_deleted:
                await query.edit_message_text("Your wallet have been deleted. To create new one use /create_wallet ")
    elif query.data == "cancel_delete":
        await query.edit_message_text("Deletion cancelled.")

def fetch_url(url):
    logger.info(f"Requesting {url}")
    
    try:
        response = requests.get(url, timeout=RPC_REQUEST_TIMEOUT)
        response.raise_for_status()  # Raises HTTPError for bad responses

        try:
            json_data = response.json()
            logger.info("Response JSON: %s", json_data)
            return json_data
        except ValueError:
            logger.error("Response is not in JSON format")
            return None
    except requests.exceptions.Timeout:
        logger.warning(f"Request to {url} timed out after {RPC_REQUEST_TIMEOUT} seconds.")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching {url}: {e}")
        return None

async def async_notify_user(context, chat_id, message):
    await context.bot.send_message(chat_id=chat_id, text=message)

async def async_fetch_url(url, context=None, chat_id=None):
    loop = asyncio.get_event_loop()
    if context and chat_id:
        await async_notify_user(context, chat_id, f"Requesting {url}")
        
    with ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, fetch_url, url)
    
    if result is None and context and chat_id:
        await async_notify_user(context, chat_id, f"Failed to fetch data from {url}")
    
    return result


#async def ryo_rates_handler(update, context):
async def ryo_rates_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        user = update.callback_query.from_user
        chat_id = update.callback_query.message.chat_id
    else:
        user = update.message.from_user
        chat_id = update.message.chat_id
    logger.info(f"User {user.id} requested exchange rate information")
    logger.info(f"Exchange rates RYO_BTC {config.RYO_BTC_RATE} ")
    logger.info(f"Exchange rates RYO_BTC {config.BTC_USD_RATE} ")
    logger.info(f"Exchange rates RUB_USD {config.RUB_USD_RATE} ")
    urls = {
        "ryo_btc": 'https://tradeogre.com/api/v1/ticker/RYO-BTC',
        "btc_usd": 'https://tradeogre.com/api/v1/ticker/BTC-USDT',
        "usd_rub": 'https://www.cbr-xml-daily.ru/daily_json.js'
    }

    tasks = { 
        'ryo_btc': async_fetch_url(urls["ryo_btc"], context=context, chat_id=update.effective_chat.id),
        'btc_usd': async_fetch_url(urls["btc_usd"], context=context, chat_id=update.effective_chat.id),
        'usd_rub': async_fetch_url(urls["usd_rub"], context=context, chat_id=update.effective_chat.id)
    }   

    warn_message = (f"Please, be patient:\n"
                f"Requests to API-servers take time and may be cancelled out after {RPC_REQUEST_TIMEOUT} seconds\n"
                f"if server not respond")        
    await context.bot.send_message(chat_id=update.effective_chat.id, text=warn_message)

    results = await asyncio.gather(*tasks.values())

    ryo_btc_price = float(results[0].get("price", config.RYO_BTC_RATE))
    btc_usd_price = float(results[1].get("price", config.BTC_USD_RATE))
    usd_rub_price = float(results[2].get("Valute", {}).get("USD", {}).get("Value", config.RUB_USD_RATE))

    ryo_usd_price = ryo_btc_price * btc_usd_price
    ryo_rub_price = ryo_usd_price * usd_rub_price        

    message = (f"Current exchange rate for RYO:\n"
                f"1 RYO per BTC: {ryo_btc_price}\n"
                f"1 BTC per USD: {btc_usd_price}\n"
                f"1 USD per RUB: {usd_rub_price}\n\n"
                f"Price for 1 RYO per USD: {ryo_usd_price}\n"
                f"Price for 1 RYO per RUB: {ryo_rub_price}")
    # Sending message to user
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)


# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     await update.message.reply_text(
#         "Welcome! Use the following commands to interact with your RYO wallet:\n" +
#         "/create_wallet - Create new wallet\n" +
#         "/delete_wallet - Delete your wallet\n" +
#         "/restore_wallet - Restore wallet from seed\n" +
#         "/balance - Check wallet balance\n" +
#         "/send - Send funds to another wallet\n"
#     )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        user = update.callback_query.from_user
        chat_id = update.callback_query.message.chat_id
    else:
        user = update.message.from_user
        chat_id = update.message.chat_id
    logger.info(f"User {user.id} started a conversation")
    # await update.message.reply_text("Welcome to the Ryo wallet bot!")
    if update.callback_query:
        await update.callback_query.message.reply_text("Welcome to the Ryo wallet bot!")
    else:
        await update.message.reply_text("Welcome to the Ryo wallet bot!")
    command_list = [
        "/start - Get help prompt about bot functionality",
        "/create_wallet - Create new wallet for payments in RYO",
        "/delete_wallet - Delete your active wallet completely",
        "/restore_wallet - Restore your RYO wallet from seed phrase",
        "/check_address - Display RYO-address(es) of your wallet",
        "/balance - check balance of your wallet",
        "/send - send RYO coins to other wallet",
        "/test_base - display all user records located on server",
        "/ryo_rates - check current exchange rated for RYO coin",
        "/seed_request - request you seed-phrase from wallet to save it in secure place"

    ]
    ryo_usd_price = RYO_BTC_RATE * BTC_USD_RATE
    ryo_rub_price = ryo_usd_price * RUB_USD_RATE
    message2 = [
        f"Current exchange rate for RYO:",
        f"1 RYO per BTC: {RYO_BTC_RATE}",
        f"1 BTC per USD: {BTC_USD_RATE}",
        f"1 USD per RUB: {RUB_USD_RATE}",
        f"Price for 1 RYO per USD: {ryo_usd_price}",
        f"Price for 1 RYO per RUB: {ryo_rub_price}"

    ]   
    reply_text = "Hi! This is telegram bot for RYO-payment service (test version). Avialable commands are:\n\n" + "\n".join(command_list)
    reply_text2 = "For today prices for currency might be the following:\n" + "\n".join(message2)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=reply_text)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=reply_text2)

async def restore_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id
    logger.info(f"User {user_id} requested a wallet restoration")
    context.user_data['user_id'] = user_id

    session = Session()
    # Check, if the user already has a wallet
    user_wallet = session.query(UserWallet).filter_by(user_id=user_id).first()

    if user_wallet:
        await update.message.reply_text("You already have a wallet. To restore, delete the existing wallet first with /delete_wallet.")
        return

    keyboard = [
        [
            InlineKeyboardButton("Restore", callback_data="q_restore"),
            InlineKeyboardButton("Cancel", callback_data="q_rest_cancel"),
        ],
        
    ]
     
    
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Would you like to restore your previously created wallet now?", reply_markup=reply_markup)
    # # Send a request on enter seed-phrase
    # await update.message.reply_text("Please enter your 25-word seed phrase for wallet restoration:")

    # # Setting up flag on waiting of input seed-phrase
    # context.user_data['awaiting_seed'] = True
    # context.user_data['action'] = "restore_wallet"

async def test_base(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    user_id = user.id    
    session = Session()
    logger.info(f"User {user_id} requested a users base content for a moment")
    # get all records from UserWallet
    wallets = session.query(UserWallet).all()

    if not wallets:
        await update.message.reply_text("No wallets found in the database.")
    else:
        # display all records from table
        for wallet in wallets:
            message = (f"Wallet ID: {wallet.id}\n"
                       f"User ID: {wallet.user_id}\n"
                       f"Wallet Name: {wallet.wallet_name}")
            await update.message.reply_text(message)
    
    session.close()

async def cvh_check_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    session = Session()
    user_id = update.message.from_user.id
    logger.info(f"User {user_id} requested a balance checking")

   # Get user's wallet from the database
    user_wallet = session.query(UserWallet).filter_by(user_id=str(user_id)).first()
    if not user_wallet:
        await update.message.reply_text("You don't have a wallet yet. Use /create_wallet to create one.")
        session.close()
        return ConversationHandler.END

    # Save wallet ID and database password in context for further steps
    logger.info(f"Get user {user_id} password from database...")
    context.user_data["user_id"] = user_id
    context.user_data["db_password"] = user_wallet.user_psw

    await update.message.reply_text("Please enter a password for wallet balance checking:")
    session.close()    
    return BALANCE

async def cvh_send_funds(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    session = Session()
    user_id = update.message.from_user.id
    logger.info(f"User {user_id} requested a funds transfer...")

   # Get user's wallet from the database
    user_wallet = session.query(UserWallet).filter_by(user_id=str(user_id)).first()
    if not user_wallet:
        await update.message.reply_text("You don't have a wallet yet. Use /create_wallet to create one.")
        session.close()
        return ConversationHandler.END

    # Save wallet ID and database password in context for further steps
    logger.info(f"Get user {user_id} password from database...")
    context.user_data["user_id"] = user_id
    context.user_data["db_password"] = user_wallet.user_psw

    await update.message.reply_text("Please enter a password for funds sending:")
    session.close()
    return SEND_ADDR

async def send_address_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_pass = update.message.text  # Get the password entered by the user
    # rstrd_pass = context.user_data.get("user_password")
    db_password = context.user_data.get("db_password")
    user_id = context.user_data.get("user_id")
    logger.info(f"User {user_id} entered BALANCE point")
    await update.message.reply_text(f"Provided password: {user_pass}")
    await update.message.reply_text(f"Database hashed password: {db_password}")
    if  not verify_password(user_pass, db_password):
        await update.message.reply_text(f"Provided password: {user_pass}")
        await update.message.reply_text(f"Database password: {db_password}")
        await update.message.reply_text("Invalid password. Please try again.")
        return ConversationHandler.END

        # Password is correct

    context.user_data["user_pass"] = user_pass
    await update.message.reply_text("Password accepted. Please input ryo-address to send coins...:")
    # await update.message.reply_text(f"Password correct. Please input_address 2 send")
    return SEND_SUM

async def send_ryo_sum(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    send_ryo_address = update.message.text
    context.user_data["send_ryo_address"] = send_ryo_address
    await update.message.reply_text("Fetching your wallet balance...")
    user_id = context.user_data.get("user_id")
    user_pass = context.user_data.get("user_pass")
    # Open the wallet
    wallet_opened = await open_wallet_rpc(user_id, user_pass)
    if not wallet_opened:
        await update.message.reply_text("Failed to open wallet. Please try again later.")
        return ConversationHandler.END

    # Get wallet balance
    wallet_balance = await get_balance_wallet_rpc(user_id, user_pass)
    context.user_data["spent_balance"] = "0"
    if wallet_balance[0] == "Error":
        await update.message.reply_text(f"Error fetching balance: {wallet_balance[1]}")
    else:
        balance, unlocked_balance = wallet_balance
        await update.message.reply_text(
            f"Wallet Balance: {ryoval2user(balance):.2f} RYO\n"
            f"Unlocked Balance: {ryoval2user(unlocked_balance):.2f} RYO"
        )
        context.user_data["spent_balance"] = balance

    #wallet_closed = await close_wallet_rpc(user_id, user_pass)
    #if wallet_closed:
        #await update.message.reply_text("Wallet closed.")
    #else:
        #await update.message.reply_text("Some problem appeared during the wallet closing...")


    await update.message.reply_text(f"Please input sum to send.")
    #await update.message.reply_text(f"Your balance is following:")
    return SEND_TRANSFER

async def send_ryo_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    sum_ryo_send = update.message.text
    context.user_data["sum_ryo_send"] = sum_ryo_send
    send_ryo_address = context.user_data.get("send_ryo_address")
    await update.message.reply_text(f"Now check the data transaction:")
    await update.message.reply_text(f"Send to {send_ryo_address} amount of {sum_ryo_send} Ryo coins. ")
    await update.message.reply_text(f"Type 'yes' if you agree to send those one.")
    await update.message.reply_text(f"Use /pay_id if you need to add payment_ID to your address")
    return MAKE_SEND_TRANSACTION

async def msend_trans(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    send_action = update.message.text.lower()
    user_id = context.user_data.get("user_id")
    user_pass = context.user_data.get("user_pass")
    sum_ryo_send = context.user_data.get("sum_ryo_send")
    send_ryo_address = context.user_data.get("send_ryo_address")
    curr_wallet_balance = context.user_data.get("spent_balance")
    await update.message.reply_text(f"Okay. You replied with {send_action}")
    if send_action == 'yes':
        await update.message.reply_text(f"Will send your money as you requested...")
    if send_action == '/pay_id':
        await update.message.reply_text(f"Enter your payment id:")
        return MAKE_SEND_TRANSACTION_PAY_ID
    await update.message.reply_text(f"You want to spend {sum_ryo_send} in int({user2ryoval(sum_ryo_send)})")
    await update.message.reply_text(f"You have in wallet {ryoval2user(curr_wallet_balance)} in int({curr_wallet_balance})")
    if ryoval2user(curr_wallet_balance) > float(sum_ryo_send):
        await update.message.reply_text(f"You have enough money to spend. Now make transaction...")
        money_send = await send_coins_rpc(user2ryoval(sum_ryo_send), rpc_address, user_id, user_pass)
        if not money_send:
            await update.message.reply_text("Failed to create send transaction. Try again later. Or call support.")
            return ConversationHandler.END
        transfer_submit = await submit_transaction_rpc(user_id, user_pass)
        if not transfer_submit:
            await update.message.reply_text("Can't submit transaction. Check your balance. Try again later. Or call support.")
            return ConversationHandler.END
    else:
        await update.message.reply_text(f"You don't have enough money to spend. Choose other amount of RYO to send.")
        return  ConversationHandler.END

    wallet_closed = await close_wallet_rpc(user_id, user_pass)
    if wallet_closed:
        await update.message.reply_text("Wallet closed.")
    else:
        await update.message.reply_text("Some problem appeared during the wallet closing...")

    return ConversationHandler.END

async def msend_trans_payid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    pay_id = update.message.text.lower()
    await update.message.reply_text(f"payment_ID for this transaction: {pay_id}")
    return ConversationHandler.END

async def cvh_new_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    logger.info(f"User {user_id} requested a wallet creation")
    context.user_data['user_id'] = user_id
    session = Session()
    # Checking the user wallet existence
    user_wallet = session.query(UserWallet).filter_by(user_id=user_id).first()
    if user_wallet:
        await update.message.reply_text(f"You already have a wallet.\nYour id: {user_wallet.user_id}\nCreated: {user_wallet.created_at}")
        return ConversationHandler.END   
    # if user_has_wallet(user_id):
    #     await update.message.reply_text("You already have a wallet.")
    #     return ConversationHandler.END
    await update.message.reply_text("Please enter a password for your new wallet:")
    return CREATE_WALLET

async def create_wallet_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    password = update.message.text
    user_id = update.message.from_user.id
    # wallet_id = create_rpc_wallet(user_id, password)
    # add_wallet(user_id, wallet_id)
    # await update.message.reply_text("Wallet created successfully!")
    rpc_user = user_id
    password_from_user = password
    logger.info(f" {rpc_user} now can create wallet...")

    # Create session for db transaction
    Session = init_db()
    with Session() as session: # Create instance of sesson
            # Create wallet via RPC-server
            wallet_created = await create_wallet_via_rpc(rpc_user, password_from_user)
            
            if wallet_created:
                # Add info about wallet to database
                wallet_name = f"{WALLET_DIR}/{rpc_user}_wallet"
                add2db_wallet(session, user_id=rpc_user, user_psw=hash_password(password_from_user), wallet_name=wallet_name)
                await update.message.reply_text("Wallet created successfully.")
            else:
                await update.message.reply_text("Failed to create wallet.")    
    
    return ConversationHandler.END

async def cvh_handle_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    session = Session()
    #await update.message.reply_text("Are you sure to delete wallet? This action can't be undone.\n Type 'yes' to confirm.")
    await update.message.reply_text("Are you sure to delete wallet? This action can't be undone.\n Type 'no' if you are not sure.")
    user_id = update.message.from_user.id
    logger.info(f"User {user_id} requested a wallet deletion")
    context.user_data['user_id'] = user_id
    # Get user's wallet from the database
    user_wallet = session.query(UserWallet).filter_by(user_id=str(user_id)).first()
    if not user_wallet:
        await update.message.reply_text("You don't have a wallet yet. Use /create_wallet to create one.")
        session.close()
        return ConversationHandler.END
    
    context.user_data["db_password"] = user_wallet.user_psw

    await update.message.reply_text("Please enter a password for your existing wallet:")
    session.close()
    return DELETE_WALLET

async def delete_wallet_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    #response = update.message.text.lower()
    response = update.message.text
    user_id = context.user_data.get('user_id')
    wallet_name = f"{user_id}_wallet"  # wallet file name
    db_password = context.user_data.get("db_password")

    if  verify_password(response, db_password):
    #if response == "yes":
        await update.message.reply_text("Password accepted. Now delete wallet...")
        await delete_wallet_files(wallet_name)  # file deletion
        Session = init_db()
        with Session() as session:
            wallet_record = session.query(UserWallet).filter_by(user_id=user_id).first()
            wallet_deleted = delete_user_wallet_record(session, wallet_record)  # Delete record from database
            if wallet_deleted:
                await update.message.reply_text("Your wallet have been deleted. To create new one use /create_wallet.")
    else:
        await update.message.reply_text("Wallet deletion cancelled.")            

    return ConversationHandler.END

async def cvh_restore_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # user_id = update.message.from_user.id
    user_id = update.message.from_user.id
    logger.info(f"User {user_id} requested a wallet restoring")
    context.user_data['user_id'] = user_id
    session = Session()    
    # Checking the user wallet existence
    user_wallet = session.query(UserWallet).filter_by(user_id=user_id).first()
    if user_wallet:
        await update.message.reply_text(f"You already have a wallet.\nYour id: {user_wallet.user_id}\nCreated: {user_wallet.created_at}")
        return ConversationHandler.END   
    
    # if user_has_wallet(user_id):
    #     await update.message.reply_text("You already have a wallet.")
    #     return ConversationHandler.END

    await update.message.reply_text("Please enter a password for your wallet to restore:")
    return RESTORE_WALLET

async def restore_wallet_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    #password = update.message.text
    user_id = update.message.from_user.id
    response = update.message.text
    context.user_data['user_password'] = response
    context.user_data['user_id'] = user_id
    await update.message.reply_text(f"Obtain your pwd: {response} for user {user_id}")
    await update.message.reply_text(f"Now give me your seed: ")
    return SEED_PROCESS

async def restore_wallet_seed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    response = update.message.text
    context.user_data['seed_phrase'] = response
    logger.info(f"Action seed phrase request raised ok. User should see his seed...")    
    await update.message.reply_text(f"This is your seed: {response}")
    await update.message.reply_text(f"Now give me your height: ")
    return BLOCKHEIGHT_TAKE

async def proc_wallet_bh(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    response = update.message.text if update.message.text.isdigit() else "0"
    context.user_data['block_height'] = response
    logger.info(f"Action block height request raised ok. User should see his block height to restore...")    
    await update.message.reply_text(f"Let's process your full request... Finally info for restore:")
    user_id = context.user_data.get('user_id')
    user_password = context.user_data.get('user_password')
    seed_phrase = context.user_data.get('seed_phrase')
    await update.message.reply_text(f"User_id: {user_id}")
    await update.message.reply_text(f"User password: {user_password}")
    await update.message.reply_text(f"Seed phrase: {seed_phrase}")
    await update.message.reply_text(f"BLOCKCHAIN HEIGHT: {response}")
    success = await restore_wallet_via_rpc(user_id, seed_phrase, user_password, response)
    if success:
        session = Session()
        add2db_wallet(session, user_id, hash_password(user_password), f"{user_id}_wallet")
        await update.message.reply_text("Your wallet has been successfully restored and saved.")
        await update.message.reply_text("To see the address, please tap the /address key.")
        return ADDRESS_REQUEST
    else:
        await update.message.reply_text("Failed to restore wallet. Please check your seed phrase and try again.")
    #return BLOCKHEIGHT_TAKE 
        return ConversationHandler.END

async def req_seed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = Session()
    user_id = update.message.from_user.id
    logger.info(f"User {user_id} requested his seed checking")

   # Get user's wallet from the database
    user_wallet = session.query(UserWallet).filter_by(user_id=str(user_id)).first()
    if not user_wallet:
        await update.message.reply_text("You don't have a wallet yet. Use /create_wallet to create one.")
        session.close()
        return ConversationHandler.END

    # Save wallet ID and database password in context for further steps
    logger.info(f"Get user {user_id} password from database...")
    context.user_data["user_id"] = user_id
    context.user_data["db_password"] = user_wallet.user_psw

    # Ask password from user for the wallet password
    await update.message.reply_text("Please enter your wallet password to see your seed:")
    session.close()
    return SEED_REQUEST

async def get_seed_psw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: 
    response = update.message.text
    user_id = context.user_data.get('user_id')
    db_password = context.user_data.get("db_password")

    if  not verify_password(response, db_password):
        await update.message.reply_text("Wallet seed request unsuccessful.")      

    await update.message.reply_text("Password accepted. Now check your seed...")

    # Open the wallet
    wallet_opened = await open_wallet_rpc(user_id, response)
    if not wallet_opened:
        await update.message.reply_text("Failed to open wallet. Please try again later.")
        return ConversationHandler.END

    wallet_seed = await get_seed_mnemonic_rpc(user_id, response)  # getting the wallet seed
    if wallet_seed:
        await update.message.reply_text("Your seed is:")
        await update.message.reply_text(wallet_seed)


    wallet_closed = await close_wallet_rpc(user_id, response)
    if wallet_closed:
        await update.message.reply_text("Wallet closed.")
    else:
        await update.message.reply_text("Some problem appeared during the wallet closing...")

    return ConversationHandler.END   

async def check_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = Session()
    user_id = update.message.from_user.id
    logger.info(f"User {user_id} requested an adress checking")

   # Get user's wallet from the database
    user_wallet = session.query(UserWallet).filter_by(user_id=str(user_id)).first()
    if not user_wallet:
        await update.message.reply_text("You don't have a wallet yet. Use /create_wallet to create one.")
        session.close()
        return ConversationHandler.END

    # Save wallet ID and database password in context for further steps
    logger.info(f"Get user {user_id} password from database...")
    context.user_data["user_id"] = user_id
    context.user_data["db_password"] = user_wallet.user_psw

    # Ask password from user for the wallet password
    await update.message.reply_text("Please enter your wallet password:")
    session.close()
    return ADDRESS_REQUEST

async def address_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_pass = update.message.text  # Get the password entered by the user
    rstrd_pass = context.user_data.get("user_password")
    db_password = context.user_data.get("db_password")
    user_id = context.user_data.get("user_id")
    logger.info(f"User {user_id} entered adress_info point")
    if user_pass != "/address":
        await update.message.reply_text(f"Provided password: {user_pass}")
        await update.message.reply_text(f"Database hashed password: {db_password}")

        rstrd_pass = user_pass

        if not db_password or not user_id:
            await update.message.reply_text("Failed to retrieve user data. Please try again.")
            return ConversationHandler.END

        # Check if the entered password matches the stored password
        # if user_password != db_password:
        if  not verify_password(user_pass, db_password):
            await update.message.reply_text(f"Provided password: {user_pass}")
            await update.message.reply_text(f"Database password: {db_password}")
            await update.message.reply_text("Invalid password. Please try again.")
            return ConversationHandler.END

        # Password is correct
        await update.message.reply_text("Password accepted. Fetching your wallet address...")

    # Open the wallet
    wallet_opened = await open_wallet_rpc(user_id, rstrd_pass)
    if not wallet_opened:
        await update.message.reply_text("Failed to open wallet. Please try again later.")
        return ConversationHandler.END

    # Get wallet addresses
    wallet_addresses = await get_address_wallet_rpc(user_id, rstrd_pass)
    if wallet_addresses:
        # Output main address
        await update.message.reply_text(f"Your main address:\n1. {wallet_addresses[0]}")

        # Output sub-addresses if present
        if len(wallet_addresses) > 1:
            sub_addresses = "\n".join(
                [f"{i + 1}. {address}" for i, address in enumerate(wallet_addresses[1:], start=1)]
            )
            await update.message.reply_text(f"Your sub-addresses are the following:\n{sub_addresses}")
    else:
        await update.message.reply_text("Failed to retrieve wallet address. Please try again later.")

    wallet_closed = await close_wallet_rpc(user_id, rstrd_pass)
    if wallet_closed:
        await update.message.reply_text("Wallet closed.")
    else:
        await update.message.reply_text("Some problem appeared during the wallet closing...")


    return ConversationHandler.END    

async def balance_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # await update.message.reply_text(f"Balance_check happened")
    user_pass = update.message.text  # Get the password entered by the user
    # rstrd_pass = context.user_data.get("user_password")
    db_password = context.user_data.get("db_password")
    user_id = context.user_data.get("user_id")
    logger.info(f"User {user_id} entered BALANCE point")
    await update.message.reply_text(f"Provided password: {user_pass}")
    await update.message.reply_text(f"Database hashed password: {db_password}")
    if  not verify_password(user_pass, db_password):
        await update.message.reply_text(f"Provided password: {user_pass}")
        await update.message.reply_text(f"Database password: {db_password}")
        await update.message.reply_text("Invalid password. Please try again.")
        return ConversationHandler.END

        # Password is correct
    
    await update.message.reply_text("Password accepted. Fetching your wallet balance...")

    # Open the wallet
    wallet_opened = await open_wallet_rpc(user_id, user_pass)
    if not wallet_opened:
        await update.message.reply_text("Failed to open wallet. Please try again later.")
        return ConversationHandler.END

    # Get wallet balance
    wallet_balance = await get_balance_wallet_rpc(user_id, user_pass)
    if wallet_balance[0] == "Error":
        await update.message.reply_text(f"Error fetching balance: {wallet_balance[1]}")
    else:
        balance, unlocked_balance = wallet_balance
        await update.message.reply_text(
            f"Wallet Balance: {ryoval2user(balance):.2f} RYO\n"
            f"Unlocked Balance: {ryoval2user(unlocked_balance):.2f} RYO"
        )    

    wallet_closed = await close_wallet_rpc(user_id, user_pass)
    if wallet_closed:
        await update.message.reply_text("Wallet closed.")
    else:
        await update.message.reply_text("Some problem appeared during the wallet closing...")

    return ConversationHandler.END


# async def new_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     user = update.message.from_user
#     user_id = user.id
#     logger.info(f"User {user_id} requested a wallet creation")
#     context.user_data['user_id'] = user_id
#     logger.info(f"pass user_id to handle_message section : {user_id}")
#     session = Session()
#     # Checking the user wallet existence
#     user_wallet = session.query(UserWallet).filter_by(user_id=user_id).first()

#     if user_wallet:
#         await update.message.reply_text(f"You already have a wallet.\nYour id: {user_wallet.user_id}\nCreated: {user_wallet.created_at}")
#         return

#     keyboard = [
#         [
#             InlineKeyboardButton("Yes", callback_data="1"),
#             InlineKeyboardButton("No", callback_data="2"),
#         ],
        
#     ]
     
    
#     reply_markup = InlineKeyboardMarkup(keyboard)

#     await update.message.reply_text("Create your wallet now?", reply_markup=reply_markup)
   
    # password = "user-provided-password"
    # wallet_manager = WalletManager(rpc_url=RPC_URL, rpc_user="rpc_user", rpc_password="rpc_pass")
    # await wallet_manager.create_wallet(update.message.chat_id, password)
    # await update.message.reply_text("Wallet created successfully!")

async def delete_messages(context, chat_id, message_ids):
    await asyncio.sleep(10)  # waiting 30 sec before messages deletion
    for message_id in message_ids:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception as e:
            print(f"Failed to delete message {message_id}: {e}")

async def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()  # Close spinner after pushing the button
    print("attend button_handler")

    # Checking which button was pushed
    if query.data == "1":
        await query.message.reply_text("Please enter a password for your wallet:")
        # save state of waiting keyboard input
        context.user_data['awaiting_password'] = True
        context.user_data['action'] = "create_wallet"
               
        #await create_wallet(update, context)  # start creates wallet function
    elif query.data == "2":
        await start(update, context)  # show again message from bot help

    if query.data == "confirm_delete":
        # Delete wallet and record from base
        user_id = query.from_user.id
        wallet_name = f"{user_id}_wallet"  # wallet file name
        await delete_wallet_files(wallet_name)  # file deletion
        Session = init_db()
        with Session() as session:
            wallet_record = session.query(UserWallet).filter_by(user_id=user_id).first()
            wallet_deleted = delete_user_wallet_record(session, wallet_record)  # Delete record from database
            if wallet_deleted:
                await query.edit_message_text("Your wallet have been deleted. To create new one use /create_wallet.")

    elif query.data == "cancel_delete":
        await query.edit_message_text("Deletion cancelled.")

    if query.data == "q_restore":
        await query.message.reply_text("Please enter a password for your restored wallet:")       
        context.user_data['awaiting_password'] = True
        # await update.message.reply_text("Please enter your 25-word seed phrase for wallet restoration:")
        # context.user_data['awaiting_seed'] = True
        context.user_data['action'] = "restore_wallet"
    elif query.data == "q_rest_cancel":
        await query.edit_message_text("Wallet restore cancelled.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_input = update.message.text
    action = context.user_data.get('action')
    rpc_user = context.user_data.get('user_id')
    if action != "create_wallet" and action != "restore_wallet" :
        wallet = context.user_data.get('user_wallet')
        wallpsw = wallet.user_psw
    logger.info(f"now handle_message reached for user : {rpc_user}")
    await update.message.reply_text(f"handling your message...")
    # await update.message.reply_text(f"User found: {rpc_user}")

    if not rpc_user:
        await update.message.reply_text("User ID not found.")
        return

    if context.user_data.get('awaiting_password') and (action != "restore_wallet"):
        password_from_user = update.message.text
        await update.message.reply_text(action)
        message_id = update.message.message_id
        chat_id = update.message.chat_id

        # context.job_queue.run_once(lambda _: asyncio.create_task(delete_message(context, chat_id, message_id)), 5)
        asyncio.create_task(delete_messages(context, chat_id, [message_id]))
        await update.message.reply_text(f"Password received: ||{password_from_user}||", parse_mode="MarkdownV2")

        # Password check
        if action != "create_wallet" and action != "restore_wallet" :
            if password_from_user != wallpsw:
                await update.message.reply_text("Invalid password.")
                context.user_data['awaiting_password'] = False
                return
                
        # Remove waiting password state
        context.user_data['awaiting_password'] = False
        logger.info(f"Action password request finished with: {password_from_user}")

    # Run wallet creation procedure
    if action == "create_wallet":
        print("Reach create wallet item. Proceed with this...")
        logger.info(f" {rpc_user} now can create wallet...")

        # Create session for db transaction
        Session = init_db()
        with Session() as session: # Create instance of sesson
            # Create wallet via RPC-server
            wallet_created = await create_wallet_via_rpc(rpc_user, password_from_user)
            
            if wallet_created:
                # Add info about wallet to database
                wallet_name = f"{WALLET_DIR}/{rpc_user}_wallet"
                add2db_wallet(session, user_id=rpc_user, user_psw=hash_password(password_from_user), wallet_name=wallet_name)
                await update.message.reply_text("Wallet created successfully.")
            else:
                await update.message.reply_text("Failed to create wallet.")

    # restore wallet feature

    if action == "restore_wallet":
        if context.user_data.get('awaiting_password'):
            password_from_user = update.message.text
            context.user_data['password'] = password_from_user
            context.user_data['awaiting_password'] = False
            context.user_data['awaiting_seed'] = True
            await update.message.reply_text(f" {password_from_user} Password received. Now, please enter your 25-word seed phrase:")
            x = update.message.text
            context.user_data['seed_phrase'] = x
        # await update.message.reply_text(f" {password_from_user} Password received. Now, please enter your 25-word seed phrase:")
        # context.user_data['awaiting_seed'] = True
        
        
        if context.user_data.get('awaiting_seed'):
            x = update.message.text
            context.user_data['seed_phrase'] = x
            seed_phrase = context.user_data['seed_phrase']
            context.user_data['awaiting_seed'] = False
            context.user_data['awaiting_height'] = True
            await update.message.reply_text(f" {seed_phrase} Seed phrase received. Enter the block height to start synchronization from (or type '0' for the latest block):")
            return
        
        elif context.user_data.get('awaiting_height'):
            context.user_data['refresh_start_height'] = update.message.text if user_input.isdigit() else "0"
            refresh_start_height = context.user_data['refresh_start_height']
            await update.message.reply_text(f"Starting wallet restoration...from... {refresh_start_height}")

            # Starting the process of restoring wallet via RPC
            user_id = context.user_data['user_id']
            seed_phrase = context.user_data['seed_phrase']
            # password2 = context.user_data['password']
            password2 = password_from_user
            start_height = context.user_data['refresh_start_height']

            success = await restore_wallet_via_rpc(user_id, seed_phrase, password2, start_height)

            if success:
                session = Session()
                await add2db_wallet(session, user_id, hash_password(password2), f"{user_id}_wallet")
                await update.message.reply_text("Your wallet has been successfully restored and saved.")
            else:
                await update.message.reply_text("Failed to restore wallet. Please check your seed phrase and try again.")

            # Clear the data before the finishing the process...
            context.user_data.clear()
    # if action == "restore_wallet":
    #     # after password is entered
    #     if context.user_data.get('awaiting_password') == False:
    #         # Input seed phrase
    #         if context.user_data.get('awaiting_seed'):
    #            await update.message.reply_text("Please enter your 25-word seed phrase for wallet restoration:") 
    #            context.user_data['seed_phrase'] = user_input
    #            seed_phrase = context.user_data['seed_phrase']
    #            logger.info(f"Action seed phrase request finished with: {seed_phrase}")
    #            context.user_data['awaiting_seed'] = False
    #            return


    # if not (context.user_data.get('awaiting_password'))  and context.user_data.get('awaiting_seed') and context.user_data['action'] == "restore_wallet":
    #     await update.message.reply_text("Please enter your 25-word seed phrase for wallet restoration:")
    #     context.user_data['seed_phrase'] = user_input
    #     seed_phrase = context.user_data['seed_phrase']
    #     logger.info(f"Action seed phrase request finished with: {seed_phrase}")
    #     context.user_data['awaiting_seed'] = False
    #     # await update.message.reply_text("Please enter the block height to start synchronization from (or type '0' for the latest block):")
    #     context.user_data['awaiting_height'] = True
    #     return

    # if not (context.user_data.get('awaiting_seed')) and context.user_data.get('awaiting_height') and context.user_data['action'] == "restore_wallet":
    #     await update.message.reply_text("Please enter the block height to start synchronization from (or type '0' for the latest block):")
    #     context.user_data['refresh_start_height'] = user_input if user_input.isdigit() else "0"
    #     refresh_start_height = context.user_data['refresh_start_height']
    #     logger.info(f"Action refresh start height request finished with: {refresh_start_height}")
    #     context.user_data['awaiting_height'] = False
    #     # await update.message.reply_text("Please enter a password for your wallet:")
    #     # context.user_data['awaiting_password'] = True
    #     return

    # if not (context.user_data.get('awaiting_seed')) and not (context.user_data.get('awaiting_password')) and context.user_data['action'] == "restore_wallet":
    #     #user_password = user_input
    #     #context.user_data['awaiting_password'] = False

    #     # Launch restoring wallet via RPC
    #     user_id = context.user_data['user_id']
    #     seed_phrase = context.user_data['seed_phrase']
    #     refresh_start_height = context.user_data['refresh_start_height']
    #     logger.info(f"now restore proc from : {rpc_user}")
    #     logger.info(f"test properties of launch rpc instance: user_id: {user_id}, seed phrase: {seed_phrase}, start_height {refresh_start_height}")
    #     print(f"test properties of launch rpc instance: user_id: {user_id}, seed phrase: {seed_phrase}, start_height {refresh_start_height}")
    #     success = await restore_wallet_via_rpc(user_id, seed_phrase, password_from_user, refresh_start_height)

    #     if success:
    #         # Add wallet to DB
    #         session = Session()
    #         await add2db_wallet(session, user_id, password_from_user, f"{user_id}_wallet")
    #         await update.message.reply_text("Your wallet has been successfully restored and saved.")
    #     else:
    #         await update.message.reply_text("Failed to restore wallet. Please check your seed phrase and try again.")
        
    #     context.user_data.clear()   
    # restore wallet AI - actions
    # ==================================================================
    #      
    #     # await create_wallet(update, context, password_from_user)
    # elif context.user_data.get('awaiting_seed') and context.user_data['action'] == "restore_wallet":
    #     context.user_data['seed_phrase'] = user_input
    #     context.user_data['awaiting_seed'] = False

    #     # request from user block height for syncing
    #     await update.message.reply_text("Please enter the block height to start synchronization from (or type '0' for the latest block):")
    #     context.user_data['awaiting_height'] = True

    # elif context.user_data.get('awaiting_height') and context.user_data['action'] == "restore_wallet":
    #     refresh_start_height = user_input if user_input.isdigit() else "0"
    #     user_id = context.user_data['user_id']
    #     seed_phrase = context.user_data['seed_phrase']

    #     # Launch restoring process
    #     success = await restore_wallet_via_rpc(user_id, seed_phrase, refresh_start_height)
    #     if success:
    #         await update.message.reply_text("Your wallet has been successfully restored.")
    #     else:
    #         await update.message.reply_text("Failed to restore wallet. Please check your seed phrase and try again.")
        
    #     context.user_data.clear()    
    # elif action == "check_balance":
    #     #user_wallet = context.user_data.get('user_wallet')
    #     await check_balance(update, context, password_from_user)

    # elif action == 'get_recipient':
    #     # Check if password is matched
    #     if password_from_user != wallpsw:
    #         await update.message.reply_text("Invalid password.")
    #         context.user_data['awaiting_password'] = False  # Reset waiting state
    #         return
    #     await update.message.reply_text("Password accepted.")
    #     await update.message.reply_text("Please enter the recipient address:")
    #     context.user_data['action'] = 'wait_for_recipient'

    # # Now handle the recipient input
    # elif action == 'wait_for_recipient':
    #     recipient = update.message.text  # Capture the recipient from this input
    #     context.user_data['recipient'] = recipient
    #     await update.message.reply_text(f"recipient address: {recipient}")
    #     await update.message.reply_text("Please enter the to send (in Ryo):")
    #     context.user_data['action'] = 'get_amount'

    # elif action == 'get_amount':
    #     recipient = context.user_data.get('recipient')  # Retrieve recipient from context.user_data
    #     await update.message.reply_text(f"recipient address : {recipient}")
    #     balance = None  # Initialize balance to ensure it's defined in case of an error
    #     try:
    #         # amount = int(update.message.text) * 1e9
    #         # context.user_data['amount'] = amount
    #         # Convert the input amount to a float to handle decimal values
    #         amount = float(update.message.text) * 1e9  # Handle decimal values
    #         context.user_data['amount'] = int(amount)  # Convert to int for smallest unit            

    #         balance = await sf_check_balance(rpc_user, wallpsw)
    #         if balance < context.user_data['amount']:
    #             await update.message.reply_text("Insufficient balance.")
    #             return
    #         await update.message.reply_text(f"Do you want to send {amount / 1e9} Ryo to {context.user_data['recipient']}? Reply with 'yes' or 'no'.")
    #         context.user_data['action'] = 'confirm_send'
    #     except ValueError:
    #         if balance is not None:
    #             await update.message.reply_text(f"Found balance: {balance}")
    #         await update.message.reply_text(f"Desired amount2send: {amount}")
    #         await update.message.reply_text("Please enter a valid amount.")
    
    # elif action == 'confirm_send' and update.message.text.lower() == 'yes':
    #     await update.message.reply_text("Preparing to send funds...")
    #     await initiate_transfer(update, context)

    # elif action == 'approve_submission' and update.message.text.lower() == 'yes':
    #     await update.message.reply_text("Now sign your transaction...")
    #     tr2sign = context.user_data.get('tx_metadata')
    #     await sign_transaction(update, context, tr2sign)

    # elif action == 'confirm_submission' and update.message.text.lower() == 'yes':
    #     await submit_transaction(update, context)
 
    # else:
    #     await update.message.reply_text("Returned with:")
    #     await update.message.reply_text(action)
    #     await update.message.reply_text("Please use the menu to proceed.")
