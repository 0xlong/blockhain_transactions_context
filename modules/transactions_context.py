import time
import json
from typing import Dict, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import requests
import logging
from modules import config
from modules import validators


def setup_driver(headless: bool = True) -> webdriver.Chrome:
    """
    Setup Chrome WebDriver with appropriate options.
    
    Args:
        headless (bool): Whether to run browser in headless mode
        
    Returns:
        webdriver.Chrome: Configured Chrome driver
    """
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument("--headless")
    
    # Additional options for better compatibility
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    # Disable images and CSS for faster loading
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.default_content_setting_values.notifications": 2
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    try:
        # Use webdriver-manager to automatically download and manage ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except WebDriverException as e:
        raise Exception(f"Failed to initialize Chrome driver. Make sure Chrome browser is installed. Error: {str(e)}")

def get_arkham_address_info(wallet_address: str) -> str:
    """
    Simple Arkham Intel scraper - extracts all available information.
    
    Args:
        wallet_address (str): Wallet address to scrape (e.g., "0x123...")
        
    Returns:
        str: All found information including exchange:label and tags
    """
    
    # ===== INPUT VALIDATION SECTION =====
    
    # Set context for error messages (function name)
    context = "transactions_context.get_arkham_address_info"
    
    # Validate Ethereum address format
    is_valid, error_msg = validators.validate_ethereum_address(wallet_address, context)
    if not is_valid:
        return [f"Error: {error_msg}"]
    
    # Convert address to lowercase for consistency
    wallet_address = wallet_address.lower()
    
    # ===== END VALIDATION SECTION =====
    
    logging.info(f"transactions_context.get_arkham_address_info: Getting Arkham address info for {wallet_address}")
    try:
        driver = setup_driver(headless=True)
        driver.get(f"https://intel.arkm.com/explorer/address/{wallet_address}")
        
        # Wait for page to load
        time.sleep(3)
        
        result_parts = []
        
        # Try to extract exchange and label from span.Address-module__iDi0mG__shortenContent
        try:
            span_element = driver.find_element(By.CSS_SELECTOR, "span.Address-module__iDi0mG__shortenContent")
            
            # Find the exchange link (e.g., MEXC)
            exchange_link = span_element.find_element(By.CSS_SELECTOR, "a.Address-module__iDi0mG__link")
            exchange = exchange_link.text.strip()
            
            # Find the wallet label input (e.g., Hot Wallet)
            label_input = span_element.find_element(By.CSS_SELECTOR, "input.Input-module__j8lwcG__input")
            label = label_input.get_attribute("value").strip()

            if exchange and label:
                result_parts.append(f"{exchange}:{label}")
            
        except (NoSuchElementException, TimeoutException):
            pass
        
        # Try to extract tags from Header-module__MAtMma__tagsContainer
        try:
            tags_container = driver.find_element(By.CSS_SELECTOR, "div.Header-module__MAtMma__tagsContainer")
            
            # Find all tag elements within the container
            tag_elements = tags_container.find_elements(By.CSS_SELECTOR, "div.Header-module__MAtMma__tag")
            
            tags = []
            for tag_element in tag_elements:
                # Skip the "+6 more" button
                if "tagShowMoreButton" not in tag_element.get_attribute("class"):
                    tag_text = tag_element.text.strip().replace("\n", "")
                    if tag_text and tag_text != " more":
                        result_parts.append(tag_text)
    
        except (NoSuchElementException, TimeoutException):
            # Tags container not found - expected in some cases
            result_parts.append("No tags found")
        driver.quit()
        logging.info(f"transactions_context.get_arkham_address_info: Arkham address info for {wallet_address} done successfully")
        return result_parts
    except Exception as e:
        logging.error(f"transactions_context.get_arkham_address_info: Error getting Arkham address info for {wallet_address}: {e}")
        return [f"Error: {str(e)}"]
    finally:
        # If exception occurs or function exits, quit the driver anyway to avoid resource leaks
        if driver is not None:
            driver.quit()

