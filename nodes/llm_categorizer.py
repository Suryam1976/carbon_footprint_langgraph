"""Node 6: LLM-based Categorization

Categorizes uncategorized transactions using Anthropic/Groq LLM with batching
to keep token usage reasonable. Uses structured output for reliable schema
compliance.
"""

from __future__ import annotations

import logging

from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate

from core.config import DEFAULT_ANTHROPIC_MODEL, LLM_CATEGORIZATION_BATCH_SIZE
from core.llm_factory import get_llm
from core.schemas import TransactionCategorizationList
from core.state import GraphState
from utils.patterns import get_all_categories, normalize_category

logger = logging.getLogger(__name__)


def llm_categorization_node(state: GraphState) -> GraphState:
    """
    Node 6: Use LLM to categorize remaining uncategorized transactions.
    Batches transactions to keep token budget reasonable.
    """
    uncategorized = state.get("uncategorized", [])

    if not uncategorized:
        logger.debug("No uncategorized transactions to process")
        state["messages"] = state.get("messages", []) + [
            AIMessage(content="✅ No transactions need LLM categorization")
        ]
        return state

    logger.debug("Processing %d uncategorized transactions in batches of %d",
                 len(uncategorized), LLM_CATEGORIZATION_BATCH_SIZE)

    # Get LLM (default to Anthropic for better categorization quality)
    llm = get_llm(
        provider=state.get("llm_provider", "anthropic"),
        model=state.get("llm_model", DEFAULT_ANTHROPIC_MODEL),
    )

    # Prepare categories list for the prompt
    categories = get_all_categories()
    categories_text = "\n".join([f"- {cat}" for cat in categories])

    # Create categorization prompt with strict category enforcement
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"""You are a transaction categorizer for carbon footprint analysis.

You MUST use ONLY these exact categories (no others allowed):
{categories_text}

For each transaction, assign the most appropriate category based on the merchant/description.

IMPORTANT:
- Use ONLY the exact category names listed above
- Use "miscellaneous" if no category fits well
- Do NOT create new categories or variations

Return a JSON object with a "categorizations" array.
Each item in the array must have an "index" field (integer, 0-based) and a "category" field (string).
""",
            ),
            ("human", "Transactions to categorize:\n{transactions}"),
        ]
    )

    # Process transactions in batches
    llm_categorized = []

    for batch_start in range(0, len(uncategorized), LLM_CATEGORIZATION_BATCH_SIZE):
        batch_end = min(batch_start + LLM_CATEGORIZATION_BATCH_SIZE, len(uncategorized))
        batch = uncategorized[batch_start:batch_end]

        logger.debug("Processing batch %d-%d of %d", batch_start, batch_end, len(uncategorized))

        try:
            # Format transactions for LLM (using local batch indices 0..batch_len-1)
            transactions_text = ""
            for local_idx, txn in enumerate(batch):
                transactions_text += f"{local_idx}: {txn.get('description', '')} - ₹{txn.get('amount', 0)}\n"

            # Use structured output
            structured_llm = llm.with_structured_output(TransactionCategorizationList)
            chain = prompt | structured_llm

            result = chain.invoke(
                {"transactions": transactions_text},
                config={
                    "run_name": "llm_categorization",
                    "tags": [
                        "categorization",
                        state.get("llm_provider", "anthropic"),
                        f"batch_{batch_start}",
                    ],
                },
            )

            # Apply categorizations with global index offset
            for cat_result in result.categorizations:
                local_idx = cat_result.index
                category = cat_result.category

                # Normalize category to official list
                category = normalize_category(category)

                if 0 <= local_idx < len(batch):
                    global_idx = batch_start + local_idx
                    categorized_txn = {
                        **batch[local_idx],
                        "category": category,
                        "categorization_method": "llm_based",
                    }
                    llm_categorized.append(categorized_txn)
                else:
                    logger.warning(
                        "Batch %d: index %d out of range [0, %d)",
                        batch_start // LLM_CATEGORIZATION_BATCH_SIZE,
                        local_idx,
                        len(batch),
                    )

        except Exception as e:
            logger.warning(
                "LLM categorization failed for batch %d-%d: %s. "
                "Falling back to miscellaneous for remaining uncategorized transactions.",
                batch_start,
                batch_end,
                str(e),
                exc_info=True,
            )

            # Fallback: all remaining transactions → miscellaneous
            for local_idx, txn in enumerate(batch):
                categorized_txn = {
                    **txn,
                    "category": "miscellaneous",
                    "categorization_method": "fallback",
                }
                llm_categorized.append(categorized_txn)

    # Combine with rule-based categorizations
    all_categorized = state.get("rule_categorized", []) + llm_categorized
    state["categorized_transactions"] = all_categorized
    state["llm_based_count"] = len(llm_categorized)

    state["messages"] = state.get("messages", []) + [
        AIMessage(
            content=f"✅ LLM categorization: {len(llm_categorized)} transactions "
            f"(in {(len(uncategorized) + LLM_CATEGORIZATION_BATCH_SIZE - 1) // LLM_CATEGORIZATION_BATCH_SIZE} batches)"
        )
    ]

    return state
