import requests
import json
from typing import List, Dict
import datetime
import pandas as pd
import logging
from modules import config
from modules.config import OHLC_DIR
from modules import validators

# Note: Logging is configured centrally via config.setup_logging() 
# No need to call logging.basicConfig() here - it's called once at app startup

def moralis_data_extract_token_transactions(
    token_address: str,
    max_transactions: int = 10,
    moralis_api_key: str = config.MORALIS_API_KEY
    ) -> List[Dict]:
    """
    Get the latest token transfer transactions for a given token using Moralis API.
    
    This function uses the Moralis Token Transfers API to retrieve the most recent token transfers
    for a specific token contract. The API provides enhanced blockchain data with better
    performance and additional metadata compared to direct RPC calls.
    
    Args:
        token_address (str): The contract address of the token
        max_transactions (int): Maximum number of transactions to return (default: 10)
        moralis_api_key (str): Moralis API key for authentication
    
    Returns:
        List[Dict]: List of transfer transaction data dictionaries containing token transfers
    """
    
    # ===== INPUT VALIDATION SECTION =====
    
    # Set context for error messages (function name)
    context = "moralis_data.moralis_data_extract_token_transactions"
    
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
    is_valid, error_msg = validators.validate_api_key(moralis_api_key, "Moralis", context)
    if not is_valid:
        return []
    
    # ===== END VALIDATION SECTION =====
    
    logging.info(f"moralis_data.moralis_data_extract_token_transactions: Extracting token transactions for {token_address} with max_transactions {max_transactions}")
    
    # Construct Moralis API URL for token transfers
    url = f"https://deep-index.moralis.io/api/v2.2/erc20/{token_address}/transfers"
    
    params = {
        "chain": "eth",
        "order": "DESC",
        "limit": max_transactions
    }   
    
    headers = {
        "Accept": "application/json",
        "X-API-Key": moralis_api_key
    }
    
    try:
        # Use shared session for connection pooling (faster, reuses TCP connections)
        response = config.shared_api_session.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        # Check for Moralis API errors
        if "error" in result:
            error_message = result.get("error", {}).get("message", "Unknown error")
            logging.error(f"moralis_data.moralis_data_extract_token_transactions: No results found from Moralis API: {error_message}")
            return []
        
        logging.info(f"moralis_data.moralis_data_extract_token_transactions: Token transactions for {token_address} with max_transactions {max_transactions} done successfully")
        return result
        
    except requests.exceptions.RequestException as e:
        logging.error(f"moralis_data.moralis_data_extract_token_transactions: Network error when calling Moralis API: {e}")
        return []
    except json.JSONDecodeError as e:
        logging.error(f"moralis_data.moralis_data_extract_token_transactions: JSON decode error when parsing Moralis response: {e}")
        return []
    except Exception as e:
        logging.error(f"moralis_data.moralis_data_extract_token_transactions: Unexpected error in moralis_data_extract_token_transactions: {e}")
        return []

