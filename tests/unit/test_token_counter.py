#!/usr/bin/env python3
"""
Test module: test_token_counter
"""
import sys
from pathlib import Path
import pytest
from unittest.mock import MagicMock

# Add project root to sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from codebase_skeleton import TokenCounter


class TestTokenCounter:
    """Test TokenCounter with and without tiktoken."""

    def test_token_counter_initialization_with_tiktoken(self, monkeypatch):
        """Test TokenCounter initializes with tiktoken."""
        monkeypatch.setattr("codebase_skeleton.TIKTOKEN_AVAILABLE", True)
        mock_get_encoding = MagicMock()
        monkeypatch.setattr(
            "codebase_skeleton.tiktoken.get_encoding", mock_get_encoding
        )

        counter = TokenCounter()
        assert counter.encoder is not None
        mock_get_encoding.assert_called_once_with("cl100k_base")

    def test_token_counter_initialization_without_tiktoken(
        self, mock_tiktoken_unavailable
    ):
        """Test TokenCounter falls back without tiktoken."""
        counter = TokenCounter()
        assert counter.encoder is None

    def test_count_with_tiktoken(self, monkeypatch):
        """Test token counting using tiktoken encoder."""
        monkeypatch.setattr("codebase_skeleton.TIKTOKEN_AVAILABLE", True)

        mock_encoder = MagicMock()
        mock_encoder.encode.return_value = [1, 2, 3, 4, 5]  # 5 tokens
        mock_get_encoding = MagicMock(return_value=mock_encoder)
        monkeypatch.setattr(
            "codebase_skeleton.tiktoken.get_encoding", mock_get_encoding
        )

        counter = TokenCounter()
        text = "This is a test."
        count = counter.count(text)

        assert count == 5
        mock_encoder.encode.assert_called_once_with(text)

    def test_count_with_fallback(self, mock_tiktoken_unavailable):
        """Test approximate token counting (4 chars per token)."""
        counter = TokenCounter()
        text = "12345678"  # 8 characters
        assert counter.count(text) == 2  # 8 // 4

    def test_count_empty_string(self, mock_tiktoken_unavailable):
        """Test counting tokens in empty string."""
        counter = TokenCounter()
        assert counter.count("") == 0

    def test_count_single_line(self, mock_tiktoken_unavailable):
        """Test counting tokens in single line."""
        counter = TokenCounter()
        assert counter.count("Hello world") == len("Hello world") // 4

    def test_count_multiline_text(self, mock_tiktoken_unavailable):
        """Test counting tokens in multiline text."""
        counter = TokenCounter()
        text = "Hello\nWorld"
        assert counter.count(text) == len(text) // 4

    def test_count_unicode_text(self, mock_tiktoken_unavailable):
        """Test counting tokens in Unicode text."""
        counter = TokenCounter()
        text = "こんにちは"
        assert counter.count(text) == len(text) // 4

    def test_count_code_with_comments(self, mock_tiktoken_unavailable):
        """Test counting tokens in code with comments."""
        counter = TokenCounter()
        code = "def func(): # comment"
        assert counter.count(code) == len(code) // 4
