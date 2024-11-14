# This module will handle communication with the 
# Ryo wallet RPC server. It includes a generic 
# RPCClient class to manage all requests to the 
# server.

# Main responsibilities:

#     Sending RPC requests.
#     Handling RPC responses and errors.
import subprocess
import os
import time
import requests
import aiohttp

from logger import setup_logging
from config import RPC_URL, RPC_PORT,WALLET_DIR

logger = setup_logging()

async def delete_wallet_files(wallet_name: str) -> None:
    wallet_path = os.path.join(WALLET_DIR, wallet_name)
    wallet_keys_path = wallet_path + ".keys"
    
    if os.path.exists(wallet_path):
        os.remove(wallet_path)
    if os.path.exists(wallet_keys_path):
        os.remove(wallet_keys_path)
        
async def create_wallet_via_rpc(rpc_user, password):
    # Setting up wallet name and URL RPC
    wallet_name = f"{rpc_user}_wallet"
    wallet_path = os.path.join(WALLET_DIR, wallet_name)
    loc_rpc_url = RPC_URL

    # Prepare request for wallet creation
    payload = {
        "jsonrpc": "2.0",
        "id": "0",
        "method": "create_wallet",
        "params": {
            "filename": wallet_name,
            "password": password,
            "language": "English"
        }
    }

    # async with aiohttp.ClientSession() as session:
    #     async with session.post(loc_rpc_url, json=payload) as response:
    #         if response.status == 200:
    #             result = await response.json()
    #             if result.get("result") == {}:  # Check for empty result
    #                 # Check, if the wallet created
    #                 if await wallet_exists(wallet_path):
    #                     return True  # Creation succes
    # return False  # Wallet was not created

    async with aiohttp.ClientSession() as session:
        async with session.post(loc_rpc_url, json=payload) as response:
            if response.status == 200:
                # Getting response text 
                text_response = await response.text()
                print("Response text from server:", text_response)  # output response text for diagnosis
                
                try:
                    # Trying decode response as  JSON, if possible
                    result = await response.json()
                    if result.get("result") == {}:  # check for empty result
                        # Checking creation of wallet 
                        if await wallet_exists(wallet_path):
                            return True  # successful creation
                except aiohttp.ContentTypeError:
                    print("Failed to parse JSON, received text/plain content.")
                    return False
            else:
                print("Request failed with status:", response.status)
                return False

async def restore_wallet_via_rpc(rpc_user, seed_phrase, password, refresh_start_height):
    wallet_name = f"{rpc_user}_wallet"
    wallet_path = os.path.join(WALLET_DIR, wallet_name)
    loc_rpc_url = RPC_URL

    payload = {
        "jsonrpc": "2.0",
        "id": "0",
        "method": "restore_wallet",
        "params": {
            "filename": wallet_name,
            "password": password,
            "seed": seed_phrase,
            "refresh_start_height": refresh_start_height
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(loc_rpc_url, json=payload) as response:
            if response.status == 200:
               # Getting response text 
                text_response = await response.text()
                print("Response text from server:", text_response)  # output response text for diagnosis                

                try:
                    # Trying decode response as  JSON, if possible
                    result = await response.json()
                    if result.get("result") == {}:  # check for empty result
                        # Checking creation of wallet 
                        if await wallet_exists(wallet_path):
                            return True  # successful creation
                except aiohttp.ContentTypeError:
                    print("Failed to parse JSON, received text/plain content.")
                    return False
            else:
                print("Request failed with status:", response.status)
                return False

            #     result = await response.json()
            #     # Checking, if the wallet created
            #     if result.get("result") == {} and await wallet_exists(wallet_path):
            #         return True
            # return False
        
async def wallet_exists(wallet_path):
    # Checking, if the wallet exists
    return os.path.exists(wallet_path)

def start_wallet_rpc():
    """Function to start the ryo-wallet-rpc server."""
    # wallet_dir = "./testwall"  # Path to your wallet directory
    command = f"./ryo-wallet-rpc --rpc-bind-port {RPC_PORT} --disable-rpc-login --wallet-dir {WALLET_DIR}"
    
    if not os.path.exists(WALLET_DIR):
        os.makedirs(WALLET_DIR)
        logger.info(f"Created wallet directory at {WALLET_DIR}")

    try:
        # Start the wallet server process
        logger.info(f"Starting wallet server with command: {command}")
        process = subprocess.Popen(command, shell=True)
        logger.info("Wallet server started.")
        return process
    except Exception as e:
        logger.error(f"Error starting wallet server: {e}")

def is_wallet_running():
    """Function to check if the wallet server is running."""
    try:
        # Check if the wallet RPC server is responding (on localhost by default)
        response = requests.get(f"http://localhost:{RPC_PORT}/json_rpc", timeout=2)
        if response.status_code == 200:
            logger.info("Wallet server is running.")
            return True
    except requests.ConnectionError:
        logger.warning("Wallet server is not running.")
    return False

def call_rpc(method, params):
    logger.debug(f"Calling RPC method: {method} with params: {params}")
    # RPC logic here

    