def moralis_data_transform(transactions: List[Dict]) -> List[Dict]:
    """
    Transform raw transaction data from Moralis API into a simplified JSON format.
    
    This function extracts key information from Moralis transaction data and
    converts them into a more readable format with decoded addresses and amounts.
    The Moralis API provides enhanced metadata including timestamps and formatted values.
    
    Args:
        transactions (List[Dict]): Raw transaction data from moralis_data_extract_token_transactions
        
    Returns:
        List[Dict]: List of transformed transaction data with the following fields:
            - transactionHash: The hash of the transaction
            - blockTimestamp: UTC timestamp in format "YYYY-MM-DD HH:MM:SS UTC"
            - tokenAddress: Token contract address
            - fromAddress: Sender address
            - toAddress: Receiver address
            - transferAmount: Transfer amount (raw value)
            - transferAmountFormatted: Human-readable transfer amount with commas
    """

    logging.info(f"moralis_data.moralis_data_transform: Initiating transformation of transactions")

    transformed_transactions = []
    
    # Handle the Moralis API response structure
    # The API returns a dict with 'result' key containing the transactions array
    if isinstance(transactions, dict) and 'result' in transactions:
        transaction_list = transactions['result']
    elif isinstance(transactions, list):
        transaction_list = transactions
    else:
        logging.error(f"moralis_data.moralis_data_transform: Invalid transaction data format")
        raise ValueError()
    
    for transaction in transaction_list:
        try:
            # Extract basic transaction information from Moralis ERC20 transfer data structure
            transaction_hash = transaction.get('transaction_hash', '')
            from_address = transaction.get('from_address', '')
            to_address = transaction.get('to_address', '')
            
            # Get token transfer amount (ERC20 token amount, not ETH)
            transfer_value = transaction.get('value', '0')
            
            # Get token contract address
            token_address = transaction.get('address', '')
            
            # Get token decimals for proper formatting
            token_decimals = transaction.get('decimals', 18)  # Default to 18 decimals
            
            # Skip transactions with missing required fields
            if not transaction_hash or not from_address or not to_address or not token_address:
                logging.warning(f"moralis_data.moralis_data_transform: Skipping transaction with missing required fields: {transaction}")
                continue
            
            # Convert transfer value from raw token units to actual token amount
            transfer_amount_formatted = '0'
            if transfer_value and transfer_value != '0':
                try:
                    amount_raw = int(transfer_value)
                    # Convert from raw token units to actual tokens (divide by 10^decimals)
                    amount_tokens = amount_raw / (10 ** token_decimals)
                    transfer_amount_formatted = f"{amount_tokens:,.2f}"
                except (ValueError, TypeError):
                    transfer_amount_formatted = 'Invalid amount'
            
            # Get block timestamp and convert to UTC format
            block_timestamp = transaction.get('block_timestamp', '')
            human_timestamp = ''
            if block_timestamp:
                try:
                    # Parse ISO format timestamp and convert to UTC format
                    # Moralis returns: "2025-10-15T20:04:23.000Z"
                    dt = datetime.datetime.fromisoformat(block_timestamp.replace('Z', '+00:00'))
                    human_timestamp = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
                except (ValueError, TypeError):
                    human_timestamp = 'Invalid timestamp'
            
            # Create transformed transaction object
            transformed_transaction = {
                'transactionHash': transaction_hash,
                'blockTimestamp': human_timestamp,
                'tokenAddress': token_address,
                'fromAddress': from_address,
                'toAddress': to_address,
                'transferAmount': str(transfer_value),  # Convert to string for consistency
                'transferAmountFormatted': transfer_amount_formatted,
            }
            
            transformed_transactions.append(transformed_transaction)
            logging.info(f"moralis_data.moralis_data_transform: Transaction {transaction_hash} transformed successfully")

        except Exception as e:
            logging.error(f"moralis_data.moralis_data_transform: Error transforming transaction data: {e}")
            continue
    
    return transformed_transactions

def get_token_address(symbol: str, chain: str = 'ethereum') -> str:
    """Fetch contract address from CoinGecko (free)."""
    
    # ===== INPUT VALIDATION SECTION =====
    
    # Set context for error messages (function name)
    context = "moralis_data.get_token_address"
    
    # Validate symbol is a non-empty string
    is_valid, error_msg = validators.validate_string(symbol, allow_empty=False, context=context)
    if not is_valid:
        return None
    
    # Validate chain is a non-empty string
    is_valid, error_msg = validators.validate_string(chain, allow_empty=False, context=context)
    if not is_valid:
        return None
    
    # ===== END VALIDATION SECTION =====
    
    logging.info(f"moralis_data.get_token_address: Fetching token address with {symbol}")
    try:
        # Step 1: Search symbol and return coingecko id
        search_url = f"https://api.coingecko.com/api/v3/search?query={symbol.lower()}"
        search_response = config.shared_api_session.get(search_url).json()
        if not search_response['coins']:
            return None
        coin_id = search_response['coins'][0]['id']  # Top match - highest by marketcap

        logging.info(f"moralis_data.get_token_address: CoinGecko ID for {symbol} is {coin_id}")
        # Step 2: Get token address given coingecko coin id
        details_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
        details = config.shared_api_session.get(details_url).json()
        address = details['platforms'].get(chain, None)

        logging.info(f"moralis_data.get_token_address: Token address for {symbol} is {address}")
        return address
    except requests.exceptions.RequestException as e:
        logging.error(f"moralis_data.get_token_address: Network error when calling CoinGecko API: {e}")
        return None

