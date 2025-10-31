"""
Comprehensive tests for the moralis_data module.

This module tests the Moralis API integration functionality including:
- Token transaction extraction
- Data transformation
- Token address resolution
- Price fetching
- OHLCV data retrieval
- Error handling and edge cases
"""

import pytest
import json
import requests
from unittest.mock import patch, Mock
from datetime import datetime

# Add the project root directory to Python path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from modules import moralis_data


class TestMoralisDataModule:
    """Test suite for the moralis_data module functionality."""

    def test_moralis_data_extract_token_transactions_success(self):
        """Test successful token transaction extraction with valid response."""
        # Mock successful API response
        mock_response_data = {
            "result": [
                {
                    "transaction_hash": "0x123abc",
                    "from_address": "0xfrom123",
                    "to_address": "0xto456",
                    "value": "1000000000000000000",
                    "address": "0xtoken789",
                    "decimals": 18,
                    "block_timestamp": "2023-10-15T12:30:45.000Z"
                }
            ]
        }
        
        with patch('modules.moralis_data.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = moralis_data.moralis_data_extract_token_transactions(
                token_address="0xtoken123",
                max_transactions=5
            )
            
            # Verify the result
            assert len(result["result"]) == 1
            assert result["result"][0]["transaction_hash"] == "0x123abc"
            assert result["result"][0]["from_address"] == "0xfrom123"
            assert result["result"][0]["to_address"] == "0xto456"
            assert result["result"][0]["value"] == "1000000000000000000"

    def test_moralis_data_extract_token_transactions_api_error(self):
        """Test handling of API errors in token transaction extraction."""
        # Mock API error response
        mock_response_data = {
            "error": {
                "message": "Invalid token address"
            }
        }
        
        with patch('modules.moralis_data.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = moralis_data.moralis_data_extract_token_transactions(
                token_address="0xtoken123",
                max_transactions=5
            )
            
            # Should return empty list on API error
            assert result == []

    def test_moralis_data_extract_token_transactions_network_error(self):
        """Test handling of network errors during API calls."""
        with patch('modules.moralis_data.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException("Network error")
            
            with pytest.raises(ValueError) as exc_info:
                moralis_data.moralis_data_extract_token_transactions(
                    token_address="0xtoken123",
                    max_transactions=5
                )
            
            # Should raise ValueError with network error message
            assert "Network error when calling Moralis API" in str(exc_info.value)

    def test_moralis_data_extract_token_transactions_json_error(self):
        """Test handling of JSON decode errors."""
        with patch('modules.moralis_data.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            with pytest.raises(ValueError) as exc_info:
                moralis_data.moralis_data_extract_token_transactions(
                    token_address="0xtoken123",
                    max_transactions=5
                )
            
            # Should raise ValueError with JSON error message
            assert "JSON decode error when parsing Moralis response" in str(exc_info.value)

    def test_moralis_data_extract_token_transactions_address_normalization(self):
        """Test that token addresses are normalized to lowercase."""
        with patch('modules.moralis_data.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"result": []}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            moralis_data.moralis_data_extract_token_transactions(
                token_address="0xTOKEN123ABC",
                max_transactions=5
            )
            
            # Verify the address was normalized to lowercase
            call_args = mock_get.call_args
            assert "0xtoken123abc" in call_args[0][0]  # URL contains lowercase address

    def test_moralis_data_extract_token_transactions_request_params(self):
        """Test that the request parameters are correctly formatted."""
        with patch('modules.moralis_data.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"result": []}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            moralis_data.moralis_data_extract_token_transactions(
                token_address="0xtoken123",
                max_transactions=5
            )
            
            # Verify the request parameters
            call_args = mock_get.call_args
            params = call_args[1]['params']
            headers = call_args[1]['headers']
            
            assert params['chain'] == "eth"
            assert params['order'] == "DESC"
            assert params['limit'] == 5
            assert headers['Accept'] == "application/json"
            assert 'X-API-Key' in headers

    def test_moralis_data_extract_token_transactions_custom_api_key(self):
        """Test that custom API key is used when provided."""
        with patch('modules.moralis_data.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"result": []}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            moralis_data.moralis_data_extract_token_transactions(
                token_address="0xtoken123",
                max_transactions=5,
                moralis_api_key="custom_key"
            )
            
            # Verify the custom API key was used
            call_args = mock_get.call_args
            headers = call_args[1]['headers']
            assert headers['X-API-Key'] == "custom_key"

    def test_moralis_data_transform_success(self):
        """Test successful data transformation."""
        # Mock transaction data
        transactions = {
            "result": [
                {
                    "transaction_hash": "0x123abc",
                    "from_address": "0xfrom123",
                    "to_address": "0xto456",
                    "value": "1000000000000000000",
                    "address": "0xtoken789",
                    "decimals": 18,
                    "block_timestamp": "2023-10-15T12:30:45.000Z"
                }
            ]
        }
        
        result = moralis_data.moralis_data_transform(transactions)
        
        # Verify the transformation
        assert len(result) == 1
        transformed = result[0]
        assert transformed['transactionHash'] == "0x123abc"
        assert transformed['fromAddress'] == "0xfrom123"
        assert transformed['toAddress'] == "0xto456"
        assert transformed['tokenAddress'] == "0xtoken789"
        assert transformed['transferAmount'] == "1000000000000000000"
        assert transformed['transferAmountFormatted'] == "1.00"
        assert transformed['blockTimestamp'] == "2023-10-15 12:30:45 UTC"

    def test_moralis_data_transform_empty_transactions(self):
        """Test transformation with empty transactions list."""
        result = moralis_data.moralis_data_transform({"result": []})
        assert result == []

    def test_moralis_data_transform_list_input(self):
        """Test transformation with list input instead of dict."""
        transactions = [
            {
                "transaction_hash": "0x123abc",
                "from_address": "0xfrom123",
                "to_address": "0xto456",
                "value": "1000000000000000000",
                "address": "0xtoken789",
                "decimals": 18,
                "block_timestamp": "2023-10-15T12:30:45.000Z"
            }
        ]
        
        result = moralis_data.moralis_data_transform(transactions)
        
        # Should handle list input correctly
        assert len(result) == 1
        assert result[0]['transactionHash'] == "0x123abc"

    def test_moralis_data_transform_invalid_format(self):
        """Test transformation with invalid data format."""
        with pytest.raises(ValueError):
            moralis_data.moralis_data_transform("invalid_data")

    def test_moralis_data_transform_malformed_data(self):
        """Test transformation with malformed transaction data."""
        transactions = {
            "result": [
                {
                    "transaction_hash": "0x123abc",
                    # Missing required fields
                },
                {
                    "transaction_hash": "0x456def",
                    "from_address": "0xfrom123",
                    "to_address": "0xto456",
                    "value": "2000000000000000000",
                    "address": "0xtoken789",
                    "decimals": 18,
                    "block_timestamp": "2023-10-15T12:30:45.000Z"
                }
            ]
        }
        
        result = moralis_data.moralis_data_transform(transactions)
        
        # Should only return the valid transaction
        assert len(result) == 1
        assert result[0]['transactionHash'] == "0x456def"

    def test_moralis_data_transform_zero_value(self):
        """Test transformation with zero value transfers."""
        transactions = {
            "result": [
                {
                    "transaction_hash": "0x123abc",
                    "from_address": "0xfrom123",
                    "to_address": "0xto456",
                    "value": "0",
                    "address": "0xtoken789",
                    "decimals": 18,
                    "block_timestamp": "2023-10-15T12:30:45.000Z"
                }
            ]
        }
        
        result = moralis_data.moralis_data_transform(transactions)
        
        # Verify zero value is handled correctly
        assert len(result) == 1
        assert result[0]['transferAmount'] == "0"
        assert result[0]['transferAmountFormatted'] == "0"

    def test_moralis_data_transform_invalid_timestamp(self):
        """Test transformation with invalid timestamp."""
        transactions = {
            "result": [
                {
                    "transaction_hash": "0x123abc",
                    "from_address": "0xfrom123",
                    "to_address": "0xto456",
                    "value": "1000000000000000000",
                    "address": "0xtoken789",
                    "decimals": 18,
                    "block_timestamp": "invalid_timestamp"
                }
            ]
        }
        
        result = moralis_data.moralis_data_transform(transactions)
        
        # Should handle invalid timestamp gracefully
        assert len(result) == 1
        assert result[0]['blockTimestamp'] == "Invalid timestamp"

    def test_moralis_data_transform_invalid_amount(self):
        """Test transformation with invalid amount."""
        transactions = {
            "result": [
                {
                    "transaction_hash": "0x123abc",
                    "from_address": "0xfrom123",
                    "to_address": "0xto456",
                    "value": "invalid_amount",
                    "address": "0xtoken789",
                    "decimals": 18,
                    "block_timestamp": "2023-10-15T12:30:45.000Z"
                }
            ]
        }
        
        result = moralis_data.moralis_data_transform(transactions)
        
        # Should handle invalid amount gracefully
        assert len(result) == 1
        assert result[0]['transferAmountFormatted'] == "Invalid amount"

    def test_moralis_data_transform_custom_decimals(self):
        """Test transformation with custom token decimals."""
        transactions = {
            "result": [
                {
                    "transaction_hash": "0x123abc",
                    "from_address": "0xfrom123",
                    "to_address": "0xto456",
                    "value": "1000000",  # 1 token with 6 decimals
                    "address": "0xtoken789",
                    "decimals": 6,
                    "block_timestamp": "2023-10-15T12:30:45.000Z"
                }
            ]
        }
        
        result = moralis_data.moralis_data_transform(transactions)
        
        # Verify custom decimals are handled correctly
        assert len(result) == 1
        assert result[0]['transferAmount'] == "1000000"
        assert result[0]['transferAmountFormatted'] == "1.00"

    def test_get_token_address_success(self):
        """Test successful token address retrieval by symbol."""
        # Mock CoinGecko search response
        mock_search_response = {
            "coins": [
                {
                    "id": "pepe",
                    "name": "Pepe",
                    "symbol": "PEPE"
                }
            ]
        }
        
        # Mock CoinGecko details response
        mock_details_response = {
            "platforms": {
                "ethereum": "0x6982508145454Ce325dDbE47a25d4ec3d2311933"
            }
        }
        
        with patch('modules.moralis_data.requests.get') as mock_get:
            mock_get.side_effect = [
                Mock(json=lambda: mock_search_response),
                Mock(json=lambda: mock_details_response)
            ]
            
            result = moralis_data.get_token_address("PEPE")
            
            # Verify the result
            assert result == "0x6982508145454Ce325dDbE47a25d4ec3d2311933"

    def test_get_token_address_no_results(self):
        """Test handling when no token is found."""
        mock_search_response = {
            "coins": []
        }
        
        with patch('modules.moralis_data.requests.get') as mock_get:
            mock_get.return_value = Mock(json=lambda: mock_search_response)
            
            result = moralis_data.get_token_address("INVALID")
            
            # Should return None when no results found
            assert result is None

    def test_get_token_address_network_error(self):
        """Test handling of network errors in token address retrieval."""
        with patch('modules.moralis_data.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException("Network error")
            
            result = moralis_data.get_token_address("PEPE")
            
            # Should return None on network error
            assert result is None

    def test_get_token_price_success(self):
        """Test successful token price retrieval."""
        mock_response_data = {
            "usdPrice": 0.000001,
            "24hrPercentChange": 5.2
        }
        
        with patch('modules.moralis_data.requests.request') as mock_request:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_request.return_value = mock_response
            
            price, change = moralis_data.get_token_price("0xtoken123")
            
            # Verify the result
            assert price == 0.000001
            assert change == 5.2

    def test_get_token_price_no_price(self):
        """Test handling when no price is found."""
        mock_response_data = {
            "usdPrice": None,
            "24hrPercentChange": None
        }
        
        with patch('modules.moralis_data.requests.request') as mock_request:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_request.return_value = mock_response
            
            with pytest.raises(ValueError) as exc_info:
                moralis_data.get_token_price("0xtoken123")
            
            # Should raise ValueError when no price found
            assert "No price found" in str(exc_info.value)

    def test_get_token_price_network_error(self):
        """Test handling of network errors in price retrieval."""
        with patch('modules.moralis_data.requests.request') as mock_request:
            mock_request.side_effect = requests.exceptions.RequestException("Network error")
            
            with pytest.raises(ValueError) as exc_info:
                moralis_data.get_token_price("0xtoken123")
            
            # Should raise ValueError with network error message
            assert "Network error" in str(exc_info.value)

    def test_get_best_pair_address_success(self):
        """Test successful best pair address retrieval."""
        mock_response_data = {
            "pairs": [
                {
                    "pair_address": "0xpair123",
                    "liquidity_usd": 1000000
                },
                {
                    "pair_address": "0xpair456",
                    "liquidity_usd": 2000000
                }
            ]
        }
        
        with patch('modules.moralis_data.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = moralis_data.get_best_pair_address("0xtoken123")
            
            # Should return the pair with highest liquidity
            assert result == "0xpair456"

    def test_get_best_pair_address_no_pairs(self):
        """Test handling when no pairs are found."""
        mock_response_data = {
            "pairs": []
        }
        
        with patch('modules.moralis_data.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            with pytest.raises(ValueError) as exc_info:
                moralis_data.get_best_pair_address("0xtoken123")
            
            # Should raise ValueError when no pairs found
            assert "No trading pairs found" in str(exc_info.value)

    def test_get_best_pair_address_no_api_key(self):
        """Test handling when no API key is provided."""
        with pytest.raises(ValueError) as exc_info:
            moralis_data.get_best_pair_address("0xtoken123", api_key="")
        
        # Should raise ValueError when no API key
        assert "API key is required" in str(exc_info.value)

    def test_get_best_pair_address_network_error(self):
        """Test handling of network errors in pair address retrieval."""
        with patch('modules.moralis_data.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException("Network error")
            
            with pytest.raises(requests.RequestException):
                moralis_data.get_best_pair_address("0xtoken123")

    def test_fetch_ohlcv_success(self):
        """Test successful OHLCV data retrieval."""
        mock_search_response = {
            "coins": [
                {
                    "id": "pepe",
                    "name": "Pepe",
                    "symbol": "PEPE"
                }
            ]
        }
        
        mock_details_response = {
            "platforms": {
                "ethereum": "0x6982508145454Ce325dDbE47a25d4ec3d2311933"
            }
        }
        
        mock_pairs_response = {
            "pairs": [
                {
                    "pair_address": "0xpair123",
                    "liquidity_usd": 1000000
                }
            ]
        }
        
        mock_ohlcv_response = {
            "result": [
                {
                    "timestamp": "2023-10-15T12:00:00.000Z",
                    "open": 0.000001,
                    "high": 0.000002,
                    "low": 0.0000005,
                    "close": 0.0000015,
                    "volume": 1000000,
                    "trades": 100
                }
            ]
        }
        
        with patch('modules.moralis_data.requests.get') as mock_get:
            mock_get.side_effect = [
                Mock(json=lambda: mock_search_response),
                Mock(json=lambda: mock_details_response),
                Mock(json=lambda: mock_pairs_response),
                Mock(json=lambda: mock_ohlcv_response)
            ]
            
            with patch('modules.moralis_data.requests.request') as mock_request:
                mock_request.return_value = Mock(json=lambda: mock_pairs_response, raise_for_status=lambda: None)
                
                result = moralis_data.fetch_ohlcv(
                    token_symbol="PEPE",
                    timeframe="5min",
                    from_date="2023-10-15 10:51:47 UTC",
                    to_date="2023-10-15 12:51:47 UTC",
                    hours_before_transaction=1,
                    hours_after_transaction=1
                )
                
                # Verify the result
                assert len(result) == 1
                assert result[0]["open"] == 0.000001
                assert result[0]["high"] == 0.000002
                assert result[0]["low"] == 0.0000005
                assert result[0]["close"] == 0.0000015

    def test_fetch_ohlcv_no_api_key(self):
        """Test handling when no API key is provided."""
        with pytest.raises(ValueError) as exc_info:
            moralis_data.fetch_ohlcv(
                token_symbol="PEPE",
                timeframe="5min",
                from_date="2023-10-15 10:51:47 UTC",
                to_date="2023-10-15 12:51:47 UTC",
                api_key=""
            )
        
        # Should raise ValueError when no API key
        assert "API key is required" in str(exc_info.value)

    def test_fetch_ohlcv_no_to_date(self):
        """Test handling when no to_date is provided."""
        with pytest.raises(ValueError) as exc_info:
            moralis_data.fetch_ohlcv(
                token_symbol="PEPE",
                timeframe="5min",
                from_date="2023-10-15 10:51:47 UTC",
                to_date="",
                api_key="test_key"
            )
        
        # Should raise ValueError when no to_date
        assert "from_date and to_date are required" in str(exc_info.value)

    def test_fetch_ohlcv_network_error(self):
        """Test handling of network errors in OHLCV retrieval."""
        with patch('modules.moralis_data.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException("Network error")
            
            with pytest.raises(Exception):
                moralis_data.fetch_ohlcv(
                    token_symbol="PEPE",
                    timeframe="5min",
                    from_date="2023-10-15 10:51:47 UTC",
                    to_date="2023-10-15 12:51:47 UTC",
                    api_key="test_key"
                )

    def test_moralis_data_transform_large_amounts(self):
        """Test transformation with large transfer amounts."""
        transactions = {
            "result": [
                {
                    "transaction_hash": "0x123abc",
                    "from_address": "0xfrom123",
                    "to_address": "0xto456",
                    "value": "123456789012345678901234567890",
                    "address": "0xtoken789",
                    "decimals": 18,
                    "block_timestamp": "2023-10-15T12:30:45.000Z"
                }
            ]
        }
        
        result = moralis_data.moralis_data_transform(transactions)
        
        # Verify large amounts are formatted correctly
        assert len(result) == 1
        assert result[0]['transferAmount'] == "123456789012345678901234567890"
        assert "123,456,789,012.35" in result[0]['transferAmountFormatted']

    def test_moralis_data_transform_timestamp_conversion(self):
        """Test proper timestamp conversion from ISO format to UTC format."""
        transactions = {
            "result": [
                {
                    "transaction_hash": "0x123abc",
                    "from_address": "0xfrom123",
                    "to_address": "0xto456",
                    "value": "1000000000000000000",
                    "address": "0xtoken789",
                    "decimals": 18,
                    "block_timestamp": "2023-10-15T12:30:45.000Z"
                }
            ]
        }
        
        result = moralis_data.moralis_data_transform(transactions)
        
        # Verify timestamp conversion
        assert len(result) == 1
        timestamp = result[0]['blockTimestamp']
        assert "2023-10-15" in timestamp
        assert "12:30:45" in timestamp
        assert "UTC" in timestamp
        assert len(timestamp) == 23  # "YYYY-MM-DD HH:MM:SS UTC" format
