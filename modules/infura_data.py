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

def infura_data_extract_token_transactions(
    token_address: str,
    max_transactions: int = 10,
    infura_api_key: str = config.INFURA_API_KEY
    ) -> List[Dict]:
    """
    Get the latest transactions for a given token using Infura API.
    
    Args:
        token_address (str): The contract address of the token
        infura_url (str): Infura API endpoint URL (e.g., 'https://mainnet.infura.io/v3/YOUR_PROJECT_ID')
        max_transactions (int): Maximum number of transactions to return (default: 10)
    
    Returns:
        List[Dict]: List of transaction data dictionaries
    """
    
    # ===== INPUT VALIDATION SECTION =====
    
    # Set context for error messages (function name)
    context = "infura_data.infura_data_extract_token_transactions"
    
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
    is_valid, error_msg = validators.validate_api_key(infura_api_key, "Infura", context)
    if not is_valid:
        return []
    
    # ===== END VALIDATION SECTION =====
    
    logging.info(f"infura_data.infura_data_extract_token_transactions: Extracting token transactions for {token_address} with max_transactions {max_transactions}")
    
    # construct infura url with api key
    infura_url = "https://mainnet.infura.io/v3/" + infura_api_key

    # First, get the latest block number
    try:
        payload_eth_getBlockNumber = {
                "jsonrpc": "2.0",
                "method": "eth_blockNumber",
                "params": [],
                "id": 1
        }
        
        eth_getBlockNumber_response = config.shared_api_session.post(
            infura_url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload_eth_getBlockNumber),
            timeout=30  # 30 second timeout
        )

        latest_block_number = int(eth_getBlockNumber_response.json()['result'], 16)

    except Exception as e:
        logging.error(f"infura_data.infura_data_extract_token_transactions: Error getting latest block number: {e}")
        latest_block_number = 0
        return latest_block_number

    # Prepare the JSON-RPC request payload
    # This uses eth_getLogs to get transfer events for the token
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getLogs",
        "params": [{
            "fromBlock": hex(latest_block_number - 100),  # infura does not support last transaction, so we need to retrieve 100 block from latest
            "toBlock": hex(latest_block_number),    # End at the latest block (convert to hex)
            "address": token_address,  # Token contract address
            "topics": [
                "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"  # Transfer event signature
            ]
        }],
        "id": 1
    }

    try:
        
        # Make the HTTP request to Infura using shared session for connection pooling
        response = config.shared_api_session.post(
            infura_url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=30  # 30 second timeout
        )
        
        # Check if request was successful
        response.raise_for_status()
        
        # Parse the JSON response
        result = response.json()
        
        # Check for JSON-RPC errors
        if "error" in result:
            logging.error(f"infura_data.infura_data_extract_token_transactions: Infura API Error: {result['error']}")
            return []
        
        # Extract transaction logs from the response
        logs = result.get("result", [])
        
        # get lates transaction from logs
        limited_logs = logs[-max_transactions:]
        
        logging.info(f"infura_data.infura_data_extract_token_transactions: Token transactions for {token_address} with max_transactions {max_transactions} done successfully")
        return limited_logs
        
    except requests.exceptions.RequestException as e:
        logging.error(f"infura_data.infura_data_extract_token_transactions: Network error: {e}")
        return []
    except json.JSONDecodeError as e:
        logging.error(f"infura_data.infura_data_extract_token_transactions: JSON decode error: {e}")
        return []
    except Exception as e:
        logging.error(f"infura_data.infura_data_extract_token_transactions: Unexpected error: {e}")
        return []


