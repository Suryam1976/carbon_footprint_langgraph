"""Node 4: Rule-based Categorization"""

import re
from langchain_core.messages import AIMessage
from core.state import GraphState
from utils.patterns import categorize_transaction

def rule_based_categorization_node(state: GraphState) -> GraphState:
    """
    Node 4: Apply rule-based categorization using merchant patterns
    Fast categorization for known merchants
    """
    categorized_transactions = []
    uncategorized_transactions = []
    rule_based_count = 0
    
    for transaction in state.get("redacted_transactions", []):
        description = transaction.get("description", "")
        category = categorize_transaction(description)
        
        if category:
            # Successfully categorized by rules
            categorized_transaction = {
                **transaction,
                "category": category,
                "categorization_method": "rule_based"
            }
            categorized_transactions.append(categorized_transaction)
            rule_based_count += 1
        else:
            # Needs LLM categorization
            uncategorized_transactions.append(transaction)
    
    state["rule_categorized"] = categorized_transactions
    state["uncategorized"] = uncategorized_transactions
    state["rule_based_count"] = rule_based_count
    
    state["messages"] = state.get("messages", []) + [
        AIMessage(content=f"✅ Rule-based categorization: {rule_based_count} transactions"),
        AIMessage(content=f"⏳ Remaining for LLM categorization: {len(uncategorized_transactions)} transactions")
    ]
    
    return state