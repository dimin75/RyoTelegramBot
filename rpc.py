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
from requests.auth import HTTPDigestAuth
import aiohttp
import asyncio
import json

from logger import setup_logging
from config import RPC_URL, RPC_PORT,WALLET_DIR, LOG_WALLET

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

async def open_wallet_rpc(rpc_user, password):
    lrpc_user = rpc_user
    user_wall_name = f"{lrpc_user}_wallet"
    rpc_password = password
    url = f"http://127.0.0.1:{RPC_PORT}/json_rpc"
    headers = {"Content-Type": "application/json"}
    data_open_file = {
        "jsonrpc": "2.0",
        "id": "0",
        "method": "open_wallet",
        "params": {
          "filename": user_wall_name,
          "password": rpc_password
        }
    }
    try:
        logger.info(f"Request on opening the {user_wall_name}")
        response_open = requests.post(url, json=data_open_file, headers=headers, auth=HTTPDigestAuth(rpc_user, rpc_password))

        await asyncio.sleep(1)  
        result = response_open.json()
        logger.info(f"result of wallet opening: {result}")
        if 'error' in result:
            logger.error(f"Error opening wallet: {result['error']['message']}")
            return False
        logger.info("Wallet opened successfully.")
        return True        
    except Exception as e:        
       logger.error(f"Exception during wallet opening: {str(e)}")
       print(f"Error parsing JSON response: {response_open.text}")
       return False

    if 'error' in result:
        logger.info(f"Error opening wallet: {result['error']['message']}")

async def close_wallet_rpc(rpc_user, password):
    lrpc_user = rpc_user
    user_wall_name = f"{lrpc_user}_wallet"
    rpc_password = password
    url = f"http://127.0.0.1:{RPC_PORT}/json_rpc"
    headers = {"Content-Type": "application/json"}
    data_close_file = {
        "jsonrpc": "2.0",
        "id": "0",
        "method": "close_wallet",
        "params": {
          "filename": user_wall_name,
          "password": rpc_password
        }
    }        
    try:
        logger.info(f"Request on opening the {user_wall_name}")
        response_close = requests.post(url, json=data_close_file, headers=headers, auth=HTTPDigestAuth(rpc_user, rpc_password))

        await asyncio.sleep(1)  
        result = response_close.json()
        logger.info(f"result of wallet closing: {result}")
        return True
    except Exception as e:
       logger.error(f"Exception during wallet closing: {str(e)}")
       print(f"Error parsing JSON response: {response_close.text}")
       return False

    # if 'error' in result:
    #     logger.info(f"Error closing wallet: {result['error']['message']}")

async def send_coins_rpc(rpc_amount, rpc_address, rpc_user, rpc_password):
    url = f"http://127.0.0.1:{RPC_PORT}/json_rpc"
    headers = {"Content-Type": "application/json"}
    params_send = {
        "jsonrpc": "2.0",
        "method": "transfer",
        "params": {
            "destinations": [{"amount": rpc_amount, "address": rpc_address}],
            "mixin": 5,  # amount of mixins
            "get_tx_key": True,
            "get_tx_metadata": True,
            "do_not_relay": True  #create, but not send
        },
        "id": "0"
    }
    try:

        # await update.message.reply_text("Send Ryo to recipient...")
        logger.info(f"Send Ryo to recipient...: {rpc_user}")
        response = requests.post(url, json=params_send, headers=headers, auth=HTTPDigestAuth(rpc_user, rpc_password))

        await asyncio.sleep(1)

        logger.info(f"RPC send. Response status code: {response.status_code}")
        logger.info(f"Response text: {response.text}")

        # Check if the response status code indicates success
        if response.status_code != 200:
            #await update.message.reply_text(f"Error: received status code {response.status_code}")
            logger.info(f"Error: received status code {response.status_code}")
            session.close()
            return

        # Check if the response body is empty or invalid
        if not response.text:
            #await update.message.reply_text("Error: Empty response from the wallet RPC.")
            logger.info(f"Error: Empty response from the wallet RPC.")
            session.close()
            return

        result = response.json()

        logger.info(f"Response JSON: {json.dumps(result, indent=4)}")

        if 'error' in result:
            #await update.message.reply_text(f"Error initiating transfer: {result['error']['message']}")
            logger.info(f"Error initiating transfer: {result['error']['message']}")
        else:
        # Storing tx_metadata for the future signing
            # context.user_data['unsigned_txset'] = result.get('result', {}).get('unsigned_txset')
            context.user_data['tx_metadata'] = result.get('result', {}).get('tx_metadata')
            fee = result.get('result', {}).get('fee') / 1e9  # Comission in RYO
            tr2sign = context.user_data.get('tx_metadata')
            #await update.message.reply_text(f"Tx metadata: {tr2sign[:20]} ...")
            #await update.message.reply_text(f"Transfer initiated. The network fee is {fee} Ryo.")
            logger.info(f"Tx metadata: {tr2sign[:20]} ...")
            logger.info(f"Transfer initiated. The network fee is {fee} Ryo.")
            #await update.message.reply_text(f"Transfer initiated. The network fee is {fee} Ryo. Do you want to proceed? Reply with 'yes' or 'no'.")
            #context.user_data['action'] = 'approve_submission'
    except requests.exceptions.RequestException as e:
        # Log of exception
        logger.error(f"Error making the RPC request: {str(e)}")
        #await update.message.reply_text(f"Error making the RPC request: {str(e)}")

    except json.decoder.JSONDecodeError as e:
        # Log of error decoding JSON
        logger.error(f"Error parsing JSON response: {str(e)}")
        #await update.message.reply_text(f"Error parsing JSON response: {str(e)}")

