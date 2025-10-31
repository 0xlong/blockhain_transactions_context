"""
Simple AI module for generating transaction summaries using Gemini LLM via LangChain.
This module provides a minimalistic function to analyze transaction data and generate
human-readable summaries for whale alert notifications.
"""

import json
import logging
import re
from typing import Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from modules import config

# Note: Logging is configured centrally via config.setup_logging() 
# Called once at app startup in streamlit_app.py
def clean_text_output(text: str) -> str:
    """
    Clean and normalize text output to remove formatting issues and special characters.
    This function ensures the text displays properly without character-by-character formatting.
    
    Args:
        text (str): Raw text that may contain formatting issues
        
    Returns:
        str: Cleaned text ready for display
    """
    if not text:
        return ""
    
    # Remove any non-printable characters except newlines, tabs, and carriage returns
    text = re.sub(r'[^\x20-\x7E\n\r\t]', '', text)
    
    # Normalize whitespace - replace multiple spaces/tabs with single space
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Clean up line breaks - replace multiple newlines with single newline
    text = re.sub(r'\n+', '\n', text)
    
    # Remove spaces before punctuation
    text = re.sub(r'\s+([.!?,:;])', r'\1', text)
    
    # Remove double periods
    text = re.sub(r'\.+', '.', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text

# genrating ai summary with transaction data list of dictionaries
def generate_transaction_summary(transaction_data: List[Dict[str, Any]]) -> str:
    """
    Generate a concise, human-readable summary of a cryptocurrency transaction
    using Gemini LLM wrapped in LangChain.
    
    This function takes transaction context data and produces a clear summary
    that can be used for whale alert notifications or dashboard displays.
    
    Args:
        transaction_data (Dict[str, Any]): Dictionary containing transaction details
            Expected keys: 'token', 'amount', 'value_usd', 'from_address', 'to_address', 
                          'transaction_hash', 'timestamp', 'block_number'
    
    Returns:
        str: A formatted summary string describing the transaction in plain English
        
    Example:
        >>> transaction = {
        ...     'token': 'PEPE',
        ...     'amount': '1000000',
        ...     'value_usd': '50000',
        ...     'from_address': '0x123...',
        ...     'to_address': '0x456...'
        ... }
        >>> summary = generate_transaction_summary(transaction)
        >>> print(summary)
        "🐋 Large PEPE transfer: 1M tokens ($50,000) moved between addresses"
    """
    
    # Initialize Gemini LLM with API key from config
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        google_api_key=config.GEMINI_API_KEY,
        temperature=0.3,  # Low temperature for consistent, factual summaries
        max_output_tokens=500  # Keep summaries concise
    )
    
    # Create a structured prompt for the LLM
    prompt = f"""
    Analyze this cryptocurrency transaction data given <input_data> and create a concise (max 200 words) summary:
    
    <input_data>
    {transaction_data}
    </input_data>

    Requirements:
    1. Keep the summary under 200 words
    2. Dont use any emojis and styling, special characters and formatting, just output simple text
    3. Format as a single paragraph
    """
    
    logging.info(f"ai_module.generate_transaction_summary: Generating transaction summary with AI module")

    try:
        # Generate the summary using Gemini
        response = llm.invoke([HumanMessage(content=prompt)])
        raw_summary = response.content.strip()
        
        # Clean the text output to remove formatting issues
        summary = clean_text_output(raw_summary)
        
        logging.info(f"ai_module.generate_transaction_summary: Transaction summary generated successfully")
        return summary
        
    except Exception as e:
        logging.error(f"ai_module.generate_transaction_summary: Error generating transaction summary: {e}")
        return None

'''
# Example usage
transaction_data = {
        'token': 'PEPE',
        'amount': '1000000',
        'value_usd': '50000',
}
summary = generate_transaction_summary(transaction_data)
print(summary)
'''