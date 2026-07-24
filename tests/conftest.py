"""
Pytest configuration and shared fixtures for carbon footprint analyzer tests.

Key gotchas handled:
1. Each node imports get_llm directly (from core.llm_factory import get_llm),
   so we must patch the name at each importing module (e.g., nodes.transaction_extractor.get_llm),
   NOT just core.llm_factory.get_llm.

2. Nodes call llm.with_structured_output(Schema) then chain.invoke(). A bare MagicMock
   doesn't implement LangChain's Runnable protocol, so prompt | mock fails. Fix: return
   a real RunnableLambda that behaves like production.

3. All LLM-dependent tests must be offline and deterministic.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock
from langchain_core.runnables import RunnableLambda

from core.schemas import ExtractedTransactionList, ExtractedTransaction, TransactionCategorizationList, TransactionCategorization


@pytest.fixture(autouse=True)
def no_network_env(monkeypatch):
    """Prevent any stray real API calls by clearing API keys from environment."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("LANGCHAIN_PROJECT", raising=False)


def make_fake_structured_llm(fixed_response, plain_text_response: str = ""):
    """
    Create a mock LLM that supports structured output.

    Args:
        fixed_response: A pydantic model instance (e.g., ExtractedTransactionList(...))
                       returned by the structured-output path.
        plain_text_response: What .invoke() on the raw (non-structured) llm returns,
                           for testing the plain-text fallback.

    Returns:
        A MagicMock that behaves like a production LLM for both structured and plain paths.
    """
    fake_llm = MagicMock()

    # Structured output path: return RunnableLambda that ignores input and returns fixed_response
    # RunnableLambda genuinely implements Runnable protocol, so prompt | llm.with_structured_output(...) works
    fake_llm.with_structured_output.return_value = RunnableLambda(lambda _: fixed_response)

    # Plain text path: .invoke() returns an object with .content attribute
    fake_response = MagicMock()
    fake_response.content = plain_text_response
    fake_llm.invoke.return_value = fake_response

    return fake_llm


@pytest.fixture
def patch_get_llm(monkeypatch):
    """
    Fixture to patch get_llm at specific importing modules.
    Must patch each module individually because they do direct imports.

    Usage:
        def test_something(patch_get_llm):
            fake_llm = make_fake_structured_llm(fixed_response)
            patch_get_llm(fake_llm)
            # Now when transaction_extractor.get_llm is called, it gets fake_llm
    """
    def _patch(fake_llm, targets=None):
        # Default targets: all modules that import get_llm
        targets = targets or [
            "nodes.transaction_extractor.get_llm",
            "nodes.llm_categorizer.get_llm",
            "nodes.insights_generator.get_llm",
        ]
        for target in targets:
            monkeypatch.setattr(target, lambda *a, **k: fake_llm)

    return _patch


@pytest.fixture
def sample_extracted_transaction_list():
    """Sample structured output for transaction extraction."""
    return ExtractedTransactionList(
        transactions=[
            ExtractedTransaction(
                date="01/11/2024",
                description="SWIGGY",
                amount=450.00,
                type="debit",
                balance=74550.00,
                raw_text="UPI-SWIGGY"
            ),
            ExtractedTransaction(
                date="03/11/2024",
                description="UBER",
                amount=280.00,
                type="debit",
                balance=74270.00,
                raw_text="UPI-UBER"
            ),
            ExtractedTransaction(
                date="05/11/2024",
                description="ELECTRICITY",
                amount=2500.00,
                type="debit",
                balance=71770.00,
                raw_text="NEFT-ELECTRICITY"
            ),
        ]
    )


@pytest.fixture
def sample_transaction_categorization_list():
    """Sample structured output for transaction categorization."""
    return TransactionCategorizationList(
        categorizations=[
            TransactionCategorization(index=0, category="food_and_groceries"),
            TransactionCategorization(index=1, category="transport"),
            TransactionCategorization(index=2, category="housing_and_utilities"),
        ]
    )
