import os
import logging
from pathlib import Path
from dotenv import load_dotenv
import requests

# Load environment variables from .env file
load_dotenv()

# Centralized logging configuration
def setup_logging():
    """
    Configure logging for the entire application.
    Sets up consistent logging format and level across all modules.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        force=True  # Override any existing logging configuration
    )

# API Keys - Load from environment variables
SLACK_API_TOKEN = os.getenv("SLACK_API_TOKEN")
INFURA_API_KEY = os.getenv("INFURA_API_KEY")
ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")
HYPERLIQUID_API_KEY = os.getenv("HYPERLIQUID_API_KEY")
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
MORALIS_API_KEY = os.getenv("MORALIS_API_KEY")
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")
METASLEUTH_API_KEY = os.getenv("METASLEUTH_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Authentication credentials for login
# These are stored in .env file for security purposes
# The username and password required to access the application
LOGIN_USERNAME = os.getenv("LOGIN_USERNAME")
LOGIN_PASSWORD = os.getenv("LOGIN_PASSWORD")

# Validate that all required keys are present
def validate_required_keys(required_keys_list=None):
    """
    Validate that required environment variables are present.
    Can be called after Streamlit starts to show user-friendly errors.
    
    Args:
        required_keys_list: Optional list of keys to validate. 
                          If None, validates all standard keys.
    
    Returns:
        tuple: (bool, list) - (is_valid, missing_keys)
    """
    if required_keys_list is None:
        required_keys_list = [
            "INFURA_API_KEY", "ALCHEMY_API_KEY", 
            "HYPERLIQUID_API_KEY", "ETHERSCAN_API_KEY", "MORALIS_API_KEY",
            "COINGECKO_API_KEY", "METASLEUTH_API_KEY", "GEMINI_API_KEY",
            "LOGIN_USERNAME", "LOGIN_PASSWORD"
        ]
    
    missing_keys = [key for key in required_keys_list if not os.getenv(key)]
    return len(missing_keys) == 0, missing_keys

# PATH CONFIGURATION to centralize file paths
PROJECT_ROOT = Path(__file__).parent.parent  # Goes up from modules/ to project root
DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = DATA_DIR / "reports"
OHLC_DIR = DATA_DIR / "prices" / "ohlc"
CSV_DIR = DATA_DIR

OHLC_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ===== CONNECTION POOLING - Centralized HTTP Session =====
# One shared session for all API calls across the entire application
# This enables connection pooling - reuses TCP connections for faster requests
# Different APIs can still use different headers per request, but share the same connection pool
shared_api_session = requests.Session()