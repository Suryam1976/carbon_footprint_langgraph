"""Node 2: Transaction Extraction

Extracts structured transactions from raw bank statement text using Groq LLM
with structured output (primary) and plain-text fallback (secondary).

LLM is ALWAYS set to Groq (llama-3.3-70b-versatile) for extraction because it's
fast and cost-effective for this high-volume task. Anthropic is reserved for
categorization and insights.
"""

from __future__ import annotations

import json
import logging
import re

from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable

from core.exceptions import TransactionExtractionError
from core.llm_factory import get_llm
from core.schemas import ExtractedTransactionList
from core.state import GraphState
from utils.sample_data import get_sample_transactions

logger = logging.getLogger(__name__)


@traceable(name="extract_transactions", run_type="chain")
def extract_transactions_node(state: GraphState) -> GraphState:
    """
    Node 2: Extract structured transactions from raw bank statement text.
    Uses Groq LLM (always, for extraction speed) with structured output primary
    path and plain-text fallback if structured output fails.

    Raises TransactionExtractionError if a real PDF was provided but extraction
    fails (does NOT silently fall back to sample data, which would be misleading).
    """

    # Short-circuit: if we're already using sample data from pdf_parser, skip extraction
    if state.get("processing_status") == "using_sample_data" and state.get("transactions"):
        logger.debug(
            "Using %d sample transactions (extraction skipped)", len(state["transactions"])
        )
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Using {len(state['transactions'])} sample transactions")
        ]
        return state

    # Always use Groq for transaction extraction (fast, cost-effective)
    llm = get_llm(
        provider="groq",
        model="llama-3.3-70b-versatile",
        temperature=0,  # Deterministic parsing
        max_tokens=8000,
    )

    # Universal bank statement extraction prompt
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an expert Indian bank statement parser. Extract ALL transactions from this bank statement.

IMPORTANT: HDFC Bank Format Detection
If you see columns like "Date | Narration | Chq./Ref.No. | Value Dt | Withdrawal Amt. | Deposit Amt. | Closing Balance":
- The statement has TWO amount columns
- Withdrawal Amt. column = DEBIT transactions (money OUT - purchases, payments, UPI spends)
- Deposit Amt. column = CREDIT transactions (money IN - salary, refunds, transfers)
- Extract the amount from whichever column has a value
- Set type="debit" if amount is in Withdrawal column
- Set type="credit" if amount is in Deposit column

Common Transaction Patterns:
- UPI-BBNOW, UPI-Swiggy, UPI-Zomato, UPI-merchant → DEBIT (Withdrawal column)
- NEFT-SALARY, Refund, Cashback → CREDIT (Deposit column)
- ATM withdrawals → DEBIT
- Bill payments, EMI → DEBIT

For ALL Bank Statements, extract:
- date: Transaction date (convert to DD/MM/YYYY format)
- description: Merchant/payee name (clean, remove reference numbers)
- amount: Transaction amount (from Withdrawal OR Deposit column, remove commas/₹)
- type: "debit" (money out) or "credit" (money in)
- balance: Closing balance (if available, else 0)
- raw_text: Original line