async def submit_transaction_rpc(rpc_user, rpc_password):
    tx_metadata = context.user_data.get('tx_metadata')
    #rpc_user = context.user_data.get('rpc_id')
    #rpc_password = context.user_data.get('rpc_psw')
    url = f"http://127.0.0.1:{RPC_PORT}/json_rpc"
    headers = {"Content-Type": "application/json"}
    params_submit = {
        "jsonrpc": "2.0",
        "method": "submit_transfer",
        "params": {
            "tx_data_hex": tx_metadata
        },
        "id": "0"
    }

    try:
        # response = requests.post(WALLET_RPC_URL, json=params, headers=HEADERS)
        response = requests.post(url, json=params_submit, headers=headers, auth=HTTPDigestAuth(rpc_user, rpc_password))

        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response text: {response.text}")

        # Check if the response status code indicates success
        if response.status_code != 200:
            #await update.message.reply_text(f"Error: received status code {response.status_code}")
            logger.info(f"Error: received status code {response.status_code}")
            # session.close()
            return

        # Check if the response body is empty or invalid
        if not response.text:
            logger.info(f"Error: Empty response from the wallet RPC.")
            #await update.message.reply_text("Error: Empty response from the wallet RPC.")
            # session.close()
            return

        result = response.json()

        logger.info(f"Response JSON: {json.dumps(result, indent=4)}")

        # result = response.json()

        if 'error' in result:
            logger.info(f"Transaction: {signed_txset}")
            logger.info(f"Error submitting transaction: {result['error']['message']}")
            #await update.message.reply_text(f"Transaction: {signed_txset}")
            #await update.message.reply_text(f"Error submitting transaction: {result['error']['message']}")
        else:
            tx_hash_list = result.get('result', {}).get('tx_hash_list')
            logger.info(f"Transaction submitted successfully! Tx Hash: {tx_hash_list[0]}")
            context.user_data['tx_hash_final'] = tx_hash_list[0]
            #await update.message.reply_text(f"Transaction submitted successfully! Tx Hash: {tx_hash_list[0]}")

    except requests.exceptions.RequestException as e:
        # Log of exception
        logger.error(f"Error making the RPC request: {str(e)}")
        logger.info(f"Error making the RPC request: {str(e)}")
        #await update.message.reply_text(f"Error making the RPC request: {str(e)}")

    except json.decoder.JSONDecodeError as e:
        # Log of error decoding JSON
        logger.error(f"Error parsing JSON response: {str(e)}")
        #await update.message.reply_text(f"Error parsing JSON response: {str(e)}")

    finally:
        logger.error(f"Submit transaction over")
        #await update.message.reply_text(f"Submit transaction over")

