"""
Comprehensive tests for the transactions_context module.

This module tests the transaction context functionality including:
- Arkham address info scraping
- Metasleuth API integration
- Signature description retrieval
- ENS/UD domain resolution
- Net worth calculation
- Error handling and edge cases
"""

import pytest
import json
import requests
from unittest.mock import patch, Mock, MagicMock
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# Add the project root directory to Python path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from modules import transactions_context


class TestTransactionsContextModule:
    """Test suite for the transactions_context module functionality."""

    def test_get_arkham_address_info_success(self):
        """Test successful Arkham address info retrieval."""
        mock_driver = Mock()
        mock_span_element = Mock()
        mock_exchange_link = Mock()
        mock_label_input = Mock()
        mock_tags_container = Mock()
        mock_tag_element = Mock()
        
        # Configure mocks
        mock_exchange_link.text = "MEXC"
        mock_label_input.get_attribute.return_value = "Hot Wallet"
        mock_tag_element.text = "Whale"
        mock_tag_element.get_attribute.return_value = "tag"
        
        mock_tags_container.find_elements.return_value = [mock_tag_element]
        mock_span_element.find_element.side_effect = [mock_exchange_link, mock_label_input]
        mock_driver.find_element.side_effect = [mock_span_element, mock_tags_container]
        
        with patch('modules.transactions_context.setup_driver') as mock_setup:
            mock_setup.return_value = mock_driver
            
            result = transactions_context.get_arkham_address_info("0xaddress123")
            
            # Verify the result
            assert "MEXC:Hot Wallet" in result
            assert "Whale" in result

    def test_get_arkham_address_info_no_elements(self):
        """Test Arkham address info when no elements are found."""
        mock_driver = Mock()
        mock_driver.find_element.side_effect = Exception("Element not found")
        
        with patch('modules.transactions_context.setup_driver') as mock_setup:
            mock_setup.return_value = mock_driver
            
            result = transactions_context.get_arkham_address_info("0xaddress123")
            
            # Should return "No tags found" message when no elements found
            assert "No tags found" in result[0]

    def test_get_arkham_address_info_exception(self):
        """Test handling of exceptions in Arkham address info retrieval."""
        with patch('modules.transactions_context.setup_driver') as mock_setup:
            mock_setup.side_effect = Exception("Driver error")
            
            result = transactions_context.get_arkham_address_info("0xaddress123")
            
            # Should return error message
            assert "Error:" in result[0]

    def test_get_metasleuth_addresses_nametags_success(self):
        """Test successful Metasleuth addresses nametags retrieval."""
        mock_response_data = {
            "data": [
                {
                    "label": "Exchange",
                    "category": "CEX"
                }
            ]
        }
        
        with patch('modules.transactions_context.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_post.return_value = mock_response
            
            result = transactions_context.get_metasleuth_addresses_nametags("0xaddress123")
            
            # Verify the result
            assert len(result) == 1
            assert result[0]["label"] == "Exchange"
            assert result[0]["category"] == "CEX"

    def test_get_metasleuth_addresses_nametags_network_error(self):
        """Test handling of network errors in Metasleuth API calls."""
        with patch('modules.transactions_context.requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.RequestException("Network error")
            
            result = transactions_context.get_metasleuth_addresses_nametags("0xaddress123")
            
            # Should return empty list on network error
            assert result == []

    def test_get_metasleuth_addresses_nametags_json_error(self):
        """Test handling of JSON decode errors in Metasleuth API calls."""
        with patch('modules.transactions_context.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)
            mock_post.return_value = mock_response
            
            result = transactions_context.get_metasleuth_addresses_nametags("0xaddress123")
            
            # Should return empty list on JSON error
            assert result == []

    def test_get_etherface_signature_description_success(self):
        """Test successful Etherface signature description retrieval."""
        mock_response_data = {
            "items": [
                {
                    "text": "transfer(address,uint256)"
                }
            ]
        }
        
        with patch('modules.transactions_context.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_get.return_value = mock_response
            
            result = transactions_context.get_etherface_signature_description("0x1234567890")
            
            # Verify the result
            assert result == "transfer(address,uint256)"

    def test_get_etherface_signature_description_no_results(self):
        """Test Etherface signature description when no results found."""
        with patch('modules.transactions_context.requests.get') as mock_get:
            mock_get.side_effect = Exception("No results")
            
            result = transactions_context.get_etherface_signature_description("0x1234567890")
            
            # Should return None when no results
            assert result is None

    def test_get_4bytes_signature_description_success(self):
        """Test successful 4bytes signature description retrieval."""
        mock_response_data = {
            "results": [
                {
                    "text_signature": "transfer(address,uint256)"
                }
            ]
        }
        
        with patch('modules.transactions_context.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_get.return_value = mock_response
            
            result = transactions_context.get_4bytes_signature_description("0x12345678")
            
            # Verify the result
            assert result == "transfer(address,uint256)"

    def test_get_4bytes_signature_description_no_results(self):
        """Test 4bytes signature description when no results found."""
        mock_response_data = {
            "results": []
        }
        
        with patch('modules.transactions_context.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_get.return_value = mock_response
            
            result = transactions_context.get_4bytes_signature_description("0x12345678")
            
            # Should return None when no results
            assert result is None

    def test_get_etherscan_transaction_method_selector_success(self):
        """Test successful Etherscan transaction method selector retrieval."""
        mock_response_data = {
            "result": {
                "input": "0x1234567890abcdef"
            }
        }
        
        with patch('modules.transactions_context.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_get.return_value = mock_response
            
            result = transactions_context.get_etherscan_transaction_method_selector("0xtx123")
            
            # Verify the result
            assert result == "0x1234567890abcdef"

    def test_get_address_ens_domain_moralis_success(self):
        """Test successful ENS domain retrieval."""
        mock_response_data = {
            "name": "vitalik.eth"
        }
        
        with patch('modules.transactions_context.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_get.return_value = mock_response
            
            result = transactions_context.get_address_ens_domain_moralis("0xaddress123")
            
            # Verify the result
            assert result == "vitalik.eth"

    def test_get_address_ens_domain_moralis_not_found(self):
        """Test ENS domain retrieval when domain not found."""
        with patch('modules.transactions_context.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response
            
            result = transactions_context.get_address_ens_domain_moralis("0xaddress123")
            
            # Should return not found message
            assert result == "ENS domain not found"

    def test_get_address_unstoppable_domain_moralis_success(self):
        """Test successful Unstoppable domain retrieval."""
        mock_response_data = {
            "name": "vitalik.crypto"
        }
        
        with patch('modules.transactions_context.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_get.return_value = mock_response
            
            result = transactions_context.get_address_unstoppable_domain_moralis("0xaddress123")
            
            # Verify the result
            assert result == "vitalik.crypto"

    def test_get_address_unstoppable_domain_moralis_not_found(self):
        """Test Unstoppable domain retrieval when domain not found."""
        with patch('modules.transactions_context.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response
            
            result = transactions_context.get_address_unstoppable_domain_moralis("0xaddress123")
            
            # Should return not found message
            assert result == "Unstoppable Domain (UD) not found"

    def test_get_address_networth_moralis_success(self):
        """Test successful net worth retrieval."""
        mock_response_data = {
            "total_networth_usd": 1000000.50
        }
        
        with patch('modules.transactions_context.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_get.return_value = mock_response
            
            result = transactions_context.get_address_networth_moralis("0xaddress123")
            
            # Verify the result
            assert result == 1000000.50

    def test_get_address_networth_moralis_not_found(self):
        """Test net worth retrieval when net worth not found."""
        with patch('modules.transactions_context.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response
            
            result = transactions_context.get_address_networth_moralis("0xaddress123")
            
            # Should return not found message
            assert result == "Net worth not found"

    def test_get_etherface_signature_description_method_selector_truncation(self):
        """Test that method selector is truncated to 10 characters."""
        with patch('modules.transactions_context.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"items": [{"text": "transfer(address,uint256)"}]}
            mock_get.return_value = mock_response
            
            transactions_context.get_etherface_signature_description("0x1234567890abcdef")
            
            # Verify the URL contains only first 10 characters (including 0x)
            call_args = mock_get.call_args
            assert "0x12345678" in call_args[0][0]

    def test_get_4bytes_signature_description_method_selector_truncation(self):
        """Test that method selector is truncated to 8 characters."""
        with patch('modules.transactions_context.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"results": [{"text_signature": "transfer(address,uint256)"}]}
            mock_get.return_value = mock_response
            
            transactions_context.get_4bytes_signature_description("0x1234567890abcdef")
            
            # Verify the URL contains only first 8 characters (including 0x)
            call_args = mock_get.call_args
            assert "0x123456" in call_args[0][0]

    def test_get_metasleuth_addresses_nametags_request_payload(self):
        """Test that Metasleuth request payload is correctly formatted."""
        with patch('modules.transactions_context.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {"data": []}
            mock_post.return_value = mock_response
            
            transactions_context.get_metasleuth_addresses_nametags("0xaddress123")
            
            # Verify the request payload
            call_args = mock_post.call_args
            payload = json.loads(call_args[1]['data'])
            
            assert payload['chain_id'] == 1
            assert payload['address'] == "0xaddress123"
            assert 'API-KEY' in call_args[1]['headers']

    def test_get_address_ens_domain_moralis_request_params(self):
        """Test that ENS domain request parameters are correctly formatted."""
        with patch('modules.transactions_context.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"name": "test.eth"}
            mock_get.return_value = mock_response
            
            transactions_context.get_address_ens_domain_moralis("0xaddress123")
            
            # Verify the URL contains the address
            call_args = mock_get.call_args
            assert "0xaddress123" in call_args[0][0]
            assert 'X-API-Key' in call_args[1]['headers']

    def test_get_address_unstoppable_domain_moralis_request_params(self):
        """Test that Unstoppable domain request parameters are correctly formatted."""
        with patch('modules.transactions_context.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"name": "test.crypto"}
            mock_get.return_value = mock_response
            
            transactions_context.get_address_unstoppable_domain_moralis("0xaddress123")
            
            # Verify the URL and parameters
            call_args = mock_get.call_args
            assert "0xaddress123" in call_args[0][0]
            assert call_args[1]['params']['currency'] == "eth"
            assert 'X-API-Key' in call_args[1]['headers']

    def test_get_address_networth_moralis_request_params(self):
        """Test that net worth request parameters are correctly formatted."""
        with patch('modules.transactions_context.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"total_networth_usd": 1000000}
            mock_get.return_value = mock_response
            
            transactions_context.get_address_networth_moralis("0xaddress123")
            
            # Verify the URL and parameters
            call_args = mock_get.call_args
            assert "0xaddress123" in call_args[0][0]
            params = call_args[1]['params']
            assert params['exclude_spam'] == "true"
            assert params['exclude_unverified_contracts'] == "true"
            assert params['max_token_inactivity'] == "1"
            assert params['min_pair_side_liquidity_usd'] == "1000"
            assert 'X-API-Key' in call_args[1]['headers']
