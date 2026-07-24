"""Node 3: PII Redaction and Credit Filtering

Redacts personally identifiable information (mobile numbers, UPI IDs, account
numbers) for DPDP Act 2023 compliance before sending transactions to LLM.

ALSO filters to include only DEBIT transactions (spends only), excluding credits.

TRADEOFF ALERT: The UPI-ID pattern (email-like) can match real email addresses
ambiguously. Over-redaction is safer for compliance purposes — this is an
accepted tradeoff documented here and in the module docstring.
"""

from __future__ import annotations

import logging
import re

from langchain_core.messages import AIMessage

from core.state import GraphState

logger = logging.getLogger(__name__)

# Module-level compiled regex patterns for PII redaction
# Mobile number: 10 consecutive digits (Indian standard)
MOBILE_PATTERN = re.compile(r'\b\d{10}\b')

# UPI ID: email-like pattern (name@bank)
# Tradeoff: also matches real email addresses, but over-redaction is safer for compliance
UPI_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\b')

# Account number: 8+ consecutive digits
# Risk: can match formatted amounts like "1,234,567.89" if the comma is removed
ACCOUNT_PATTERN = re.compile(r'\b\d{8,}\b')


def _is_amount_match(matched_digits: str, amount: float) -> bool:
    """Check if matched digits numerically match the transaction amount.

    Used to avoid redacting amount values when they happen to be 8+ digits long.
    Allows for floating-point rounding error (within ±0.01).
    """
    try:
        matched_value = float(matched_digits)
        return abs(matched_value - amount) < 0.01
    except ValueError:
        return False


def redact_pii_node(state: GraphState) -> GraphState:
    """
    Node 3: Redact PII from transactions for DPDP Act compliance.
    Removes sensitive payment references before sending to LLM.
    ALSO filters to only include DEBIT transactions (spends only).
    """
    redacted_transactions = []
    pii_redacted_count = 0
    credit_count = 0
    debit_count = 0

    for transaction in state.get("transactions", []):
        # Filter: Only process DEBIT transactions (actual spending)
        if transaction.get("type", "").lower() == "credit":
            credit_count += 1
            continue

        debit_count += 1
        original_desc = transaction.get("description", "")
        redacted_desc = original_desc
        amount = transaction.get("amount", 0)
        local_pii_count = 0

        # Redact mobile numbers (10 digits)
        if MOBILE_PATTERN.search(redacted_desc):
            redacted_desc = MOBILE_PATTERN.sub('[MOBILE_REDACTED]', redacted_desc)
            local_pii_count += 1

        # Redact UPI IDs (email-like patterns)
        # Note: this also matches real email addresses (accepted tradeoff for compliance)
        if UPI_PATTERN.search(redacted_desc):
            redacted_desc = UPI_PATTERN.sub('[UPI_ID_REDACTED]', redacted_desc)
            local_pii_count += 1

        # Redact account numbers (8+ digits), but NOT if they match the transaction amount
        for match in ACCOUNT_PATTERN.finditer(redacted_desc):
            matched_digits = match.group()
            # Guard: don't redact if this matches the transaction amount
            if not _is_amount_match(matched_digits, amount):
                redacted_desc = redacted_desc.replace(matched_digits, '[ACCOUNT_REDACTED]')
                local_pii_count += 1

        if local_pii_count > 0:
            pii_redacted_count += 1

        # Create redacted transaction (flat structure, matches CategorizedTransaction TypedDict)
        redacted_transaction = {
            **transaction,
            "description": redacted_desc,
            "original_description": original_desc,
        }

        redacted_transactions.append(redacted_transaction)

    state["redacted_transactions"] = redacted_transactions
    state["pii_redacted_count"] = pii_redacted_count
    state["credits_filtered_count"] = credit_count
    state["debits_processed_count"] = debit_count

    state["messages"] = state.get("messages", []) + [
        AIMessage(content=f"✅ PII redacted from {pii_redacted_count} transactions"),
        AIMessage(
            content=f"✅ Filtered {credit_count} credit transactions, processing {debit_count} debits only"
        ),
    ]

    logger.debug(
        "PII redaction: redacted %d transactions, filtered %d credits, processing %d debits",
        pii_redacted_count,
        credit_count,
        debit_count,
    )

    return state
