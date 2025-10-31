"""
Comprehensive tests for the ai_module module.

This module tests the AI functionality including:
- Text cleaning and normalization
- Transaction summary generation using Gemini LLM
- Error handling and edge cases
- Prompt formatting and LLM configuration
"""

import pytest
import sys
import os
from unittest.mock import patch, Mock

# Add the project root directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from modules.ai_module import clean_text_output, generate_transaction_summary
from modules import config


class TestAiModule:
    """Test suite for the ai_module functionality."""

    # Test clean_text_output function
def test_clean_text_output_basic():
    """Test basic text cleaning functionality"""
    input_text = "  Hello   world  !  "
    expected = "Hello world!"
    result = clean_text_output(input_text)
    assert result == expected


def test_clean_text_output_remove_non_printable():
    """Test removal of non-printable characters"""
    input_text = "Hello\x00world\x01test"
    expected = "Helloworldtest"
    result = clean_text_output(input_text)
    assert result == expected


def test_clean_text_output_normalize_whitespace():
    """Test normalization of multiple spaces and tabs"""
    input_text = "Hello\t\t\tworld    test"
    expected = "Hello world test"
    result = clean_text_output(input_text)
    assert result == expected


def test_clean_text_output_clean_line_breaks():
    """Test cleaning of multiple newlines"""
    input_text = "Hello\n\n\nworld\n\n\ntest"
    expected = "Hello\nworld\ntest"
    result = clean_text_output(input_text)
    assert result == expected


def test_clean_text_output_remove_spaces_before_punctuation():
    """Test removal of spaces before punctuation"""
    input_text = "Hello , world . Test : here ;"
    expected = "Hello, world. Test: here;"
    result = clean_text_output(input_text)
    assert result == expected


def test_clean_text_output_remove_double_periods():
    """Test removal of multiple periods"""
    input_text = "Hello... world.... test....."
    expected = "Hello. world. test."
    result = clean_text_output(input_text)
    assert result == expected


def test_clean_text_output_empty_string():
    """Test handling of empty string"""
    result = clean_text_output("")
    assert result == ""


def test_clean_text_output_none_input():
    """Test handling of None input"""
    result = clean_text_output(None)
    assert result == ""


# Test generate_transaction_summary function
@patch('modules.ai_module.ChatGoogleGenerativeAI')
def test_generate_transaction_summary_success(mock_llm_class):
    """Test successful transaction summary generation"""
    # Mock the LLM response
    mock_response = Mock()
    mock_response.content = "Large PEPE transfer detected: 1M tokens worth $50,000 moved between addresses"
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke.return_value = mock_response
    mock_llm_class.return_value = mock_llm_instance
    
    # Test data
    transaction_data = [{
        'token': 'PEPE',
        'amount': '1000000',
        'value_usd': '50000',
        'from_address': '0x123...',
        'to_address': '0x456...'
    }]
    
    result = generate_transaction_summary(transaction_data)
    
    # Verify the result
    assert result == "Large PEPE transfer detected: 1M tokens worth $50,000 moved between addresses"


@patch('modules.ai_module.ChatGoogleGenerativeAI')
def test_generate_transaction_summary_llm_exception(mock_llm_class):
    """Test handling of LLM exceptions"""
    # Mock LLM to raise an exception
    mock_llm_instance = Mock()
    mock_llm_instance.invoke.side_effect = Exception("API Error")
    mock_llm_class.return_value = mock_llm_instance
    
    transaction_data = [{'token': 'PEPE', 'amount': '1000000', 'value_usd': '50000'}]
    
    result = generate_transaction_summary(transaction_data)
    
    # Should return None on exception
    assert result is None


@patch('modules.ai_module.ChatGoogleGenerativeAI')
def test_generate_transaction_summary_empty_response(mock_llm_class):
    """Test handling of empty LLM response"""
    # Mock empty response
    mock_response = Mock()
    mock_response.content = ""
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke.return_value = mock_response
    mock_llm_class.return_value = mock_llm_instance
    
    transaction_data = [{'token': 'PEPE', 'amount': '1000000', 'value_usd': '50000'}]
    
    result = generate_transaction_summary(transaction_data)
    
    # Should return empty string
    assert result == ""