def get_metasleuth_addresses_nametags(address: str) -> str:
    """
    Get all wallets addresses from a given address using Metasleuth API.
    """
    
    # ===== INPUT VALIDATION SECTION =====
    
    # Set context for error messages (function name)
    context = "transactions_context.get_metasleuth_addresses_nametags"
    
    # Validate Ethereum address format
    is_valid, error_msg = validators.validate_ethereum_address(address, context)
    if not is_valid:
        return []
    
    # Convert address to lowercase for consistency
    address = address.lower()
    
    # ===== END VALIDATION SECTION =====
    
    logging.info(f"transactions_context.get_metasleuth_addresses_nametags: Getting Metasleuth addresses nametags for {address}")
    try:
        response = config.shared_api_session.post(
            "https://aml.blocksec.com/address-label/api/v3/labels",
            headers={"API-KEY": config.METASLEUTH_API_KEY,"Content-Type":"application/json"},
            data=json.dumps({
            "chain_id": 1,
            "address": address
            })
        )

        data = response.json()['data']
        logging.info(f"transactions_context.get_metasleuth_addresses_nametags: Metasleuth addresses nametags for {address} done successfully")
        return data

    except requests.exceptions.RequestException as e:
        logging.error(f"transactions_context.get_metasleuth_addresses_nametags: Network error when calling Metasleuth API: {e}")
        return []
    except json.JSONDecodeError as e:
        logging.error(f"transactions_context.get_metasleuth_addresses_nametags: JSON decode error when parsing Metasleuth response: {e}")
        return []
    except Exception as e:
        logging.error(f"transactions_context.get_metasleuth_addresses_nametags: Error getting Metasleuth addresses nametags for {address}: {e}")
        return []

def get_etherface_signature_description(method_selector: str) -> str:
    """
    Get the method description of a given method selector.
    """
    logging.info(f"transactions_context.get_etherface_signature_description: Getting Etherface signature description")

    # get only the first 8 characters of the input data from transaction info from etherscan
    method_selector = method_selector[:10]
    url = f"https://api.etherface.io/v1/signatures/hash/all/{method_selector}/1"
    
    try:
        response = config.shared_api_session.get(url)
        data = response.json()['items'][0]['text']
        logging.info(f"transactions_context.get_etherface_signature_description: Etherface signature description done successfully")
        return data
    except Exception as e:
        logging.error(f"transactions_context.get_etherface_signature_description: {method_selector[0:10]} does not have a signature description in Etherface. ({e})")
        return None

def get_4bytes_signature_description(method_selector: str) -> str:
    """
    Get the method description of a given method selector.
    """
    logging.info(f"transactions_context.get_4bytes_signature_description: Getting 4bytes signature description")
    # get only the first 8 characters of the input data from transaction info from etherscan
    method_selector = method_selector[:8]
    url = f"https://www.4byte.directory/api/v1/signatures/?format=json&hex_signature={method_selector}"
    # Make the GET request using shared session for connection pooling
    response = config.shared_api_session.get(url)
    data = response.json()
    if data['results']:
        logging.info(f"transactions_context.get_4bytes_signature_description: 4bytes signature description for {method_selector} done successfully")
        return data['results'][0]['text_signature']
    else:
        logging.info(f"transactions_context.get_4bytes_signature_description: 4bytes signature description for {method_selector} not found")
        return None

def get_etherscan_transaction_method_selector(transaction_hash: str) -> List[Dict]:
    """
    Get the method selector of a given transaction hash.
    """
    logging.info(f"transactions_context.get_etherscan_transaction_method_selector: Getting Etherscan transaction method selector for {transaction_hash}")
    
    etherscan_url = f"https://api.etherscan.io/v2/api"
    params = {
        'chainid': 1,
        'module': 'proxy',
        'action': 'eth_getTransactionByHash',
        'txhash': transaction_hash,
        'apikey': config.ETHERSCAN_API_KEY,
    }
    response = config.shared_api_session.get(
        etherscan_url,
        params=params,
        timeout=30
    )
    data = response.json()['result']['input']
    logging.info(f"transactions_context.get_etherscan_transaction_method_selector: Etherscan transaction method selector for {transaction_hash} done successfully")
    return data

def get_address_ens_domain_moralis(address: str) -> str:
    """
    Get ENS domain of a given address.
    """
    
    # ===== INPUT VALIDATION SECTION =====
    
    # Set context for error messages (function name)
    context = "transactions_context.get_address_ens_domain_moralis"
    
    # Validate Ethereum address format
    is_valid, error_msg = validators.validate_ethereum_address(address, context)
    if not is_valid:
        return 'ENS domain not found'
    
    # Convert address to lowercase for consistency
    address = address.lower()
    
    # ===== END VALIDATION SECTION =====
    
    logging.info(f"transactions_context.get_address_ens_domain_moralis: Getting ENS domain for {address}")
    
    url = f"https://deep-index.moralis.io/api/v2.2/resolve/{address}/reverse"
    
    headers = {
        "Accept": "application/json",
        "X-API-Key": config.MORALIS_API_KEY
    }
    
    response = config.shared_api_session.get(url, headers=headers)
    
    # Check if request was successful and ENS domain exists
    if response.status_code == 200:
        data = response.json().get('name')
        if data:
            return data
    
    return 'ENS domain not found'