async def get_seed_mnemonic_rpc(rpc_user, rpc_password):
    url = f"http://127.0.0.1:{RPC_PORT}/json_rpc"
    headers = {"Content-Type": "application/json"}
    data_addr = {
        "jsonrpc": "2.0",
        "id": "0",
        "method": "query_key",
        "params": {
          "key_type": "mnemonic"
        }
    }
    try:
        logger.info(f"Request of wallet seed mnemonic for: {rpc_user}")
        response_address = requests.post(url, json=data_addr, headers=headers, auth=HTTPDigestAuth(rpc_user, rpc_password))

        await asyncio.sleep(1)  
        result = response_address.json()
        logger.info(f"result of wallet address requesting: {result}")     
        if 'error' in result:
            logger.error(f"Error requesting wallet address: {result['error']['message']}")
            return None
        # Return first address in list
        # return result["result"]["addresses"][0]["address"]
        # Extract and return all addresses in the list
        seed = result.get('result', {}).get('key')
        return seed
        # addresses = [addr["address"] for addr in result["result"]["addresses"]]
        # return addresses        
    except Exception as e:    
      logger.error(f"Exception during address request: {str(e)}")
      print(f"Error parsing JSON response: {response_address.text}")
      return None

    if 'error' in result:
        logger.info(f"Error wallet address requesting: {result['error']['message']}")

async def get_address_wallet_rpc(rpc_user, rpc_password):
    url = f"http://127.0.0.1:{RPC_PORT}/json_rpc"
    headers = {"Content-Type": "application/json"}
    data_addr = {
        "jsonrpc": "2.0",
        "id": "0",
        "method": "get_address",
        "params": {
          "account_index": 0,
          "address_index": [0,1,2,3,4]
        }
    }
    try:
        logger.info(f"Request of wallet address for: {rpc_user}")
        response_address = requests.post(url, json=data_addr, headers=headers, auth=HTTPDigestAuth(rpc_user, rpc_password))

        await asyncio.sleep(1)  
        result = response_address.json()
        logger.info(f"result of wallet address requesting: {result}")     
        if 'error' in result:
            logger.error(f"Error requesting wallet address: {result['error']['message']}")
            return None
        # Return first address in list
        # return result["result"]["addresses"][0]["address"]
        # Extract and return all addresses in the list
        addresses = [addr["address"] for addr in result["result"]["addresses"]]
        return addresses        
        # seed = result.get('result', {}).get('key')
        # return seed
    except Exception as e:    
      logger.error(f"Exception during address request: {str(e)}")
      print(f"Error parsing JSON response: {response_address.text}")
      return None

    if 'error' in result:
        logger.info(f"Error wallet address requesting: {result['error']['message']}")

async def get_balance_wallet_rpc(rpc_user, rpc_password):
    url = f"http://127.0.0.1:{RPC_PORT}/json_rpc"
    headers = {"Content-Type": "application/json"}
    data_get_balance = {
        "jsonrpc": "2.0",
        "id": "0",
        "method": "get_balance",
        "params": {
            "account_index": 0,
            "address_indices": [0,1,2,3,4]  # address indexes which is planned to get
        }
    } 
    try:
        logger.info(f"Request of wallet balance for: {rpc_user}")
        response_balance = requests.post(url, json=data_get_balance, headers=headers, auth=HTTPDigestAuth(rpc_user, rpc_password))

        await asyncio.sleep(1)  
        result = response_balance.json()
        logger.info(f"result of wallet balance request: {result}")        
    except ValueError:    
      print(f"Error parsing JSON response: {response_balance.text}")
      return "Error", response_balance.text

    if 'error' in result:
        #await update.message.reply_text(f"Error getting balance: {result['error']['message']}")
        logger.info(f"Error of wallet balance request: {result['error']['message']}")
        return "Error", result['error']['message']
    else:
        balance = result.get('result', {}).get('balance')
        unlocked_balance = result.get('result', {}).get('unlocked_balance')
        return balance, unlocked_balance
    




async def wallet_exists(wallet_path):
    # Checking, if the wallet exists
    return os.path.exists(wallet_path)

def start_wallet_rpc():
    """Function to start the ryo-wallet-rpc server."""
    # wallet_dir = "./testwall"  # Path to your wallet directory
    command = f"./ryo-wallet-rpc --rpc-bind-port {RPC_PORT} --disable-rpc-login --wallet-dir {WALLET_DIR} --log-file {LOG_WALLET}"
    
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

    
