import requests
import json
from typing import List, Dict
import datetime
import logging
from modules import config
from modules import validators

# Note: Logging is configured centrally via config.setup_logging() 
# No need to call logging.basicConfig() here - it's called once at app startup

#FUNCTIONS

def etherscan_data_extract_token_transactions(
    token_address: str,
    max_transactions: int = 10,
    etherscan_api_key: str = config.ETHERSCAN_API_KEY
    ) -> List[Dict]:
    """
    Get token transfer events for a given token using Etherscan API v2 logs endpoint.
    
    This function uses the Etherscan API v2 logs endpoint to retrieve ERC-20 token transfer
    events (Transfer events) for a specific token contract within a block range.
    
    Args:
        token_address (str): The contract address of the token
        max_transactions (int): Maximum number of transactions to return (default: 1000)
        etherscan_api_key (str): Etherscan API key for authentication
    
    Returns:
        List[Dict]: List of log event data dictionaries containing token transfer events
    """
    
    # ===== INPUT VALIDATION SECTION =====
    
    # Set context for error messages (function name)
    context = "etherscan_data.etherscan_data_extract_token_transactions"
    
    # 1. Validate Ethereum address format
    is_valid, error_msg = validators.validate_ethereum_address(token_address, context)
    if not is_valid:
        return []
    
    # Convert token address to lowercase for consistency
    token_address = token_address.lower()
    
    # 2. Validate max_transactions is a positive integer
    is_valid, error_msg = validators.validate_positive_integer(max_transactions, min_value=1, context=context)
    if not is_valid:
        return []
    
    # 3. Validate API key exists
    is_valid, error_msg = validators.validate_api_key(etherscan_api_key, "Etherscan", context)
    if not is_valid:
        return []
    
    # ===== END VALIDATION SECTION =====
    
    logging.info(f"etherscan_data.etherscan_data_extract_token_transactions: Extracting token transactions for {token_address} with max_transactions {max_transactions}")
    
    # Construct Etherscan API v2 URL for logs endpoint
    etherscan_url = "https://api.etherscan.io/v2/api"
    
    # Prepare the API request parameters for logs endpoint
    params = {
        'chainid': 1,
        'module': 'account',
        'action': 'tokentx',
        'contractaddress': token_address,
        'page': 1,
        'offset': max_transactions,
        'sort': 'desc',
        'apikey': etherscan_api_key
    }


    try:
        # Make the HTTP GET request to Etherscan API v2 using shared session for connection pooling
        response = config.shared_api_session.get(
            etherscan_url,
            params=params,
            timeout=30  # 30 second timeout for the request
        )
        
        # Check if the HTTP request was successful
        response.raise_for_status()
        
        # Parse the JSON response from the API
        result = response.json()
        
        # Check for Etherscan API errors in the response
        if result.get("status") != "1":
            error_message = result.get("message", "Unknown error")
            logging.error(f"etherscan_data.etherscan_data_extract_token_transactions: Etherscan API Error: {error_message}")
            return []
        
        # Extract log events from the API response
        # The 'result' field contains the array of log events
        log_events = result.get("result", [])
        
        # Filter for ERC-20 Transfer events only
        # Transfer events have the signature: Transfer(address indexed from, address indexed to, uint256 value)
        transfer_events = []
        for event in log_events:
            # Check if this is a Transfer event by looking at the topics
            # Transfer event signature hash: 0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef
            if (event.get("topics") and 
                len(event.get("topics", [])) >= 3 and 
                event.get("topics", [])[0] == "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"):
                transfer_events.append(event)

        logging.info(f"etherscan_data.etherscan_data_extract_token_transactions: Token transactions for {token_address} with max_transactions {max_transactions} done successfully")
        return log_events

    except requests.exceptions.RequestException as e:
        logging.error(f"etherscan_data.etherscan_data_extract_token_transactions: Network error when calling Etherscan API: {e}")
        return []
    except json.JSONDecodeError as e:
        logging.error(f"etherscan_data.etherscan_data_extract_token_transactions: JSON decode error when parsing Etherscan response: {e}")
        return []
    except Exception as e:
        logging.error(f"etherscan_data.etherscan_data_extract_token_transactions: Unexpected error in etherscan_data_extract_token_transactions: {e}")
        return []

