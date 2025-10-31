import requests
import json
from typing import List, Dict
import logging
import datetime
from modules import config
from modules import validators


#FUNCTIONS

def alchemy_data_extract_token_transactions(
    token_address: str,
    max_transactions: int = 10,
    alchemy_api_key: str = config.ALCHEMY_API_KEY
    ) -> List[Dict]:
    """
    Get latest token transfer transactions for a given token using Alchemy Transfers API.
    
    This function uses the Alchemy Transfers API to retrieve the most recent token transfers
    for a specific token contract. The API provides enhanced blockchain data with better
    performance and additional metadata compared to direct RPC calls.
    
    Args:
        token_address (str): The contract address of the token
        max_transactions (int): Maximum number of transactions to return (default: 10)
        alchemy_api_key (str): Alchemy API key for authentication
    
    Returns:
        List[Dict]: List of transfer transaction data dictionaries containing token transfers
    """
    logging.info(f"alchemy_data.alchemy_data_extract_token_transactions: Initiating function call")

    # ===== INPUT VALIDATION SECTION =====
    
    # Set context for error messages (function name)
    context = "alchemy_data.alchemy_data_extract_token_transactions"
    
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
    is_valid, error_msg = validators.validate_api_key(alchemy_api_key, "Alchemy", context)
    if not is_valid:
        return []
    
    # ===== END VALIDATION SECTION =====
    logging.info(f"alchemy_data.alchemy_data_extract_token_transactions: Input validation completed")

    # Construct Alchemy API URL for Ethereum mainnet
    # Alchemy uses different endpoints for different networks
    alchemy_url = f"https://eth-mainnet.g.alchemy.com/v2/{alchemy_api_key}"
    
    # Alchemy has a limit of 0x3e8 (1000) transfers per request
    # Ensure max_transactions is within valid range and convert to hex
    if max_transactions > 1000:
        max_transactions = "0x3e8"
    else:
        max_transactions = hex(max_transactions)  # Minimum of 1 transfer

    # Prepare the JSON-RPC request payload for alchemy_getAssetTransfers
    # This uses Alchemy's enhanced Transfers API method to get asset transfers
    payload = {
        "jsonrpc": "2.0",
        "method": "alchemy_getAssetTransfers",
        "params": [{
            "fromBlock": "0x0",  # Start from genesis block
            "toBlock": "latest",  # End at the latest block
            "contractAddresses": [token_address],  # Token contract address to monitor
            "category": ["erc20", "erc721", "erc1155"],  # Token transfer categories
            "withMetadata": True,  # Include additional metadata
            "excludeZeroValue": True,  # Include zero value transfers
            "maxCount": max_transactions,  # Limit number of results (in hex format)
            "order": "desc"  # Order by block number in descending order
        }],
        "id": 1
    }
    
    try:
        # Make the HTTP POST request to Alchemy API using shared session for connection pooling
        # Alchemy uses POST requests with JSON-RPC payload
        response = config.shared_api_session.post(
            alchemy_url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=30  # 30 second timeout for the request
        )
        
        # Check if the HTTP request was successful
        response.raise_for_status()
        
        # Parse the JSON response from the API
        result = response.json()
        
        # Check for JSON-RPC errors in the response
        if "error" in result:
            error_message = result.get("error", {}).get("message", "Unknown error")
            logging.error(f"alchemy_data.alchemy_data_extract_token_transactions: Alchemy API Error: {error_message}")
            return []
        
        # Extract transfer data from the API response
        # The 'result' field contains the transfers object with transfers array
        transfers_data = result.get("result", {})
        transfers = transfers_data.get("transfers", [])
        
        # Return the transfers (already limited by maxCount parameter)
        return transfers
        
    except requests.exceptions.RequestException as e:
        logging.error(f"alchemy_data.alchemy_data_extract_token_transactions: Network error when calling Alchemy API: {e}")
        return []
    except json.JSONDecodeError as e:
        logging.error(f"alchemy_data.alchemy_data_extract_token_transactions: JSON decode error when parsing Alchemy response: {e}")
        return []
    except Exception as e:
        logging.error(f"alchemy_data.alchemy_data_extract_token_transactions: Unexpected error in alchemy_data_extract_token_transactions: {e}")
        return []

def alchemy_get_block_timestamp(block_number: str, alchemy_api_key: str = config.ALCHEMY_API_KEY) -> str:
    """
    Get the UTC timestamp for a given block number using Alchemy's eth_getBlockByNumber method.
    
    Args:
        block_number (str): Block number in hex format (e.g., "0x1041a59")
        alchemy_api_key (str): Alchemy API key for authentication
    
    Returns:
        str: UTC timestamp in format "YYYY-MM-DD HH:MM:SS UTC" or empty string if error
    """
    logging.info(f"alchemy_data.alchemy_get_block_timestamp: Getting block timestamp for {block_number}")
    
    try:
        # Construct Alchemy API URL
        alchemy_url = f"https://eth-mainnet.g.alchemy.com/v2/{alchemy_api_key}"
        
        # Prepare the JSON-RPC request payload for eth_getBlockByNumber
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_getBlockByNumber",
            "params": [block_number, False],  # False = only block header, not full block
            "id": 1
        }
        
        # Make the HTTP POST request to Alchemy API using shared session for connection pooling
        response = config.shared_api_session.post(
            alchemy_url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=30
        )
        
        # Check if the HTTP request was successful
        response.raise_for_status()
        
        # Parse the JSON response from the API
        result = response.json()
        
        # Check for JSON-RPC errors in the response
        if "error" in result:
            error_message = result.get("error", {}).get("message", "Unknown error")
            logging.error(f"alchemy_data.alchemy_get_block_timestamp: Alchemy API Error getting block timestamp: {error_message}")
            return ""
        
        # Extract timestamp from block data
        block_data = result.get("result", {})
        timestamp_hex = block_data.get("timestamp", "")
        
        if timestamp_hex:
            # Convert hex timestamp to integer, then to UTC datetime
            timestamp_int = int(timestamp_hex, 16)
            utc_timestamp = datetime.datetime.fromtimestamp(timestamp_int, datetime.timezone.utc)
            return utc_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')
        
        return ""
        
    except Exception as e:
        logging.error(f"alchemy_data.alchemy_get_block_timestamp: Error getting block timestamp for block {block_number}: {e}")
        return ""

