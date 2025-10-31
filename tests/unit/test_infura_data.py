"""
Comprehensive tests for the infura_data module.

This module tests the Infura API integration functionality including:
- Token transaction extraction
- Data transformation
- Block number retrieval
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

from modules import infura_data


class TestInfuraDataModule:
    """Test suite for the infura_data module functionality."""

    def test_infura_data_extract_token_transactions_success(self):
        """Test successful token transaction extraction with valid response."""
        # Mock successful API responses for both block number and logs
        mock_block_response = {
            "jsonrpc": "2.0",
            "result": "0x1041a59",  # Latest block number in hex
            "id": 1
        }
        
        mock_logs_response = {
            "jsonrpc": "2.0",
            "result": [
                {
                    "transactionHash": "0x123abc",
                    "blockTimestamp": "0x5f8b8c8c",
                    "address": "0xtoken789",
                    "data": "0x0000000000000000000000000000000000000000000000000de0b6b3a7640000",
                    "topics": [
                        "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
                        "0x000000000000000000000000from123",
                        "0x000000000000000000000000to456"
                    ]
                }
            ],
            "id": 1
        }
        
        with patch('modules.infura_data.requests.post') as mock_post:
            # Configure mock to return different responses for different calls
            mock_post.side_effect = [
                Mock(json=lambda: mock_block_response, raise_for_status=lambda: None),
                Mock(json=lambda: mock_logs_response, raise_for_status=lambda: None)
            ]
            
            result = infura_data.infura_data_extract_token_transactions(
                token_address="0xtoken123",
                max_transactions=5
            )
            
            # Verify the result
            assert len(result) == 1
            assert result[0]["transactionHash"] == "0x123abc"
            assert result[0]["address"] == "0xtoken789"
            assert result[0]["data"] == "0x0000000000000000000000000000000000000000000000000de0b6b3a7640000"

    def test_infura_data_extract_token_transactions_block_number_error(self):
        """Test handling of errors when getting latest block number."""
        with patch('modules.infura_data.requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.RequestException("Network error")
            
            result = infura_data.infura_data_extract_token_transactions(
                token_address="0xtoken123",
                max_transactions=5
            )
            
            # Should return 0 on block number error
            assert result == 0

    def test_infura_data_extract_token_transactions_logs_error(self):
        """Test handling of errors when getting transaction logs."""
        # Mock successful block number response
        mock_block_response = {
            "jsonrpc": "2.0",
            "result": "0x1041a59",
            "id": 1
        }
        
        with patch('modules.infura_data.requests.post') as mock_post:
            # First call succeeds (block number), second call fails (logs)
            mock_post.side_effect = [
                Mock(json=lambda: mock_block_response, raise_for_status=lambda: None),
                requests.exceptions.RequestException("Network error")
            ]
            
            result = infura_data.infura_data_extract_token_transactions(
                token_address="0xtoken123",
                max_transactions=5
            )
            
            # Should return empty list on logs error
            assert result == []

    def test_infura_data_extract_token_transactions_json_error(self):
        """Test handling of JSON decode errors."""
        mock_block_response = {
            "jsonrpc": "2.0",
            "result": "0x1041a59",
            "id": 1
        }
        
        # Create mock objects for each response
        mock_block_mock = Mock(json=lambda: mock_block_response, raise_for_status=lambda: None)
        mock_logs_mock = Mock(raise_for_status=lambda: None)
        mock_logs_mock.json.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)
        
        with patch('modules.infura_data.requests.post') as mock_post:
            mock_post.side_effect = [mock_block_mock, mock_logs_mock]
            
            result = infura_data.infura_data_extract_token_transactions(
                token_address="0xtoken123",
                max_transactions=5
            )
            
            # Should return empty list on JSON error
            assert result == []

    def test_infura_data_extract_token_transactions_address_normalization(self):
        """Test that token addresses are normalized to lowercase."""
        mock_block_response = {
            "jsonrpc": "2.0",
            "result": "0x1041a59",
            "id": 1
        }
        
        mock_logs_response = {
            "jsonrpc": "2.0",
            "result": [],
            "id": 1
        }
        
        with patch('modules.infura_data.requests.post') as mock_post:
            mock_post.side_effect = [
                Mock(json=lambda: mock_block_response, raise_for_status=lambda: None),
                Mock(json=lambda: mock_logs_response, raise_for_status=lambda: None)
            ]
            
            infura_data.infura_data_extract_token_transactions(
                token_address="0xTOKEN123ABC",
                max_transactions=5
            )
            
            # Verify the address was normalized to lowercase in the logs request
            logs_call_args = mock_post.call_args_list[1]
            payload = json.loads(logs_call_args[1]['data'])
            assert payload['params'][0]['address'] == "0xtoken123abc"

    def test_infura_data_extract_token_transactions_max_transactions_limit(self):
        """Test that max_transactions limits the returned logs."""
        mock_block_response = {
            "jsonrpc": "2.0",
            "result": "0x1041a59",
            "id": 1
        }
        
        # Mock response with 10 logs
        mock_logs_response = {
            "jsonrpc": "2.0",
            "result": [
                {"transactionHash": f"0x{i:06x}"} for i in range(10)
            ],
            "id": 1
        }
        
        with patch('modules.infura_data.requests.post') as mock_post:
            mock_post.side_effect = [
                Mock(json=lambda: mock_block_response, raise_for_status=lambda: None),
                Mock(json=lambda: mock_logs_response, raise_for_status=lambda: None)
            ]
            
            result = infura_data.infura_data_extract_token_transactions(
                token_address="0xtoken123",
                max_transactions=3
            )
            
            # Should return only the last 3 logs
            assert len(result) == 3
            assert result[0]["transactionHash"] == "0x000007"
            assert result[1]["transactionHash"] == "0x000008"
            assert result[2]["transactionHash"] == "0x000009"

    def test_infura_data_extract_token_transactions_request_payloads(self):
        """Test that the request payloads are correctly formatted."""
        mock_block_response = {
            "jsonrpc": "2.0",
            "result": "0x1041a59",
            "id": 1
        }
        
        mock_logs_response = {
            "jsonrpc": "2.0",
            "result": [],
            "id": 1
        }
        
        with patch('modules.infura_data.requests.post') as mock_post:
            mock_post.side_effect = [
                Mock(json=lambda: mock_block_response, raise_for_status=lambda: None),
                Mock(json=lambda: mock_logs_response, raise_for_status=lambda: None)
            ]
            
            infura_data.infura_data_extract_token_transactions(
                token_address="0xtoken123",
                max_transactions=5
            )
            
            # Verify block number request payload
            block_call_args = mock_post.call_args_list[0]
            block_payload = json.loads(block_call_args[1]['data'])
            assert block_payload['jsonrpc'] == "2.0"
            assert block_payload['method'] == "eth_blockNumber"
            assert block_payload['params'] == []
            assert block_payload['id'] == 1
            
            # Verify logs request payload
            logs_call_args = mock_post.call_args_list[1]
            logs_payload = json.loads(logs_call_args[1]['data'])
            assert logs_payload['jsonrpc'] == "2.0"
            assert logs_payload['method'] == "eth_getLogs"
            assert logs_payload['id'] == 1
            
            logs_params = logs_payload['params'][0]
            assert logs_params['address'] == "0xtoken123"
            assert logs_params['topics'][0] == "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
            assert logs_params['fromBlock'].startswith("0x")
            assert logs_params['toBlock'].startswith("0x")

    def test_infura_data_extract_token_transactions_custom_api_key(self):
        """Test that custom API key is used when provided."""
        mock_block_response = {
            "jsonrpc": "2.0",
            "result": "0x1041a59",
            "id": 1
        }
        
        mock_logs_response = {
            "jsonrpc": "2.0",
            "result": [],
            "id": 1
        }
        
        with patch('modules.infura_data.requests.post') as mock_post:
            mock_post.side_effect = [
                Mock(json=lambda: mock_block_response, raise_for_status=lambda: None),
                Mock(json=lambda: mock_logs_response, raise_for_status=lambda: None)
            ]
            
            infura_data.infura_data_extract_token_transactions(
                token_address="0xtoken123",
                max_transactions=5,
                infura_api_key="custom_key"
            )
            
            # Verify the custom API key was used in the URL
            for call_args in mock_post.call_args_list:
                assert "custom_key" in call_args[0][0]  # URL contains the custom key

    def test_infura_data_transform_success(self):
        """Test successful data transformation."""
        # Mock transaction logs
        logs = [
            {
                "transactionHash": "0x123abc",
                "blockTimestamp": "0x5f8b8c8c",
                "address": "0xtoken789",
                "data": "0x0000000000000000000000000000000000000000000000000de0b6b3a7640000",
                "topics": [
                    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
                    "0x000000000000000000000000from123",
                    "0x000000000000000000000000to456"
                ]
            }
        ]
        
        result = infura_data.infura_data_transform(logs)
        
        # Verify the transformation
        assert len(result) == 1
        transformed = result[0]
        assert transformed['transactionHash'] == "0x123abc"
        assert transformed['fromAddress'] == "0xfrom123"
        assert transformed['toAddress'] == "0xto456"
        assert transformed['address'] == "0xtoken789"
        assert transformed['transferAmount'] == "1000000000000000000"
        assert transformed['transferAmountFormatted'] == "1.00"
        assert "2020-10-18" in transformed['blockTimestamp']
        assert "UTC" in transformed['blockTimestamp']

    def test_infura_data_transform_empty_logs(self):
        """Test transformation with empty logs list."""
        result = infura_data.infura_data_transform([])
        assert result == []

    def test_infura_data_transform_malformed_data(self):
        """Test transformation with malformed log data."""
        logs = [
            {
                "transactionHash": "0x123abc",
                # Missing required fields
            },
            {
                "transactionHash": "0x456def",
                "blockTimestamp": "0x5f8b8c8c",
                "address": "0xtoken789",
                "data": "0x0000000000000000000000000000000000000000000000000de0b6b3a7640000",
                "topics": [
                    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
                    "0x000000000000000000000000from123",
                    "0x000000000000000000000000to456"
                ]
            }
        ]
        
        result = infura_data.infura_data_transform(logs)
        
        # Should only return the valid log
        assert len(result) == 1
        assert result[0]['transactionHash'] == "0x456def"

    def test_infura_data_transform_zero_value(self):
        """Test transformation with zero value transfers."""
        logs = [
            {
                "transactionHash": "0x123abc",
                "blockTimestamp": "0x5f8b8c8c",
                "address": "0xtoken789",
                "data": "0x0000000000000000000000000000000000000000000000000000000000000000",
                "topics": [
                    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
                    "0x000000000000000000000000from123",
                    "0x000000000000000000000000to456"
                ]
            }
        ]
        
        result = infura_data.infura_data_transform(logs)
        
        # Verify zero value is handled correctly
        assert len(result) == 1
        assert result[0]['transferAmount'] == "0"
        assert result[0]['transferAmountFormatted'] == "0"

    def test_infura_data_transform_invalid_timestamp(self):
        """Test transformation with invalid timestamp."""
        logs = [
            {
                "transactionHash": "0x123abc",
                "blockTimestamp": "0xinvalid",
                "address": "0xtoken789",
                "data": "0x0000000000000000000000000000000000000000000000000de0b6b3a7640000",
                "topics": [
                    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
                    "0x000000000000000000000000from123",
                    "0x000000000000000000000000to456"
                ]
            }
        ]
        
        result = infura_data.infura_data_transform(logs)
        
        # Should handle invalid timestamp gracefully
        assert len(result) == 1
        assert result[0]['blockTimestamp'] == ""

    def test_infura_data_transform_usdc_token(self):
        """Test transformation with USDC token (6 decimals)."""
        logs = [
            {
                "transactionHash": "0x123abc",
                "blockTimestamp": "0x5f8b8c8c",
                "address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",  # USDC contract
                "data": "0x00000000000000000000000000000000000000000000000000000000000f4240",  # 1,000,000 (6 decimals)
                "topics": [
                    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
                    "0x000000000000000000000000from123",
                    "0x000000000000000000000000to456"
                ]
            }
        ]
        
        result = infura_data.infura_data_transform(logs)
        
        # Verify USDC amount is formatted correctly (6 decimals)
        assert len(result) == 1
        assert result[0]['transferAmount'] == "1000000"
        assert result[0]['transferAmountFormatted'] == "1.00"

    def test_infura_data_transform_large_amounts(self):
        """Test transformation with large transfer amounts."""
        logs = [
            {
                "transactionHash": "0x123abc",
                "blockTimestamp": "0x5f8b8c8c",
                "address": "0xtoken789",
                "data": "0x0000000000000000000000000000000000000000000000000de0b6b3a7640000",  # 1 ETH in wei
                "topics": [
                    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
                    "0x000000000000000000000000from123",
                    "0x000000000000000000000000to456"
                ]
            }
        ]
        
        result = infura_data.infura_data_transform(logs)
        
        # Verify large amounts are formatted correctly
        assert len(result) == 1
        assert result[0]['transferAmount'] == "1000000000000000000"
        assert result[0]['transferAmountFormatted'] == "1.00"

    def test_infura_data_transform_address_extraction(self):
        """Test proper extraction of from/to addresses from topics."""
        logs = [
            {
                "transactionHash": "0x123abc",
                "blockTimestamp": "0x5f8b8c8c",
                "address": "0xtoken789",
                "data": "0x0000000000000000000000000000000000000000000000000de0b6b3a7640000",
                "topics": [
                    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
                    "0x0000000000000000000000001234567890123456789012345678901234567890",
                    "0x000000000000000000000000abcdefabcdefabcdefabcdefabcdefabcdefabcd"
                ]
            }
        ]
        
        result = infura_data.infura_data_transform(logs)
        
        # Verify addresses are extracted correctly
        assert len(result) == 1
        assert result[0]['fromAddress'] == "0x1234567890123456789012345678901234567890"
        assert result[0]['toAddress'] == "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd"

    def test_infura_data_transform_insufficient_topics(self):
        """Test transformation with insufficient topics."""
        logs = [
            {
                "transactionHash": "0x123abc",
                "blockTimestamp": "0x5f8b8c8c",
                "address": "0xtoken789",
                "data": "0x0000000000000000000000000000000000000000000000000de0b6b3a7640000",
                "topics": [
                    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
                    # Missing from and to address topics
                ]
            }
        ]
        
        result = infura_data.infura_data_transform(logs)
        
        # Should handle missing topics gracefully
        assert len(result) == 1
        assert result[0]['fromAddress'] == ""
        assert result[0]['toAddress'] == ""

    def test_infura_data_transform_empty_data(self):
        """Test transformation with empty data field."""
        logs = [
            {
                "transactionHash": "0x123abc",
                "blockTimestamp": "0x5f8b8c8c",
                "address": "0xtoken789",
                "data": "0x",
                "topics": [
                    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
                    "0x000000000000000000000000from123",
                    "0x000000000000000000000000to456"
                ]
            }
        ]
        
        result = infura_data.infura_data_transform(logs)
        
        # Should handle empty data gracefully
        assert len(result) == 1
        assert result[0]['transferAmount'] == "0"
        assert result[0]['transferAmountFormatted'] == "0"

    def test_infura_data_extract_token_transactions_block_range_calculation(self):
        """Test that block range is calculated correctly (latest - 100 blocks)."""
        mock_block_response = {
            "jsonrpc": "2.0",
            "result": "0x1041a59",  # Block 17000025 in decimal
            "id": 1
        }
        
        mock_logs_response = {
            "jsonrpc": "2.0",
            "result": [],
            "id": 1
        }
        
        with patch('modules.infura_data.requests.post') as mock_post:
            mock_post.side_effect = [
                Mock(json=lambda: mock_block_response, raise_for_status=lambda: None),
                Mock(json=lambda: mock_logs_response, raise_for_status=lambda: None)
            ]
            
            infura_data.infura_data_extract_token_transactions(
                token_address="0xtoken123",
                max_transactions=5
            )
            
            # Verify block range calculation
            logs_call_args = mock_post.call_args_list[1]
            logs_payload = json.loads(logs_call_args[1]['data'])
            logs_params = logs_payload['params'][0]
            
            # fromBlock should be latest - 100
            from_block_hex = logs_params['fromBlock']
            from_block_decimal = int(from_block_hex, 16)
            latest_block_decimal = int("0x1041a59", 16)
            
            assert from_block_decimal == latest_block_decimal - 100
            assert logs_params['toBlock'] == "0x1041a59"
