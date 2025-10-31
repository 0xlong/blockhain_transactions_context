"""
Comprehensive tests for the alchemy_data module.

This module tests the Alchemy API integration functionality including:
- Token transaction extraction
- Block timestamp retrieval
- Data transformation
- Contract address resolution
- Error handling and edge cases
"""

import pytest
import json
import requests
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime

# Add the project root directory to Python path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from modules import alchemy_data


class TestAlchemyDataModule:
    """Test suite for the alchemy_data module functionality."""

    def test_alchemy_data_extract_token_transactions_success(self):
        """Test successful token transaction extraction with valid response."""
        # Mock successful API response
        mock_response_data = {
            "jsonrpc": "2.0",
            "result": {
                "transfers": [
                    {
                        "hash": "0x123abc",
                        "from": "0xfrom123",
                        "to": "0xto456",
                        "value": 1000000,
                        "rawContract": {"address": "0xtoken789"},
                        "blockNum": "0x1041a59"
                    }
                ]
            },
            "id": 1
        }
        
        with patch('modules.alchemy_data.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = alchemy_data.alchemy_data_extract_token_transactions(
                token_address="0xtoken123",
                max_transactions=5
            )
            
            # Verify the result
            assert len(result) == 1
            assert result[0]["hash"] == "0x123abc"
            assert result[0]["from"] == "0xfrom123"
            assert result[0]["to"] == "0xto456"
            assert result[0]["value"] == 1000000

    def test_alchemy_data_extract_token_transactions_api_error(self):
        """Test handling of API errors in token transaction extraction."""
        # Mock API error response
        mock_response_data = {
            "jsonrpc": "2.0",
            "error": {
                "code": -32602,
                "message": "Invalid params"
            },
            "id": 1
        }
        
        with patch('modules.alchemy_data.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = alchemy_data.alchemy_data_extract_token_transactions(
                token_address="0xtoken123",
                max_transactions=5
            )
            
            # Should return empty list on API error
            assert result == []

    def test_alchemy_data_extract_token_transactions_network_error(self):
        """Test handling of network errors during API calls."""
        with patch('modules.alchemy_data.requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.RequestException("Network error")
            
            result = alchemy_data.alchemy_data_extract_token_transactions(
                token_address="0xtoken123",
                max_transactions=5
            )
            
            # Should return empty list on network error
            assert result == []

    def test_alchemy_data_extract_token_transactions_json_error(self):
        """Test handling of JSON decode errors."""
        with patch('modules.alchemy_data.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = alchemy_data.alchemy_data_extract_token_transactions(
                token_address="0xtoken123",
                max_transactions=5
            )
            
            # Should return empty list on JSON error
            assert result == []

    def test_alchemy_data_extract_token_transactions_max_transactions_limit(self):
        """Test that max_transactions is properly limited to 1000."""
        with patch('modules.alchemy_data.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {"jsonrpc": "2.0", "result": {"transfers": []}, "id": 1}
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            # Test with max_transactions > 1000
            alchemy_data.alchemy_data_extract_token_transactions(
                token_address="0xtoken123",
                max_transactions=2000
            )
            
            # Verify the request payload contains the correct maxCount
            call_args = mock_post.call_args
            payload = json.loads(call_args[1]['data'])
            assert payload['params'][0]['maxCount'] == "0x3e8"  # 1000 in hex

    def test_alchemy_data_extract_token_transactions_address_normalization(self):
        """Test that token addresses are normalized to lowercase."""
        with patch('modules.alchemy_data.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {"jsonrpc": "2.0", "result": {"transfers": []}, "id": 1}
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            alchemy_data.alchemy_data_extract_token_transactions(
                token_address="0xTOKEN123ABC",
                max_transactions=5
            )
            
            # Verify the address was normalized to lowercase
            call_args = mock_post.call_args
            payload = json.loads(call_args[1]['data'])
            assert payload['params'][0]['contractAddresses'][0] == "0xtoken123abc"

    def test_alchemy_get_block_timestamp_success(self):
        """Test successful block timestamp retrieval."""
        # Mock successful API response
        mock_response_data = {
            "jsonrpc": "2.0",
            "result": {
                "timestamp": "0x5f8b8c8c"  # Unix timestamp in hex
            },
            "id": 1
        }
        
        with patch('modules.alchemy_data.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = alchemy_data.alchemy_get_block_timestamp("0x1041a59")
            
            # Verify the result is a properly formatted UTC timestamp
            assert isinstance(result, str)
            assert "UTC" in result
            assert len(result) > 0

    def test_alchemy_get_block_timestamp_api_error(self):
        """Test handling of API errors in block timestamp retrieval."""
        mock_response_data = {
            "jsonrpc": "2.0",
            "error": {
                "code": -32602,
                "message": "Invalid block number"
            },
            "id": 1
        }
        
        with patch('modules.alchemy_data.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = alchemy_data.alchemy_get_block_timestamp("0xinvalid")
            
            # Should return empty string on API error
            assert result == ""

    def test_alchemy_get_block_timestamp_network_error(self):
        """Test handling of network errors in block timestamp retrieval."""
        with patch('modules.alchemy_data.requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.RequestException("Network error")
            
            result = alchemy_data.alchemy_get_block_timestamp("0x1041a59")
            
            # Should return empty string on network error
            assert result == ""

    def test_alchemy_data_transform_success(self):
        """Test successful data transformation."""
        # Mock transfer data
        transfers = [
            {
                "hash": "0x123abc",
                "from": "0xfrom123",
                "to": "0xto456",
                "value": 1000000,
                "rawContract": {"address": "0xtoken789"},
                "blockNum": "0x1041a59"
            }
        ]
        
        with patch('modules.alchemy_data.alchemy_get_block_timestamp') as mock_timestamp:
            mock_timestamp.return_value = "2023-10-15 12:30:45 UTC"
            
            result = alchemy_data.alchemy_data_transform(transfers)
            
            # Verify the transformation
            assert len(result) == 1
            transformed = result[0]
            assert transformed['transactionHash'] == "0x123abc"
            assert transformed['fromAddress'] == "0xfrom123"
            assert transformed['toAddress'] == "0xto456"
            assert transformed['tokenAddress'] == "0xtoken789"
            assert transformed['transferAmount'] == "1000000"
            assert transformed['transferAmountFormatted'] == "1,000,000.00"
            assert transformed['blockTimestamp'] == "2023-10-15 12:30:45 UTC"

    def test_alchemy_data_transform_empty_transfers(self):
        """Test transformation with empty transfers list."""
        result = alchemy_data.alchemy_data_transform([])
        assert result == []


    def test_alchemy_data_transform_zero_value(self):
        """Test transformation with zero value transfers."""
        transfers = [
            {
                "hash": "0x123abc",
                "from": "0xfrom123",
                "to": "0xto456",
                "value": 0,
                "rawContract": {"address": "0xtoken789"},
                "blockNum": "0x1041a59"
            }
        ]
        
        with patch('modules.alchemy_data.alchemy_get_block_timestamp') as mock_timestamp:
            mock_timestamp.return_value = "2023-10-15 12:30:45 UTC"
            
            result = alchemy_data.alchemy_data_transform(transfers)
            
            # Verify zero value is handled correctly
            assert len(result) == 1
            assert result[0]['transferAmount'] == "0"
            assert result[0]['transferAmountFormatted'] == "0"

    def test_alchemy_data_transform_missing_block_timestamp(self):
        """Test transformation when block timestamp retrieval fails."""
        transfers = [
            {
                "hash": "0x123abc",
                "from": "0xfrom123",
                "to": "0xto456",
                "value": 1000000,
                "rawContract": {"address": "0xtoken789"},
                "blockNum": "0x1041a59"
            }
        ]
        
        with patch('modules.alchemy_data.alchemy_get_block_timestamp') as mock_timestamp:
            mock_timestamp.return_value = ""  # Empty timestamp
            
            result = alchemy_data.alchemy_data_transform(transfers)
            
            # Should fallback to block number
            assert len(result) == 1
            assert "Block 0x1041a59" in result[0]['blockTimestamp']

    def test_get_contract_address_by_symbol_success(self):
        """Test successful contract address retrieval by symbol."""
        mock_response_data = {
            "jsonrpc": "2.0",
            "result": {
                "address": "0xtoken123abc"
            },
            "id": 1
        }
        
        with patch('modules.alchemy_data.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_post.return_value = mock_response
            
            result = alchemy_data.get_contract_address_by_symbol("PEPE")
            
            # Verify the result
            assert result == "0xtoken123abc"

    def test_get_contract_address_by_symbol_api_error(self):
        """Test handling of API errors in contract address retrieval."""
        mock_response_data = {
            "jsonrpc": "2.0",
            "error": {
                "code": -32602,
                "message": "Token not found"
            },
            "id": 1
        }
        
        with patch('modules.alchemy_data.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_post.return_value = mock_response
            
            result = alchemy_data.get_contract_address_by_symbol("INVALID")
            
            # Should return empty string on error
            assert result == ""


    def test_alchemy_data_extract_token_transactions_request_payload(self):
        """Test that the request payload is correctly formatted."""
        with patch('modules.alchemy_data.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {"jsonrpc": "2.0", "result": {"transfers": []}, "id": 1}
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            alchemy_data.alchemy_data_extract_token_transactions(
                token_address="0xtoken123",
                max_transactions=5
            )
            
            # Verify the request payload structure
            call_args = mock_post.call_args
            payload = json.loads(call_args[1]['data'])
            
            assert payload['jsonrpc'] == "2.0"
            assert payload['method'] == "alchemy_getAssetTransfers"
            assert payload['id'] == 1
            assert 'params' in payload
            assert len(payload['params']) == 1
            
            params = payload['params'][0]
            assert params['fromBlock'] == "0x0"
            assert params['toBlock'] == "latest"
            assert params['contractAddresses'] == ["0xtoken123"]
            assert params['category'] == ["erc20", "erc721", "erc1155"]
            assert params['withMetadata'] == True
            assert params['excludeZeroValue'] == True
            assert params['order'] == "desc"

    def test_alchemy_data_extract_token_transactions_custom_api_key(self):
        """Test that custom API key is used when provided."""
        with patch('modules.alchemy_data.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {"jsonrpc": "2.0", "result": {"transfers": []}, "id": 1}
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            alchemy_data.alchemy_data_extract_token_transactions(
                token_address="0xtoken123",
                max_transactions=5,
                alchemy_api_key="custom_key"
            )
            
            # Verify the custom API key was used in the URL
            call_args = mock_post.call_args
            assert "custom_key" in call_args[0][0]  # URL contains the custom key

    def test_alchemy_get_block_timestamp_request_payload(self):
        """Test that the block timestamp request payload is correctly formatted."""
        with patch('modules.alchemy_data.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {"jsonrpc": "2.0", "result": {"timestamp": "0x5f8b8c8c"}, "id": 1}
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            alchemy_data.alchemy_get_block_timestamp("0x1041a59")
            
            # Verify the request payload structure
            call_args = mock_post.call_args
            payload = json.loads(call_args[1]['data'])
            
            assert payload['jsonrpc'] == "2.0"
            assert payload['method'] == "eth_getBlockByNumber"
            assert payload['params'] == ["0x1041a59", False]
            assert payload['id'] == 1

