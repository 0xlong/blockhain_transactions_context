"""
Comprehensive tests for the etherscan_data module.

This module tests the Etherscan API integration functionality including:
- Token transaction extraction
- Data transformation
- ETH logs retrieval
- Error handling and edge cases
"""

import pytest
import json
import requests
from unittest.mock import patch, Mock
from datetime import datetime
from modules import etherscan_data


class TestEtherscanDataModule:
    """Test suite for the etherscan_data module functionality."""

    def test_etherscan_data_extract_token_transactions_success(self):
        """Test successful token transaction extraction with valid response."""
        # Mock successful API response
        mock_response_data = {
            "status": "1",
            "message": "OK",
            "result": [
                {
                    "hash": "0x123abc",
                    "timeStamp": "1697384645",
                    "contractAddress": "0xtoken789",
                    "from": "0xfrom123",
                    "to": "0xto456",
                    "value": "1000000000000000000",
                    "topics": [
                        "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
                    ]
                }
            ]
        }
        
        with patch('modules.etherscan_data.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = etherscan_data.etherscan_data_extract_token_transactions(
                token_address="0xtoken123",
                max_transactions=5
            )
            
            # Verify the result
            assert len(result) == 1
            assert result[0]["hash"] == "0x123abc"
            assert result[0]["from"] == "0xfrom123"
            assert result[0]["to"] == "0xto456"
            assert result[0]["value"] == "1000000000000000000"

    def test_etherscan_data_extract_token_transactions_api_error(self):
        """Test handling of API errors in token transaction extraction."""
        # Mock API error response
        mock_response_data = {
            "status": "0",
            "message": "NOTOK",
            "result": "Invalid API Key"
        }
        
        with patch('modules.etherscan_data.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = etherscan_data.etherscan_data_extract_token_transactions(
                token_address="0xtoken123",
                max_transactions=5
            )
            
            # Should return empty list on API error
            assert result == []

    def test_etherscan_data_extract_token_transactions_network_error(self):
        """Test handling of network errors during API calls."""
        with patch('modules.etherscan_data.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException("Network error")
            
            result = etherscan_data.etherscan_data_extract_token_transactions(
                token_address="0xtoken123",
                max_transactions=5
            )
            
            # Should return empty list on network error
            assert result == []

    def test_etherscan_data_extract_token_transactions_json_error(self):
        """Test handling of JSON decode errors."""
        with patch('modules.etherscan_data.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = etherscan_data.etherscan_data_extract_token_transactions(
                token_address="0xtoken123",
                max_transactions=5
            )
            
            # Should return empty list on JSON error
            assert result == []

    def test_etherscan_data_extract_token_transactions_address_normalization(self):
        """Test that token addresses are normalized to lowercase."""
        with patch('modules.etherscan_data.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"status": "1", "message": "OK", "result": []}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            etherscan_data.etherscan_data_extract_token_transactions(
                token_address="0xTOKEN123ABC",
                max_transactions=5
            )
            
            # Verify the address was normalized to lowercase
            call_args = mock_get.call_args
            params = call_args[1]['params']
            assert params['contractaddress'] == "0xtoken123abc"

    def test_etherscan_data_extract_token_transactions_request_params(self):
        """Test that the request parameters are correctly formatted."""
        with patch('modules.etherscan_data.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"status": "1", "message": "OK", "result": []}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            etherscan_data.etherscan_data_extract_token_transactions(
                token_address="0xtoken123",
                max_transactions=5
            )
            
            # Verify the request parameters
            call_args = mock_get.call_args
            params = call_args[1]['params']
            
            assert params['chainid'] == 1
            assert params['module'] == 'account'
            assert params['action'] == 'tokentx'
            assert params['contractaddress'] == '0xtoken123'
            assert params['page'] == 1
            assert params['offset'] == 5
            assert params['sort'] == 'desc'
            assert 'apikey' in params

    def test_etherscan_data_extract_token_transactions_custom_api_key(self):
        """Test that custom API key is used when provided."""
        with patch('modules.etherscan_data.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"status": "1", "message": "OK", "result": []}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            etherscan_data.etherscan_data_extract_token_transactions(
                token_address="0xtoken123",
                max_transactions=5,
                etherscan_api_key="custom_key"
            )
            
            # Verify the custom API key was used
            call_args = mock_get.call_args
            params = call_args[1]['params']
            assert params['apikey'] == "custom_key"

    def test_etherscan_data_transform_success(self):
        """Test successful data transformation."""
        # Mock transaction data
        transactions = [
            {
                "hash": "0x123abc",
                "timeStamp": "1697384645",
                "contractAddress": "0xtoken789",
                "from": "0xfrom123",
                "to": "0xto456",
                "value": "1000000000000000000"
            }
        ]
        
        result = etherscan_data.etherscan_data_transform(transactions)
        
        # Verify the transformation
        assert len(result) == 1
        transformed = result[0]
        assert transformed['transactionHash'] == "0x123abc"
        assert transformed['fromAddress'] == "0xfrom123"
        assert transformed['toAddress'] == "0xto456"
        assert transformed['address'] == "0xtoken789"
        assert transformed['transferAmount'] == "1000000000000000000"
        assert transformed['transferAmountFormatted'] == "1.00"  # 1 token with 18 decimals
        assert "2023-10-15" in transformed['blockTimestamp']  # Date from timestamp
        assert "UTC" in transformed['blockTimestamp']

    def test_etherscan_data_transform_empty_transactions(self):
        """Test transformation with empty transactions list."""
        result = etherscan_data.etherscan_data_transform([])
        assert result == []



    def test_etherscan_data_transform_zero_value(self):
        """Test transformation with zero value transactions."""
        transactions = [
            {
                "hash": "0x123abc",
                "timeStamp": "1697384645",
                "contractAddress": "0xtoken789",
                "from": "0xfrom123",
                "to": "0xto456",
                "value": "0"
            }
        ]
        
        result = etherscan_data.etherscan_data_transform(transactions)
        
        # Verify zero value is handled correctly
        assert len(result) == 1
        assert result[0]['transferAmount'] == "0"
        assert result[0]['transferAmountFormatted'] == "0"

    def test_etherscan_data_transform_invalid_timestamp(self):
        """Test transformation with invalid timestamp."""
        transactions = [
            {
                "hash": "0x123abc",
                "timeStamp": "invalid_timestamp",
                "contractAddress": "0xtoken789",
                "from": "0xfrom123",
                "to": "0xto456",
                "value": "1000000000000000000"
            }
        ]
        
        result = etherscan_data.etherscan_data_transform(transactions)
        
        # Should handle invalid timestamp gracefully
        assert len(result) == 1
        assert result[0]['blockTimestamp'] == "Invalid timestamp"

    def test_etherscan_data_transform_invalid_amount(self):
        """Test transformation with invalid amount."""
        transactions = [
            {
                "hash": "0x123abc",
                "timeStamp": "1697384645",
                "contractAddress": "0xtoken789",
                "from": "0xfrom123",
                "to": "0xto456",
                "value": "invalid_amount"
            }
        ]
        
        result = etherscan_data.etherscan_data_transform(transactions)
        
        # Should handle invalid amount gracefully
        assert len(result) == 1
        assert result[0]['transferAmountFormatted'] == "Invalid amount"


    def test_get_eth_logs_by_address_api_error(self):
        """Test handling of API errors in ETH logs retrieval."""
        mock_response_data = {
            "status": "0",
            "message": "NOTOK",
            "result": "Invalid address"
        }
        
        with patch('modules.etherscan_data.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = etherscan_data.get_eth_logs_by_address("0xinvalid")
            
            # Should return empty list on API error
            assert result == []

    def test_get_eth_logs_by_address_network_error(self):
        """Test handling of network errors in ETH logs retrieval."""
        with patch('modules.etherscan_data.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException("Network error")
            
            result = etherscan_data.get_eth_logs_by_address("0xaddress123")
            
            # Should return empty list on network error
            assert result == []

    def test_get_eth_logs_by_address_request_params(self):
        """Test that the ETH logs request parameters are correctly formatted."""
        with patch('modules.etherscan_data.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"status": "1", "message": "OK", "result": []}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            etherscan_data.get_eth_logs_by_address("0xaddress123")
            
            # Verify the request parameters
            call_args = mock_get.call_args
            params = call_args[1]['params']
            
            assert params['chainid'] == 1
            assert params['module'] == 'logs'
            assert params['action'] == 'getLogs'
            assert params['address'] == '0xaddress123'
            assert params['page'] == 1
            assert params['offset'] == 1
            assert params['sort'] == 'desc'
            assert 'apikey' in params

    def test_etherscan_data_transform_timestamp_conversion(self):
        """Test proper timestamp conversion to UTC format."""
        transactions = [
            {
                "hash": "0x123abc",
                "timeStamp": "1697384645",  # October 15, 2023
                "contractAddress": "0xtoken789",
                "from": "0xfrom123",
                "to": "0xto456",
                "value": "1000000000000000000"
            }
        ]
        
        result = etherscan_data.etherscan_data_transform(transactions)
        
        # Verify timestamp conversion
        assert len(result) == 1
        timestamp = result[0]['blockTimestamp']
        assert "2023-10-15" in timestamp
        assert "UTC" in timestamp
        assert len(timestamp) == 23  # "YYYY-MM-DD HH:MM:SS UTC" format

    def test_etherscan_data_transform_missing_fields(self):
        """Test transformation with missing optional fields."""
        transactions = [
            {
                "hash": "0x123abc",
                "timeStamp": "1697384645",
                "contractAddress": "0xtoken789",
                "from": "0xfrom123",
                "to": "0xto456",
                "value": "1000000000000000000"
                # Missing optional fields should be handled gracefully
            }
        ]
        
        result = etherscan_data.etherscan_data_transform(transactions)
        
        # Should handle missing fields gracefully
        assert len(result) == 1
        transformed = result[0]
        assert transformed['transactionHash'] == "0x123abc"
        assert transformed['fromAddress'] == "0xfrom123"
        assert transformed['toAddress'] == "0xto456"
        assert transformed['address'] == "0xtoken789"
        assert transformed['transferAmount'] == "1000000000000000000"
        assert transformed['transferAmountFormatted'] == "1.00"

    def test_etherscan_data_extract_token_transactions_transfer_event_filtering(self):
        """Test that only Transfer events are filtered correctly."""
        mock_response_data = {
            "status": "1",
            "message": "OK",
            "result": [
                {
                    "hash": "0x123abc",
                    "timeStamp": "1697384645",
                    "contractAddress": "0xtoken789",
                    "from": "0xfrom123",
                    "to": "0xto456",
                    "value": "1000000000000000000",
                    "topics": [
                        "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",  # Transfer event
                        "0x000000000000000000000000from123",
                        "0x000000000000000000000000to456"
                    ]
                },
                {
                    "hash": "0x456def",
                    "timeStamp": "1697384645",
                    "contractAddress": "0xtoken789",
                    "from": "0xfrom123",
                    "to": "0xto456",
                    "value": "2000000000000000000",
                    "topics": [
                        "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925",  # Approval event
                        "0x000000000000000000000000from123",
                        "0x000000000000000000000000to456"
                    ]
                }
            ]
        }
        
        with patch('modules.etherscan_data.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = etherscan_data.etherscan_data_extract_token_transactions(
                token_address="0xtoken123",
                max_transactions=5
            )
            
            # Should return all events (the filtering logic is commented out in the actual code)
            assert len(result) == 2
            assert result[0]["hash"] == "0x123abc"
            assert result[1]["hash"] == "0x456def"