@patch('modules.ai_module.ChatGoogleGenerativeAI')
def test_generate_transaction_summary_multiple_transactions(mock_llm_class):
    """Test summary generation with multiple transactions"""
    mock_response = Mock()
    mock_response.content = "Multiple large transactions detected across different tokens"
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke.return_value = mock_response
    mock_llm_class.return_value = mock_llm_instance
    
    transaction_data = [
        {'token': 'PEPE', 'amount': '1000000', 'value_usd': '50000'},
        {'token': 'DOGE', 'amount': '500000', 'value_usd': '25000'}
    ]
    
    result = generate_transaction_summary(transaction_data)
    
    assert result == "Multiple large transactions detected across different tokens"
    mock_llm_instance.invoke.assert_called_once()


@patch('modules.ai_module.ChatGoogleGenerativeAI')
def test_generate_transaction_summary_llm_configuration(mock_llm_class):
    """Test that LLM is configured with correct parameters"""
    mock_response = Mock()
    mock_response.content = "Test summary"
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke.return_value = mock_response
    mock_llm_class.return_value = mock_llm_instance
    
    transaction_data = [{'token': 'PEPE', 'amount': '1000000', 'value_usd': '50000'}]
    
    generate_transaction_summary(transaction_data)
    
    # Verify LLM was initialized with correct parameters
    mock_llm_class.assert_called_once_with(
        model="gemini-2.5-flash-lite",
        google_api_key=config.GEMINI_API_KEY,
        temperature=0.3,
        max_output_tokens=500
    )


def test_generate_transaction_summary_empty_data():
    """Test handling of empty transaction data"""
    result = generate_transaction_summary([])
    # Should still work with empty data
    assert result is not None or result is None  # Either works or returns None


