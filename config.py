# Config.py stores all configuration settings 
# for RYO Telegram bot to centralize and simplify 
# the process of modifying values such as API tokens, 
# database settings, and RPC server configurations. 
import os

# Telegram Bot
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Ryo Wallet RPC
RPC_PORT = 18082
RPC_URL = f"http://localhost:{RPC_PORT}/json_rpc"
RPC_USER = "rpc_user"
RPC_PASSWORD = "rpc_password"
RPC_TIMEOUT = 30

# Database
DATABASE_URL = "sqlite:///data/wallets.db"
USER_DB_PATH = "data/users.db" 
WALLET_DIR = "./testwall"

# Logging
LOG_DIR = "logs"
LOG_FILE = f"{LOG_DIR}/bot.log"
LOG_LEVEL = "DEBUG"

#Currency default rates
RYO_BTC_RATE = 0.00000021
BTC_USD_RATE = 66870.00000008
RUB_USD_RATE = 96.7402
RYO_USD_RATE = 0.014
RYO_RUB_RATE = 1.358

# Timeouts and Delays
MESSAGE_DELETE_DELAY = 10
RPC_REQUEST_TIMEOUT = 10

# Security
MIN_PASSWORD_LENGTH = 8
USE_ENCRYPTION = True

# Bot Behavior
MESSAGE_PARSE_MODE = "MarkdownV2"
DEFAULT_REPLY_TIMEOUT = 30

# Celery
# CELERY_BROKER_URL = "pyamqp://guest@localhost//"
# CELERY_RESULT_BACKEND = "rpc://"

# Feature Toggles
ENABLE_WALLET_FEATURES = True
ENABLE_LOGGING = True