def alchemy_data_transform(transfers: List[Dict]) -> List[Dict]:
    """
    Transform raw transfer data from Alchemy Transfers API into a simplified JSON format.
    
    This function extracts key information from Alchemy's transfer data and
    converts them into a more readable format with decoded addresses and amounts.
    The Alchemy Transfers API provides enhanced metadata including timestamps and formatted values.
    
    Args:
        transfers (List[Dict]): Raw transfer data from alchemy_data_extract_token_transactions
        
    Returns:
        List[Dict]: List of transformed transaction data with the following fields:
            - transactionHash: The hash of the transaction
            - blockTimestamp: UTC timestamp in format "YYYY-MM-DD HH:MM:SS UTC" (fetched from block data)
            - tokenAddress: Token contract address
            - fromAddress: Sender address
            - toAddress: Receiver address
            - transferAmount: Transfer amount (already formatted by Alchemy)
            - transferAmountFormatted: Human-readable transfer amount with commas
    """
    logging.info(f"alchemy_data.alchemy_data_transform: Initiating transformation of transactions")
    
    transformed_transactions = []
    
    for transfer in transfers:
        try:
            # Extract basic transfer information from Alchemy's enhanced data structure
            transaction_hash = transfer.get('hash', '')
            from_address = transfer.get('from', '')
            to_address = transfer.get('to', '')
            
            # Get transfer value (already formatted by Alchemy API)
            transfer_value = transfer.get('value', 0)
            
            # Get token contract address from rawContract if available
            raw_contract = transfer.get('rawContract', {})
            token_address = raw_contract.get('address', '')
            
            # Format transfer amount with commas for better readability
            transfer_amount_formatted = f"{transfer_value:,.2f}" if transfer_value else "0"
            
            # Get block number and convert to UTC timestamp
            block_number = transfer.get('blockNum', '')
            block_timestamp = ''
            if block_number:
                block_timestamp = alchemy_get_block_timestamp(block_number)
            
            # Create transformed transaction object with enhanced data from Alchemy
            transformed_transaction = {
                'transactionHash': transaction_hash,
                'blockTimestamp': block_timestamp if block_timestamp else f"Block {block_number}",  # Use UTC timestamp or fallback to block number
                'tokenAddress': token_address,
                'fromAddress': from_address,
                'toAddress': to_address,
                'transferAmount': str(transfer_value),  # Convert to string for consistency
                'transferAmountFormatted': transfer_amount_formatted,
            }
            
            transformed_transactions.append(transformed_transaction)
            
        except Exception as e:
            logging.error(f"alchemy_data.alchemy_data_transform: Error transforming transfer data: {e}")
            continue
    
    return transformed_transactions

def get_contract_address_by_symbol(token_symbol: str, alchemy_api_key: str = config.ALCHEMY_API_KEY) -> str:
    """
    Get the contract address for a given token symbol using Alchemy API.
    """
    logging.info(f"alchemy_data.get_contract_address_by_symbol: Getting contract address for {token_symbol}")
    
    #alchemy api call to get the contract address for a given token symbol
    alchemy_url = f"https://eth-mainnet.g.alchemy.com/v2/{config.ALCHEMY_API_KEY}"
    payload = {
        "jsonrpc": "2.0",
        "method": "alchemy_getTokenMetadata",
        "params": [token_symbol],
    }

    response = config.shared_api_session.post(alchemy_url, headers={"Content-Type": "application/json"}, data=json.dumps(payload))
    result = response.json()
    token_address = result.get("result", {}).get("address", "")

    logging.info(f"alchemy_data.get_contract_address_by_symbol: Contract address for {token_symbol} is {token_address}")
    return token_address


'''
#EXAMPLE
# Example token address (PEPE token on Ethereum mainnet)
token_address = "0x6982508145454Ce325dDbE47a25d4ec3d2311933"

# Get latest token transfer transactions using Alchemy Transfers API
transactions = alchemy_data_extract_token_transactions(
    token_address=token_address,
    max_transactions=1,  # Maximum number of transfers to return
    alchemy_api_key=config.ALCHEMY_API_KEY
)

print("Raw token transfer data from Alchemy Transfers API:")
print(json.dumps(transactions, indent=2))

# Transform the transfer data
transformed_transactions = alchemy_data_transform(transactions)
print("\nTransformed transactions:")
print(json.dumps(transformed_transactions, indent=2))
'''