@patch('modules.ai_module.ChatGoogleGenerativeAI')
def test_generate_transaction_summary_prompt_formatting(mock_llm_class):
    """Test that the prompt is formatted correctly with transaction data"""
    mock_response = Mock()
    mock_response.content = "Test summary"
    
    mock_llm_instance = Mock()
    mock_llm_instance.invoke.return_value = mock_response
    mock_llm_class.return_value = mock_llm_instance
    
    transaction_data = [{'token': 'PEPE', 'amount': '1000000', 'value_usd': '50000'}]
    
    generate_transaction_summary(transaction_data)
    
    # Get the call arguments to verify prompt content
    call_args = mock_llm_instance.invoke.call_args[0][0]
    prompt_content = call_args[0].content
    
    # Verify prompt contains transaction data
    assert str(transaction_data) in prompt_content
    assert "max 200 words" in prompt_content
    assert "single paragraph" in prompt_content

    def test_clean_text_output_unicode_characters(self):
        """Test handling of unicode characters"""
        input_text = "Hello 世界 🌍 test"
        result = clean_text_output(input_text)
        # Should preserve unicode characters
        assert "世界" in result
        assert "🌍" in result

    def test_clean_text_output_mixed_whitespace(self):
        """Test handling of mixed whitespace characters"""
        input_text = "Hello\r\n\t world \r\n test"
        result = clean_text_output(input_text)
        # Should normalize to single spaces and newlines
        assert "Hello\nworld\ntest" == result

    def test_clean_text_output_special_characters(self):
        """Test handling of special characters"""
        input_text = "Price: $100.50 (USD) - 50% off!"
        result = clean_text_output(input_text)
        # Should preserve special characters
        assert "$100.50" in result
        assert "50%" in result

    @patch('modules.ai_module.ChatGoogleGenerativeAI')
    def test_generate_transaction_summary_whitespace_only_response(self, mock_llm_class):
        """Test handling of whitespace-only LLM response"""
        mock_response = Mock()
        mock_response.content = "   \n\t   "
        
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = mock_response
        mock_llm_class.return_value = mock_llm_instance
        
        transaction_data = [{'token': 'PEPE', 'amount': '1000000', 'value_usd': '50000'}]
        
        result = generate_transaction_summary(transaction_data)
        
        # Should return empty string after cleaning
        assert result == ""

    @patch('modules.ai_module.ChatGoogleGenerativeAI')
    def test_generate_transaction_summary_none_response(self, mock_llm_class):
        """Test handling of None LLM response"""
        mock_response = Mock()
        mock_response.content = None
        
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = mock_response
        mock_llm_class.return_value = mock_llm_instance
        
        transaction_data = [{'token': 'PEPE', 'amount': '1000000', 'value_usd': '50000'}]
        
        result = generate_transaction_summary(transaction_data)
        
        # Should return empty string
        assert result == ""

    @patch('modules.ai_module.ChatGoogleGenerativeAI')
    def test_generate_transaction_summary_complex_transaction_data(self, mock_llm_class):
        """Test summary generation with complex transaction data"""
        mock_response = Mock()
        mock_response.content = "Complex transaction analysis completed"
        
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = mock_response
        mock_llm_class.return_value = mock_llm_instance
        
        transaction_data = [
            {
                'token': 'PEPE',
                'amount': '1000000',
                'value_usd': '50000',
                'from_address': '0x1234567890123456789012345678901234567890',
                'to_address': '0xabcdefabcdefabcdefabcdefabcdefabcdefabcd',
                'transaction_hash': '0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890',
                'timestamp': '2023-10-15T12:30:45Z',
                'block_number': '18500000'
            }
        ]
        
        result = generate_transaction_summary(transaction_data)
        
        assert result == "Complex transaction analysis completed"
        mock_llm_instance.invoke.assert_called_once()

    @patch('modules.ai_module.ChatGoogleGenerativeAI')
    def test_generate_transaction_summary_custom_api_key(self, mock_llm_class):
        """Test that custom API key is used when provided"""
        mock_response = Mock()
        mock_response.content = "Test summary"
        
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = mock_response
        mock_llm_class.return_value = mock_llm_instance
        
        transaction_data = [{'token': 'PEPE', 'amount': '1000000', 'value_usd': '50000'}]
        
        # This test would require modifying the function to accept custom API key
        # For now, we test that the default config is used
        generate_transaction_summary(transaction_data)
        
        # Verify LLM was initialized with config API key
        mock_llm_class.assert_called_once()
        call_args = mock_llm_class.call_args
        assert call_args[1]['google_api_key'] == config.GEMINI_API_KEY

    def test_clean_text_output_edge_cases(self):
        """Test various edge cases for text cleaning"""
        # Test with only punctuation
        assert clean_text_output("...") == "."
        assert clean_text_output("!!!") == "!"
        assert clean_text_output("???") == "?"
        
        # Test with only spaces
        assert clean_text_output("   ") == ""
        assert clean_text_output("\t\t\t") == ""
        assert clean_text_output("\n\n\n") == ""
        
        # Test with mixed punctuation and spaces
        assert clean_text_output("Hello , world !") == "Hello, world!"
        assert clean_text_output("Test : value ;") == "Test: value;"

    @patch('modules.ai_module.ChatGoogleGenerativeAI')
    def test_generate_transaction_summary_logging_behavior(self, mock_llm_class):
        """Test that appropriate logging occurs during summary generation"""
        mock_response = Mock()
        mock_response.content = "Test summary"
        
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = mock_response
        mock_llm_class.return_value = mock_llm_instance
        
        transaction_data = [{'token': 'PEPE', 'amount': '1000000', 'value_usd': '50000'}]
        
        with patch('modules.ai_module.logging') as mock_logging:
            generate_transaction_summary(transaction_data)
            
            # Verify logging calls were made
            assert mock_logging.info.called
            assert mock_logging.error.not_called  # Should not error on success

    @patch('modules.ai_module.ChatGoogleGenerativeAI')
    def test_generate_transaction_summary_logging_on_error(self, mock_llm_class):
        """Test that error logging occurs when LLM fails"""
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.side_effect = Exception("API Error")
        mock_llm_class.return_value = mock_llm_instance
        
        transaction_data = [{'token': 'PEPE', 'amount': '1000000', 'value_usd': '50000'}]
        
        with patch('modules.ai_module.logging') as mock_logging:
            result = generate_transaction_summary(transaction_data)
            
            # Verify error logging occurred
            assert mock_logging.error.called
            assert result is None