def get_token_price(token_address: str, chain: str = 'eth') -> float:
    
    # ===== INPUT VALIDATION SECTION =====
    
    # Set context for error messages (function name)
    context = "moralis_data.get_token_price"
    
    # Validate Ethereum address format
    is_valid, error_msg = validators.validate_ethereum_address(token_address, context)
    if not is_valid:
        raise ValueError(f"moralis_data.get_token_price: {error_msg}")
    
    # Convert token address to lowercase for consistency
    token_address = token_address.lower()
    
    # Validate chain is a non-empty string
    is_valid, error_msg = validators.validate_string(chain, allow_empty=False, context=context)
    if not is_valid:
        raise ValueError(f"moralis_data.get_token_price: {error_msg}")
    
    # Validate API key exists
    is_valid, error_msg = validators.validate_api_key(config.MORALIS_API_KEY, "Moralis", context)
    if not is_valid:
        raise ValueError(f"moralis_data.get_token_price: {error_msg}")
    
    # ===== END VALIDATION SECTION =====
    
    logging.info(f"moralis_data.get_token_price: Fetching token price for {token_address}")

    url = f"https://deep-index.moralis.io/api/v2.2/erc20/{token_address}/price"

    headers = {
    "Accept": "application/json",
    "X-API-Key": config.MORALIS_API_KEY
    }

    params = {
        "chain": chain,
        "min_pair_side_liquidity_usd": 100000
    }
    try:
        response = requests.request("GET", url, headers=headers, params=params)
        response.raise_for_status()
        price_usd = response.json().get("usdPrice")
        price_24hr_percent_change = response.json().get("24hrPercentChange")
        if price_usd:
            logging.info(f"moralis_data.get_token_price: Token price for {token_address} is {price_usd}")
            logging.info(f"moralis_data.get_token_price: 24hr percent change for {token_address} is {price_24hr_percent_change}")
            return price_usd, price_24hr_percent_change
        else:
            raise ValueError(f"moralis_data.get_token_price: No price found for {token_address}")
    except Exception as e:
        raise ValueError(f"moralis_data.get_token_price: {e}")

def get_best_pair_address(
    token_address: str,
    chain: str = 'eth',
    api_key: str = config.MORALIS_API_KEY
    ) -> str:
    """
    Retrieves trading pairs for the token and selects the one with the highest liquidity.
    
    Args:
        token_address (str): The token's contract address.
        chain (str): Blockchain chain (e.g., 'eth', 'bsc'). Default: 'eth'.
        api_key (str): Your Moralis API key.
    
    Returns:
        str: The pair address with the highest liquidity in USD.
    
    Raises:
        ValueError: If no pairs found or no valid liquidity.
        requests.RequestException: On network/API errors.
    """
    
    # ===== INPUT VALIDATION SECTION =====
    
    # Set context for error messages (function name)
    context = "moralis_data.get_best_pair_address"
    
    # Validate Ethereum address format
    is_valid, error_msg = validators.validate_ethereum_address(token_address, context)
    if not is_valid:
        raise ValueError(f"moralis_data.get_best_pair_address: {error_msg}")
    
    # Convert token address to lowercase for consistency
    token_address = token_address.lower()
    
    # Validate chain is a non-empty string
    is_valid, error_msg = validators.validate_string(chain, allow_empty=False, context=context)
    if not is_valid:
        raise ValueError(f"moralis_data.get_best_pair_address: {error_msg}")
    
    # Validate API key exists
    if not api_key:
        raise ValueError("moralis_data.get_best_pair_address: API key is required. Get one from moralis.io")
    
    # ===== END VALIDATION SECTION =====
    
    logging.info(f"moralis_data.get_best_pair_address: Fetching best pair address for {token_address} on chain {chain}")
    
    base_url = "https://deep-index.moralis.io/api/v2.2"
    headers = {
        "accept": "application/json",
        "X-API-Key": api_key
    }
    
    pairs_url = f"{base_url}/erc20/{token_address}/pairs"
    params = {
        "chain": chain,
        "limit": 1  # Top pairs
    }
    response = config.shared_api_session.get(pairs_url, headers=headers, params=params)
    response.raise_for_status()
    pairs_data = response.json()
    
    logging.info(f"moralis_data.get_best_pair_address: Pairs data for {token_address} on chain {chain}")

    if not pairs_data.get("pairs"):
        logging.error(f"moralis_data.get_best_pair_address: No trading pairs found for token address '{token_address}' on chain '{chain}'")
        raise ValueError(f"moralis_data.get_best_pair_address: No trading pairs found for token address '{token_address}' on chain '{chain}'")
    
    max_liquidity = 0
    pair_address = None
    for pair in pairs_data["pairs"]:
        liquidity_usd = float(pair.get("liquidity_usd", 0))
        if liquidity_usd > max_liquidity:
            max_liquidity = liquidity_usd
            pair_address = pair["pair_address"]
    
    if not pair_address:
        logging.error(f"moralis_data.get_best_pair_address: No valid pair with liquidity found for {token_address} on chain {chain}")
        raise ValueError("moralis_data.get_best_pair_address: No valid pair with liquidity found")

    logging.info(f"moralis_data.get_best_pair_address: Best pair (liquidity) address for {token_address} is {pair_address}")
    return pair_address

