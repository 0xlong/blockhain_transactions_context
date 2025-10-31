"""
Input validation utilities for the whales_alert application.

This module provides reusable validation functions for common input types
such as Ethereum addresses, API keys, and numeric parameters. This ensures
consistent validation across all data extraction modules and prevents code duplication.

Usage:
    from modules import validators
    
    if not validators.validate_ethereum_address(address):
        return []
    
    if not validators.validate_positive_integer(max_transactions):
        return []
"""

import logging
from typing import Optional, Tuple


def validate_ethereum_address(address: str, context: str = "") -> Tuple[bool, Optional[str]]:
    """
    Validate an Ethereum address format and structure.
    
    An Ethereum address must:
    - Start with '0x'
    - Be exactly 42 characters long (0x + 40 hex characters)
    - Contain only hexadecimal characters (0-9, a-f, A-F)
    
    Args:
        address (str): The Ethereum address to validate
        context (str): Optional context string for logging (e.g., function name)
        
    Returns:
        Tuple[bool, Optional[str]]: 
            - (True, None) if address is valid
            - (False, error_message) if address is invalid
            
    Example:
        >>> is_valid, error = validate_ethereum_address("0x123...")
        >>> if not is_valid:
        ...     print(error)
    """
    # Step 1: Check if address is None or empty
    if not address:
        error_msg = "Address cannot be None or empty"
        if context:
            logging.error(f"{context}: {error_msg}")
        return False, error_msg
    
    # Step 2: Convert to lowercase for consistency
    address = address.lower()
    
    # Step 3: Check if address starts with '0x'
    if not address.startswith('0x'):
        error_msg = f"Invalid Ethereum address format: address must start with '0x', got: {address}"
        if context:
            logging.error(f"{context}: {error_msg}")
        return False, error_msg
    
    # Step 4: Check if address has correct length (42 chars: 0x + 40 hex chars)
    if len(address) != 42:
        error_msg = f"Invalid Ethereum address format: address must be 42 characters (0x + 40 hex), got {len(address)} characters: {address}"
        if context:
            logging.error(f"{context}: {error_msg}")
        return False, error_msg
    
    # Step 5: Validate that address contains only hexadecimal characters
    hex_part = address[2:]  # Remove '0x' prefix
    try:
        # Try to convert hex part to integer - this validates hex format
        int(hex_part, 16)
    except ValueError:
        error_msg = f"Invalid Ethereum address format: address contains invalid hex characters: {address}"
        if context:
            logging.error(f"{context}: {error_msg}")
        return False, error_msg
    
    # Address passed all validation checks
    return True, None


def validate_positive_integer(value: int, min_value: int = 1, max_value: Optional[int] = None, context: str = "") -> Tuple[bool, Optional[str]]:
    """
    Validate that a value is a positive integer within specified range.
    
    Args:
        value (int): The value to validate
        min_value (int): Minimum allowed value (default: 1)
        max_value (Optional[int]): Maximum allowed value (None = no limit)
        context (str): Optional context string for logging (e.g., function name)
        
    Returns:
        Tuple[bool, Optional[str]]:
            - (True, None) if value is valid
            - (False, error_message) if value is invalid
            
    Example:
        >>> is_valid, error = validate_positive_integer(5, min_value=1, max_value=100)
        >>> if not is_valid:
        ...     print(error)
    """
    # Step 1: Check if value is an integer
    if not isinstance(value, int):
        error_msg = f"Value must be an integer, got {type(value).__name__}: {value}"
        if context:
            logging.error(f"{context}: {error_msg}")
        return False, error_msg
    
    # Step 2: Check if value is at least min_value
    if value < min_value:
        error_msg = f"Value must be >= {min_value}, got: {value}"
        if context:
            logging.error(f"{context}: {error_msg}")
        return False, error_msg
    
    # Step 3: Check if value exceeds max_value (if specified)
    if max_value is not None and value > max_value:
        error_msg = f"Value must be <= {max_value}, got: {value}"
        if context:
            logging.error(f"{context}: {error_msg}")
        return False, error_msg
    
    # Value passed all validation checks
    return True, None


def validate_api_key(api_key: str, api_name: str = "API", context: str = "") -> Tuple[bool, Optional[str]]:
    """
    Validate that an API key is not None or empty.
    
    Args:
        api_key (str): The API key to validate
        api_name (str): Name of the API (for error messages, e.g., "Alchemy", "Moralis")
        context (str): Optional context string for logging (e.g., function name)
        
    Returns:
        Tuple[bool, Optional[str]]:
            - (True, None) if API key is valid
            - (False, error_message) if API key is invalid
            
    Example:
        >>> is_valid, error = validate_api_key(config.ALCHEMY_API_KEY, "Alchemy")
        >>> if not is_valid:
        ...     print(error)
    """
    if not api_key:
        error_msg = f"{api_name} API key is required but was not provided"
        if context:
            logging.error(f"{context}: {error_msg}")
        return False, error_msg
    
    # API key passed validation
    return True, None


def validate_string(value: str, allow_empty: bool = False, context: str = "") -> Tuple[bool, Optional[str]]:
    """
    Validate that a value is a non-empty string (unless allow_empty=True).
    
    Args:
        value (str): The value to validate
        allow_empty (bool): Whether to allow empty strings (default: False)
        context (str): Optional context string for logging (e.g., function name)
        
    Returns:
        Tuple[bool, Optional[str]]:
            - (True, None) if value is valid
            - (False, error_message) if value is invalid
            
    Example:
        >>> is_valid, error = validate_string("token_symbol")
        >>> if not is_valid:
        ...     print(error)
    """
    # Step 1: Check if value is a string
    if not isinstance(value, str):
        error_msg = f"Value must be a string, got {type(value).__name__}: {value}"
        if context:
            logging.error(f"{context}: {error_msg}")
        return False, error_msg
    
    # Step 2: Check if value is empty (if not allowed)
    if not allow_empty and not value:
        error_msg = "Value cannot be empty"
        if context:
            logging.error(f"{context}: {error_msg}")
        return False, error_msg
    
    # Value passed validation
    return True, None


def normalize_ethereum_address(address: str) -> str:
    """
    Normalize an Ethereum address to lowercase format.
    
    This function assumes the address has already been validated.
    Use validate_ethereum_address() first before calling this function.
    
    Args:
        address (str): Ethereum address to normalize
        
    Returns:
        str: Lowercase Ethereum address
        
    Example:
        >>> normalized = normalize_ethereum_address("0xABC123...")
        >>> print(normalized)  # "0xabc123..."
    """
    return address.lower()

