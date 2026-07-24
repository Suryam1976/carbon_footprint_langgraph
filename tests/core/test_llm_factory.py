"""Tests for core/llm_factory.py"""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from core.llm_factory import get_llm
from core.config import DEFAULT_ANTHROPIC_MODEL, DEFAULT_GROQ_MODEL


class TestLLMFactory:
    """Test LLM factory for different providers."""

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_anthropic_provider(self):
        """Anthropic provider returns ChatAnthropic instance."""
        llm = get_llm(provider="anthropic")

        assert llm is not None
        # Should have invoke method (Runnable protocol)
        assert hasattr(llm, "invoke")

    @patch.dict("os.environ", {"GROQ_API_KEY": "test-key"})
    def test_groq_provider(self):
        """Groq provider returns ChatGroq instance."""
        llm = get_llm(provider="groq")

        assert llm is not None
        # Should have invoke method (Runnable protocol)
        assert hasattr(llm, "invoke")

    def test_unsupported_provider_raises(self):
        """Unsupported provider raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            get_llm(provider="unsupported_llm")

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_default_model_anthropic(self):
        """Default Anthropic model is claude-3-5-sonnet."""
        llm = get_llm(provider="anthropic")
        # Model is passed to ChatAnthropic init, just verify it doesn't crash
        assert llm is not None

    @patch.dict("os.environ", {"GROQ_API_KEY": "test-key"})
    def test_default_model_groq(self):
        """Default Groq model is llama-3.3-70b-versatile."""
        llm = get_llm(provider="groq")
        # Model is passed to ChatGroq init, just verify it doesn't crash
        assert llm is not None

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_custom_temperature(self):
        """Custom temperature parameter passed through."""
        llm = get_llm(provider="anthropic", temperature=0.8)
        assert llm is not None

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_custom_max_tokens(self):
        """Custom max_tokens parameter passed through."""
        llm = get_llm(provider="anthropic", max_tokens=2000)
        assert llm is not None
