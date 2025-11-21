"""Node 3: High-Value Transaction Filter"""

from langchain_core.messages import AIMessage
from core.state import GraphState

# Threshold for high-value transactions that need activity-based estimation
HIGH_VALUE_THRESHOLD = 50000  # ₹50,000

def filter_high_value_node(state: GraphState) -> GraphState:
    """
    Node 3: Filter out high-value transactions before categorization
    High-value transactions (≥₹50,000) are excluded from spend-based carbon estimation
    """
    redacted_transactions = state.get("redacted_transactions", [])
    
    regular_transactions = []
    high_value_transactions = []
    
    for transaction in redacted_transactions:
        amount = transaction.get("amount", 0)
        description = transaction.get("description", "")
        
        if amount >= HIGH_VALUE_THRESHOLD:
            # Flag as high-value, exclude from carbon estimation
            high_value_txn = {
                "amount": amount,
                "description": description[:50] + "..." if len(description) > 50 else description,
                "date": transaction.get("date", ""),
                "full_transaction": transaction,
                "reason": "High-value transaction - spend-based estimation not accurate"
            }
            high_value_transactions.append(high_value_txn)
        else:
            # Regular transaction - proceed with categorization
            regular_transactions.append(transaction)
    
    # Update state
    state["filtered_transactions"] = regular_transactions
    state["high_value_transactions"] = high_value_transactions
    state["high_value_count"] = len(high_value_transactions)
    
    # Calculate total high-value amount
    total_high_value = sum(txn["amount"] for txn in high_value_transactions)
    
    # Build messages
    messages = [
        AIMessage(content=f"✅ Transaction filtering complete"),
        AIMessage(content=f"📊 Regular transactions: {len(regular_transactions)} (for carbon analysis)"),
    ]
    
    if high_value_transactions:
        messages.append(
            AIMessage(content=(
                f"⚠️ High-value transactions excluded: {len(high_value_transactions)} "
                f"(₹{total_high_value:,.0f} total). "
                "These need activity-based carbon calculation, not spend-based."
            ))
        )
    
    state["messages"] = state.get("messages", []) + messages
    
    return state
