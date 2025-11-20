"""Node 3: PII Redaction and Credit Filtering"""

import re
from langchain_core.messages import AIMessage
from core.state import GraphState

def redact_pii_node(state: GraphState) -> GraphState:
    """
    Node 3: Redact PII from transactions for DPDP Act compliance
    Removes sensitive payment references before sending to LLM
    ALSO filters to only include DEBIT transactions (spends only)
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
        
        # Redact mobile numbers (10 digits)
        if re.search(r'\b\d{10}\b', redacted_desc):
            redacted_desc = re.sub(r'\b\d{10}\b', '[MOBILE_REDACTED]', redacted_desc)
            pii_redacted_count += 1
        
        # Redact UPI IDs (email-like patterns)
        if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\b', redacted_desc):
            redacted_desc = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\b', '[UPI_ID_REDACTED]', redacted_desc)
            pii_redacted_count += 1
        
        # Redact account numbers (8+ digits, but not amounts)
        account_pattern = r'\b\d{8,}\b'
        if re.search(account_pattern, redacted_desc):
            # Don't redact if it's the amount field
            if str(transaction.get("amount", "")) not in redacted_desc:
                redacted_desc = re.sub(account_pattern, '[ACCOUNT_REDACTED]', redacted_desc)
                pii_redacted_count += 1
        
        # Create redacted transaction
        redacted_transaction = {
            **transaction,
            "description": redacted_desc,
            "original_description": original_desc
        }
        
        redacted_transactions.append(redacted_transaction)
    
    state["redacted_transactions"] = redacted_transactions
    state["pii_redacted_count"] = pii_redacted_count
    state["credits_filtered_count"] = credit_count
    state["debits_processed_count"] = debit_count
    
    state["messages"] = state.get("messages", []) + [
        AIMessage(content=f"✅ PII redacted from {pii_redacted_count} transactions"),
        AIMessage(content=f"✅ Filtered {credit_count} credit transactions, processing {debit_count} debits only")
    ]
    
    return state
