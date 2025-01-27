import logging, os
from logging.handlers import TimedRotatingFileHandler
from config import LOG_DIR, LOG_FILE, LOG_CONSOLE_FILE

# Setup logging configuration
def setup_logging():
    # log_file_path = os.path.join(LOG_DIR, LOG_FILE)
    log_file_path = os.path.join(os.getcwd(), LOG_DIR, LOG_FILE)
    console_log_file_path = os.path.join(os.getcwd(), LOG_DIR, LOG_CONSOLE_FILE)


    # Check if directory exists
    # print("check directory presence...")
    # print(LOG_DIR)
    # print(os.path)
    if not os.path.exists(os.path.dirname(log_file_path)):
        print("Create log dir if not exist:")
        print(os.path.dirname(log_file_path))
        os.makedirs(os.path.dirname(log_file_path))

    # if not os.path.exists(LOG_DIR):
    #     print("create directory:")
    #     print(LOG_DIR)
    #     os.makedirs(LOG_DIR)

    logger = logging.getLogger('TelegramBot')
    logger.setLevel(logging.DEBUG)

    # File handler with rotation
    file_handler = TimedRotatingFileHandler(log_file_path, when='midnight', interval=1)
    file_handler.suffix = "%Y-%m-%d"
    file_handler.setLevel(logging.INFO)

    console_file_handler = logging.FileHandler(console_log_file_path)
    console_file_handler.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_file_handler)
    logger.addHandler(console_handler)

    return logger
# def setup_logging():
#     logger = logging.getLogger('TelegramBot')
#     logger.setLevel(logging.DEBUG)
    
#     # File handler with rotation
#     file_handler = TimedRotatingFileHandler('logs/bot.log', when='midnight', interval=1)
#     file_handler.suffix = "%Y-%m-%d"
#     file_handler.setLevel(logging.INFO)
    
#     # Console handler
#     console_handler = logging.StreamHandler()
#     console_handler.setLevel(logging.DEBUG)

#     # Formatter
#     formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#     file_handler.setFormatter(formatter)
#     console_handler.setFormatter(formatter)

#     logger.addHandler(file_handler)
#     logger.addHandler(console_handler)

#     return logger
 