def fetch_ohlcv(
    token_symbol: str,
    timeframe: str,
    from_date: str,
    to_date: str,
    chain: str = 'eth',
    hours_before_transaction: int = 24,
    hours_after_transaction: int = 24,
    limit: int = None, # max number of data points to return
    api_key: str = config.MORALIS_API_KEY
    ) -> List[Dict]:
    """
    Fetches OHLCV data for a given token symbol using the Moralis API.
    
    This function:
    1. Searches for the token address by symbol.
    2. Retrieves trading pairs for the token and selects the one with the highest liquidity (in USD).
    3. Fetches OHLCV data for that pair in the specified timeframe, priced in USD.
    
    Args:
        token_symbol (str): Token symbol (e.g., 'ETH', 'USDC').
        timeframe (str): Time interval (e.g., '5min', '15min', '1h'). 
                         Supported: '1s', '1min', '5min', '15min', '30min', '1h', '4h', '1d', '1w', '1m'.
        chain (str): Blockchain chain (e.g., 'eth', 'bsc'). Default: 'eth'.
        from_date (str): Start date (ISO format e.g., '2025-01-01T00:00:00.000Z' or Unix timestamp). Required for the API.
        to_date (str): End date (same format as from_date). Required for the API.
        hours_back (int): Number of hours to look back for data. Default: 24.
        limit (int): Number of data points to return. Default: 100.
        api_key (str): Your Moralis API key.
    
    Returns:
        List[Dict]: List of OHLCV data points, each with 'timestamp', 'open', 'high', 'low', 'close', 'volume', 'trades'.
    
    Raises:
        ValueError: If token not found, no pairs, dates not provided, or API errors.
        requests.RequestException: On network/API errors.
    
    Note: Requires a free Moralis API key (sign up at moralis.io). Free tier has request limits (~550/day for this usage).
    Ensure from_date and to_date are provided and valid for your timeframe.
    """
    
    # ===== INPUT VALIDATION SECTION =====
    
    # Set context for error messages (function name)
    context = "moralis_data.fetch_ohlcv"
    
    # Validate token_symbol is a non-empty string
    is_valid, error_msg = validators.validate_string(token_symbol, allow_empty=False, context=context)
    if not is_valid:
        raise ValueError(f"moralis_data.fetch_ohlcv: {error_msg}")
    
    # Validate to_date is provided
    if not to_date:
        raise ValueError("moralis_data.fetch_ohlcv: from_date and to_date are required")
    
    # Validate API key exists
    if not api_key:
        raise ValueError("moralis_data.fetch_ohlcv: API key is required. Get one from moralis.io")
    
    # ===== END VALIDATION SECTION =====
    
    logging.info(f"moralis_data.fetch_ohlcv: Fetching OHLCV data for {token_symbol} on chain {chain} from {from_date} to {to_date}")

    # event_timestamp is the timestamp of the lasttransaction
    event_timestamp = to_date

    #print("event_timestamp as timestamp: ", pd.to_datetime(event_timestamp, utc=True).timestamp() * 1000)
    # to_date has to be the same as the transaction timestamp + specified hours
    to_date = datetime.datetime.strptime(event_timestamp, "%Y-%m-%d %H:%M:%S UTC") + datetime.timedelta(hours=hours_after_transaction)
    to_date = to_date.strftime("%Y-%m-%d %H:%M:%S UTC")

    from_date = datetime.datetime.strptime(event_timestamp, "%Y-%m-%d %H:%M:%S UTC") - datetime.timedelta(hours=hours_before_transaction)
    from_date = from_date.strftime("%Y-%m-%d %H:%M:%S UTC")

    # Convert inputs like "2025-10-20 10:51:47 UTC" to format("2025-10-20T10:51:47.000")
    from_date_iso = from_date.replace(" UTC", "").replace(" ", "T") + ".000"
    to_date_iso = to_date.replace(" UTC", "").replace(" ", "T") + ".000"
    #print("from_date_iso: ", from_date_iso, "\nto_date_iso: ", to_date_iso)
    
    token_address = get_token_address(token_symbol, "ethereum")
    pair_address = get_best_pair_address(token_address, "eth", api_key)
    
    base_url = "https://deep-index.moralis.io/api/v2.2"
    headers = {
        "accept": "application/json",
        "X-API-Key": api_key
    }
    
    ohlcv_url = f"{base_url}/pairs/{pair_address}/ohlcv"
    params = {
        "chain": chain,
        "timeframe": timeframe,
        "currency": "usd",
        "fromDate": from_date_iso,
        "toDate": to_date_iso,
        "limit": limit
    }

    try:
        response = config.shared_api_session.get(ohlcv_url, headers=headers, params=params)
        response.raise_for_status()
        ohlcv_data = response.json()

        # save to json file but unpack from result key
        # Using pathlib.Path from config ensures cross-platform compatibility
        json_path = OHLC_DIR / f"ohlcv_data_{token_symbol}_{timeframe}.json"
        with open(json_path, 'w') as f:
            json.dump(ohlcv_data.get("result", []), f)

        logging.info(f"moralis_data.fetch_ohlcv: OHLCV data for {token_symbol} on chain {chain} from {from_date} to {to_date} is saved to {json_path}")
        return ohlcv_data.get("result", [])

    except Exception as e:
        logging.error(f"moralis_data.fetch_ohlcv: Error fetching ohlcv data: {e}")