def infura_data_transform(transaction_logs: List[Dict]) -> List[Dict]:
    """
    Transform raw transaction logs from Infura into a simplified JSON format.
    
    This function extracts key information from Ethereum transfer event logs and
    converts them into a more readable format with decoded addresses and amounts.
    
    Args:
        transaction_logs (List[Dict]): Raw transaction logs from infura_data_extract_token_transactions
        
    Returns:
        List[Dict]: List of transformed transaction data with the following fields:
            - transactionHash: The hash of the transaction
            - blockTimestamp: Human-readable timestamp (YYYY-MM-DD HH:MM:SS)
            - address: Token contract address
            - data: Raw transfer amount data
            - fromAddress: Sender address (extracted from topics[1])
            - toAddress: Receiver address (extracted from topics[2])
            - transferAmount: Decoded transfer amount in wei
    """
    logging.info(f"infura_data.infura_data_transform: Initiating transformation of transactions")
    
    transformed_transactions = []
    
    for log in transaction_logs:
        try:
            # Extract basic transaction information
            transaction_hash = log.get('transactionHash', '')
            block_timestamp_hex = log.get('blockTimestamp', '')
            token_address = log.get('address', '')
            raw_data = log.get('data', '')
            topics = log.get('topics', [])
            
            # Skip malformed logs that are missing essential fields
            if not transaction_hash or not block_timestamp_hex or not token_address or not raw_data or not topics:
                continue
            
            # Convert hex timestamp to human-readable format in UTC
            # Remove '0x' prefix and convert hex to decimal, then to datetime
            human_timestamp = ''
            if block_timestamp_hex and block_timestamp_hex != '0x':
                timestamp_hex = block_timestamp_hex[2:] if block_timestamp_hex.startswith('0x') else block_timestamp_hex
                if timestamp_hex:
                    try:
                        # Convert hex to decimal timestamp
                        timestamp_decimal = int(timestamp_hex, 16)
                        # Convert Unix timestamp to human-readable datetime in UTC
                        # Use fromtimestamp with UTC timezone to ensure UTC timezone (modern approach)
                        human_timestamp = datetime.datetime.fromtimestamp(timestamp_decimal, datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                    except (ValueError, OSError):
                        # Handle invalid timestamp gracefully
                        human_timestamp = ''
            
            # Extract from and to addresses from topics
            # topics[0] is the event signature (Transfer event)
            # topics[1] is the from address (sender)
            # topics[2] is the to address (receiver)
            from_address = ''
            to_address = ''
            
            if len(topics) >= 3:
                # Remove '0x' prefix and leading zeros to get proper Ethereum address format
                from_address_raw = topics[1][2:] if topics[1].startswith('0x') else topics[1]
                to_address_raw = topics[2][2:] if topics[2].startswith('0x') else topics[2]
                
                # Remove leading zeros to get the actual address content
                # Ethereum addresses in topics are padded with zeros, we need to remove them
                from_address_clean = from_address_raw.lstrip('0')
                to_address_clean = to_address_raw.lstrip('0')
                
                # Ensure we have at least one character (in case address was all zeros)
                if not from_address_clean:
                    from_address_clean = '0'
                if not to_address_clean:
                    to_address_clean = '0'
                
                # Format as proper Ethereum addresses with '0x' prefix
                from_address = '0x' + from_address_clean
                to_address = '0x' + to_address_clean
            
            # Extract transfer amount from data field
            # The data field contains the transfer amount in wei (32 bytes = 64 hex chars)
            transfer_amount = '0'
            transfer_amount_formatted = '0'
            if raw_data and raw_data != '0x':
                # Remove '0x' prefix and convert to integer
                amount_hex = raw_data[2:] if raw_data.startswith('0x') else raw_data
                if amount_hex:
                    # Convert hex to decimal (this gives us the amount in wei)
                    amount_wei = int(amount_hex, 16)
                    transfer_amount = str(amount_wei)
                    
                    # Convert from wei to actual token amount
                    # Most ERC-20 tokens use 18 decimals, but USDC uses 6 decimals
                    # USDC contract address: 0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48
                    if token_address.lower() == '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48':
                        # USDC has 6 decimal places
                        amount_tokens = amount_wei / (10 ** 6)
                    else:
                        # Default to 18 decimal places for most ERC-20 tokens
                        amount_tokens = amount_wei / (10 ** 18)
                    
                    # Format with commas and appropriate decimal places
                    if amount_tokens == 0:
                        transfer_amount_formatted = "0"
                    else:
                        transfer_amount_formatted = f"{amount_tokens:,.2f}"
            
            # Create transformed transaction object
            transformed_transaction = {
                'transactionHash': transaction_hash,
                'blockTimestamp': human_timestamp,  # Now human-readable
                'address': token_address,
                #'data': raw_data,
                'fromAddress': from_address,
                'toAddress': to_address,
                'transferAmount': transfer_amount,  # Raw amount in wei
                'transferAmountFormatted': transfer_amount_formatted  # Human-readable amount with commas
            }
            
            transformed_transactions.append(transformed_transaction)
            logging.info(f"infura_data.infura_data_transform: Transaction {transaction_hash} transformed successfully")
        except Exception as e:
            logging.error(f"infura_data.infura_data_transform: Error transforming transaction log: {e}")
            # Continue processing other transactions even if one fails
            continue
    
    return transformed_transactions

'''
#EXAMPLE
# Replace with your actual Infura project URL
infura_url = "https://mainnet.infura.io/v3/" + config.INFURA_API_KEY

# Example token address (USDC on Ethereum mainnet)
token_address = "0x6982508145454Ce325dDbE47a25d4ec3d2311933"

# Get latest 2 transactions
transactions = infura_data_extract_token_transactions(
    token_address=token_address,
    infura_api_key=config.INFURA_API_KEY,
    max_transactions=1
)

print("Raw transactions:")
print(transactions)

# Transform the transactions
transformed_transactions = infura_data_transform(transactions)
print("\nTransformed transactions:")
print(json.dumps(transformed_transactions, indent=2))
    
'''