def etherscan_data_transform(token_transactions: List[Dict]) -> List[Dict]:
    """
    Transform raw token transaction data from Etherscan into a simplified JSON format.
    
    This function extracts key information from ERC-20 token transactions and
    converts them into a more readable format with decoded addresses and amounts.
    
    Args:
        token_transactions (List[Dict]): Raw token transaction data from etherscan_data_extract_token_transactions
        
    Returns:
        List[Dict]: List of transformed transaction data with the following fields:
            - transactionHash: The hash of the transaction
            - blockTimestamp: Human-readable timestamp (YYYY-MM-DD HH:MM:SS)
            - address: Token contract address
            - fromAddress: Sender address
            - toAddress: Receiver address
            - transferAmount: Transfer amount in wei
            - transferAmountFormatted: Human-readable transfer amount with commas
    """
    logging.info(f"etherscan_data.etherscan_data_transform: Initiating transformation of transactions")
    
    transformed_transactions = []
    
    for transaction in token_transactions:
        try:
            # Extract basic transaction information from token transaction structure
            transaction_hash = transaction.get('hash', '')
            block_timestamp = transaction.get('timeStamp', '')
            token_address = transaction.get('contractAddress', '')
            from_address = transaction.get('from', '')
            to_address = transaction.get('to', '')
            transfer_amount = transaction.get('value', '0')
            
            # Convert Unix timestamp to human-readable format
            human_timestamp = ''
            if block_timestamp:
                try:
                    # Convert timestamp to integer, then to datetime
                    timestamp_int = int(block_timestamp)
                    human_timestamp = datetime.datetime.fromtimestamp(timestamp_int, datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                except (ValueError, TypeError):
                    human_timestamp = 'Invalid timestamp'
            
            # Format transfer amount (assume 18 decimals for most ERC-20 tokens)
            transfer_amount_formatted = '0'
            if transfer_amount and transfer_amount != '0':
                try:
                    amount_wei = int(transfer_amount)
                    # Convert from wei to tokens (divide by 10^18)
                    amount_tokens = amount_wei / (10 ** 18)
                    transfer_amount_formatted = f"{amount_tokens:,.2f}"
                except (ValueError, TypeError):
                    transfer_amount_formatted = 'Invalid amount'
            
            # Create transformed transaction object
            transformed_transaction = {
                'transactionHash': transaction_hash,
                'blockTimestamp': human_timestamp,
                'address': token_address,
                'fromAddress': from_address,
                'toAddress': to_address,
                'transferAmount': transfer_amount,
                'transferAmountFormatted': transfer_amount_formatted
            }
            
            transformed_transactions.append(transformed_transaction)
            logging.info(f"etherscan_data.etherscan_data_transform: Transaction {transaction_hash} transformed successfully")

        except Exception as e:
            logging.error(f"etherscan_data.etherscan_data_transform: Error transforming log event: {e}")
            continue
    
    return transformed_transactions

def get_eth_logs_by_address(address: str) -> List[Dict]:
    """
    Get ETH logs from a given address.
    
    This function retrieves ETH logs for a specific address using the Etherscan API.
    It handles network errors, API errors, and JSON parsing errors gracefully.
    
    Args:
        address (str): The Ethereum address to get logs for
        
    Returns:
        List[Dict]: The first log entry from the result, or empty list if no logs found or error occurs
    """
    logging.info(f"etherscan_data.get_eth_logs_by_address: Getting ETH logs for {address}")
    etherscan_url = f"https://api.etherscan.io/v2/api"
    params = {
        'chainid': 1,
        'module': 'logs',
        'action': 'getLogs',
        'address': address,
        'apikey': config.ETHERSCAN_API_KEY,
        'page': 1,
        'offset': 1,
        'sort': 'desc',
    }

    try:
        # Make the HTTP GET request to Etherscan API using shared session for connection pooling
        response = config.shared_api_session.get(
            etherscan_url,
            params=params,
            timeout=30
        )

        # Check if the HTTP request was successful
        response.raise_for_status()

        # Parse the JSON response from the API
        result = response.json()

        # Check for Etherscan API errors in the response
        if result.get("status") != "1":
            error_message = result.get("message", "Unknown error")
            logging.error(f"etherscan_data.get_eth_logs_by_address: Etherscan API Error: {error_message}")
            return []

        # Get the result list and check if it's not empty before accessing the first element
        result_list = result.get("result", [])
        if not result_list:
            logging.warning(f"etherscan_data.get_eth_logs_by_address: No ETH logs found for address {address}")
            return []
        
        data = result_list[0]
        logging.info(f"etherscan_data.get_eth_logs_by_address: ETH logs for {address} done successfully")
        return data

    except requests.exceptions.RequestException as e:
        # Handle network errors (connection issues, timeouts, etc.)
        logging.error(f"etherscan_data.get_eth_logs_by_address: Network error when calling Etherscan API: {e}")
        return []
    except json.JSONDecodeError as e:
        # Handle JSON parsing errors
        logging.error(f"etherscan_data.get_eth_logs_by_address: JSON decode error when parsing Etherscan response: {e}")
        return []
    except Exception as e:
        # Handle any other unexpected errors
        logging.error(f"etherscan_data.get_eth_logs_by_address: Unexpected error in get_eth_logs_by_address: {e}")
        return []




# EXAMPLE USAGE (only runs when script is executed directly, not when imported)
if __name__ == "__main__":
    
    # Example token address (PEPE token on Ethereum mainnet)
    token_address = "0x6982508145454Ce325dDbE47a25d4ec3d2311933" #PEPE token
    transaction_hash = "0x3af38c5f6997ed002f0791eaa059112bf2fcad137f3b1652a9780162daf8c8d1"

    transactions = etherscan_data_extract_token_transactions(
        token_address=token_address,
        max_transactions=1,  # Maximum number of events to return
        etherscan_api_key=config.ETHERSCAN_API_KEY
    )

    print("Transactions: ", transactions)
    transformed_transactions = etherscan_data_transform(transactions)
    print("Transformed transactions: ", transformed_transactions)