CRITICAL RULES:
1. For HDFC: Withdrawal column → debit, Deposit column → credit
2. Extract EVERY transaction
3. Remove commas from amounts: "945.55" not "945.55"
4. Simplify UPI descriptions: "UPI-BBNOW-xyz@bank-ref" → "BBNOW"
5. Return JSON array with exact field names""",
            ),
            ("human", "Bank Statement Text:\n{statement_text}"),
        ]
    )

    try:
        # ======== PRIMARY PATH: Structured Output ========
        # Use .with_structured_output() for guaranteed schema compliance
        structured_llm = llm.with_structured_output(ExtractedTransactionList)
        chain = prompt | structured_llm

        result = chain.invoke(
            {"statement_text": state["raw_text"]},
            config={
                "run_name": "extract_transactions_groq_structured",
                "tags": ["extraction", "groq", "llama-3.3-70b", "structured-output"],
            },
        )

        transactions = [t.model_dump() for t in result.transactions]
        logger.debug("Structured output succeeded: extracted %d transactions", len(transactions))

    except Exception as e:
        logger.warning(
            "Structured output failed: %s. Falling back to plain-text parsing.",
            str(e),
            exc_info=True,
        )

        try:
            # ======== FALLBACK: Plain-Text Parsing ========
            # Call LLM in non-structured mode, parse the response manually
            chain = prompt | llm

            result = chain.invoke(
                {"statement_text": state["raw_text"]},
                config={
                    "run_name": "extract_transactions_groq_plaintext_fallback",
                    "tags": ["extraction", "groq", "llama-3.3-70b", "plaintext"],
                },
            )

            response_text = (
                result.content if hasattr(result, "content") else str(result)
            )

            logger.debug("LLM response (first 500 chars): %s...", response_text[:500])

            # Extract JSON using bracket matching (most robust single strategy)
            first_bracket = response_text.find("[")
            last_bracket = response_text.rfind("]")

            if first_bracket == -1 or last_bracket == -1 or last_bracket <= first_bracket:
                raise ValueError(
                    "LLM response did not contain a valid JSON array. "
                    "First '[' not found or malformed."
                )

            json_str = response_text[first_bracket : last_bracket + 1]

            # Clean up common JSON errors
            json_str = re.sub(r",\s*\]", "]", json_str)  # trailing commas before ]
            json_str = re.sub(r",\s*\}", "}", json_str)  # trailing commas before }

            transactions = json.loads(json_str)

            if not isinstance(transactions, list) or len(transactions) == 0:
                raise ValueError("Parsed JSON is not a non-empty array")

            logger.debug("Plain-text fallback succeeded: extracted %d transactions", len(transactions))

        except (json.JSONDecodeError, ValueError) as parse_error:
            # Both structured and plain-text paths failed
            # If a real PDF was given, raise an error; don't silently use sample data
            if state.get("pdf_path"):
                logger.error(
                    "Transaction extraction failed for real PDF. "
                    "Structured output: %s. Fallback parse: %s",
                    e,
                    parse_error,
                    exc_info=True,
                )
                raise TransactionExtractionError(
                    f"Could not extract transactions from the uploaded PDF. "
                    f"The file may be password-protected, scanned (image-based), "
                    f"or in an unsupported format. Try a different PDF or use sample data. "
                    f"Error: {str(parse_error)}"
                ) from parse_error
            else:
                # No PDF was provided, so we should have already short-circuited above
                logger.error("Unexpected parse failure despite no real PDF: %s", parse_error)
                raise TransactionExtractionError(
                    f"Unexpected transaction extraction error: {str(parse_error)}"
                ) from parse_error

    # Validate and normalize transaction fields
    validated = []
    for i, txn in enumerate(transactions):
        # Ensure all required fields exist
        for field, default in [
            ("date", ""),
            ("description", ""),
            ("amount", 0.0),
            ("type", "debit"),
            ("balance", 0.0),
            ("raw_text", ""),
        ]:
            if field not in txn:
                logger.debug(
                    "Transaction %d missing field '%s', using default %r", i, field, default
                )
                txn[field] = default

        # Ensure amount is numeric
        if isinstance(txn["amount"], str):
            try:
                txn["amount"] = float(txn["amount"])
            except ValueError:
                logger.warning("Transaction %d has non-numeric amount: %s", i, txn["amount"])
                txn["amount"] = 0.0

        validated.append(txn)

    state["transactions"] = validated
    state["extraction_method"] = "groq_llm_structured" if len(state["transactions"]) > 0 else "none"
    state["processing_status"] = "llm_extracted"

    state["messages"] = state.get("messages", []) + [
        AIMessage(
            content=f"✅ Extracted {len(validated)} transactions from bank statement using Groq LLM"
        )
    ]

    return state