def get_address_unstoppable_domain_moralis(address: str) -> str:
    """
    Get Unstoppable domain of a given address.
    """
    
    # ===== INPUT VALIDATION SECTION =====
    
    # Set context for error messages (function name)
    context = "transactions_context.get_address_unstoppable_domain_moralis"
    
    # Validate Ethereum address format
    is_valid, error_msg = validators.validate_ethereum_address(address, context)
    if not is_valid:
        return 'Unstoppable Domain (UD) not found'
    
    # Convert address to lowercase for consistency
    address = address.lower()
    
    # ===== END VALIDATION SECTION =====
    
    logging.info(f"transactions_context.get_address_unstoppable_domain_moralis: Getting Unstoppable domain for {address}")
    
    url = f"https://deep-index.moralis.io/api/v2.2/resolve/{address}/domain?"

    headers = {
        "Accept": "application/json",
        "X-API-Key": config.MORALIS_API_KEY
    }

    params = {
        "currency": "eth" # currency to use for the domain, Unstoppable Domains can link to multiple chains (e.g., ETH, MATIC, BTC)
    }

    response = config.shared_api_session.get(url, headers=headers, params=params)
    
    # Check if request was successful and domain exists
    if response.status_code == 200:
        data = response.json().get('name')
        if data:
            return data
    
    logging.info(f"transactions_context.get_address_unstoppable_domain_moralis: Unstoppable domain for {address} not found")
    return 'Unstoppable Domain (UD) not found'

def get_address_networth_moralis(address: str) -> str:
    """
    Get net worth of a given address.
    """
    
    # ===== INPUT VALIDATION SECTION =====
    
    # Set context for error messages (function name)
    context = "transactions_context.get_address_networth_moralis"
    
    # Validate Ethereum address format
    is_valid, error_msg = validators.validate_ethereum_address(address, context)
    if not is_valid:
        return 'Net worth not found'
    
    # Convert address to lowercase for consistency
    address = address.lower()
    
    # ===== END VALIDATION SECTION =====
    
    logging.info(f"transactions_context.get_address_networth_moralis: Getting net worth for {address}")
    
    url = f"https://deep-index.moralis.io/api/v2.2/wallets/{address}/net-worth?"
        
    headers = {
        "Accept": "application/json",
        "X-API-Key": config.MORALIS_API_KEY
    }

    params = {
        "exclude_spam": "true", # exclude spam tokens
        "exclude_unverified_contracts": "true", # exclude unverified contracts
        "max_token_inactivity": "1", # maximum token inactivity in days
        "min_pair_side_liquidity_usd": "1000" # minimum pair side liquidity in USD
    }
    
    response = config.shared_api_session.get(url, headers=headers, params=params)
    
    # Check if request was successful and net worth exists
    if response.status_code == 200:
        data = response.json().get('total_networth_usd')
        if data:
            return data
    
    logging.info(f"transactions_context.get_address_networth_moralis: Net worth for {address} not found")
    return 'Net worth not found'


'''
# Example usage
if __name__ == "__main__":
    
    # Example info data
    address = "0xd8da6bf26964af9d7eed9e03e53415d37aa96045"  # vitalik address
    tx_hash = "0x3af38c5f6997ed002f0791eaa059112bf2fcad137f3b1652a9780162daf8c8d1"

    # Address info
    #print(f"Arkham Intel info for {address}: {get_arkham_address_info(address)}")
    #print("Metasleuth addresses nametags: ", get_metasleuth_addresses_nametags(address))
    #print("ENS domain: ", get_address_ens_domain_moralis(address))
    #print("Unstoppable domain: ", get_address_unstoppable_domain_moralis(address))
    address = "0xa69babef1ca67a37ffaf7a485dfff3382056e78c"
    print("Net worth: ", get_address_networth_moralis(address))


    address = "0xf3d8736115432f80289a5fd9ce2d50f89cb0dc2c"
    print("Net worth: ", get_address_unstoppable_domain_moralis(address))
    # Transaction info
    #print("4bytes.directory method description: ", get_4bytes_signature_description(get_etherscan_transaction_method_selector(tx_hash)))
    #print("Etherface method description: ", get_etherface_signature_description(get_etherscan_transaction_method_selector(tx_hash)))
'''