'''
#TESTING - fetch ohlcv data using token symbol
token_symbol = "chainLink"

# TESTING - get token address from coingecko
address = get_token_address(token_symbol)
print(token_symbol, " address: ", address)

# TESTING - get token price from moralis
price = get_token_price(address)
print(token_symbol, " price: ", price[0], "USD", " - 24hr percent change: ", price[1], "%")

# TESTING - get best pair address from moralis
address_pair = get_best_pair_address(address)
print(token_symbol, " address_pair: ", address_pair)

# TESTING - fetch ohlcv data from moralis
data = fetch_ohlcv(
    token_symbol=token_symbol,
    timeframe="5min",
    chain="eth",
    from_date="2025-10-19 10:51:47 UTC",  # 24 hours before to_date
    to_date="2025-10-20 10:51:47 UTC",
    hours_before_transaction=24,
    hours_after_transaction=24,
    limit=1000
    )

#print(token_symbol, " OHLCV data: ", data) 
'''

'''
# TESTING - extract token transactions using moralis api
token_address = "0x6982508145454Ce325dDbE47a25d4ec3d2311933"
transactions = moralis_data_extract_token_transactions(token_address, max_transactions=1)
transformed_transactions = moralis_data_transform(transactions)
print("\nTransformed transactions:")
print(json.dumps(transformed_transactions, indent=2))
'''