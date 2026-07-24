"""Pydantic v2 models for LLM structured output.

Used at the two structured-output boundaries:
1. nodes/transaction_extractor.py: LLM returns ExtractedTransactionList
2. nodes/llm_categorizer.py: LLM returns TransactionCategorizationList

These schemas enforce shape validation at the LLM boundary, eliminating the
need for fragile regex/bracket-matching parsing.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ExtractedTransaction(BaseModel):
    """A single transaction extracted from bank statement text by LLM."""

    date: str = Field(description="Transaction date, DD/MM/YYYY format")
    description: str = Field(description="Cleaned merchant/payee name")
    amount: float = Field(ge=0, description="Amount, no commas/currency symbols")
    type: Literal["debit", "credit"] = Field(
        description="'debit' = money out, 'credit' = money in"
    )
    balance: float = Field(default=0, description="Closing account balance if available")
    raw_text: str = Field(default="", description="Original line from statement")


class ExtractedTransactionList(BaseModel):
    """Wrapper for structured output.

    Tool-calling LLMs need one top-level object, not a bare array.
    """

    transactions: list[ExtractedTransaction] = Field(
        description="List of extracted transactions"
    )


class TransactionCategorization(BaseModel):
    """Categorization result for a single transaction."""

    index: int = Field(
        description="0-based index within the current batch of uncategorized transactions"
    )
    category: str = Field(
        description="One of the official category names (will be normalized post-LLM)"
    )


class TransactionCategorizationList(BaseModel):
    """Wrapper for categorization results."""

    categorizations: list[TransactionCategorization] = Field(
        description="List of categorization results"
    )
