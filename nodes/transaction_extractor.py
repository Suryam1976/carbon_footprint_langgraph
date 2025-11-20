"""Node 2: Transaction Extraction"""

import json
import re
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate

from core.state import GraphState
from core.llm_factory import get_llm
from utils.sample_data import get_sample_transactions

def extract_transactions_node(state: GraphState) -> GraphState:
    """
    Node 2: Extract structured transactions from raw text using Groq LLM
    Sends all bank statements to LLM for extraction
    """
    
    # Skip if already have transactions (from sample data)
    if state.get("processing_status") == "using_sample_data" and state.get("transactions"):
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Using {len(state['transactions'])} sample transactions")
        ]
        return state
    
    # Always use Groq for transaction extraction
    llm = get_llm(
        provider="groq",
        model="llama-3.3-70b-versatile"
    )
    
    # Universal bank statement extraction prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert Indian bank statement parser. Extract ALL transactions from this bank statement.

Common Indian Bank Statement Formats:
- SBI, HDFC, ICICI, Axis, Kotak, PNB, Bank of Baroda, etc.
- Transactions typically have: Date | Description | Reference | Debit | Credit | Balance
- Date formats: DD-MM-YYYY, DD/MM/YYYY, DD-MMM-YYYY, DD-MMM-YY
- UPI transactions: UPI/P2M/123456789/merchant@bank or UPI-merchant-refno
- NEFT/IMPS/RTGS: followed by reference numbers
- ATM withdrawals: ATM-WDL, ATW, Cash Withdrawal
- POS transactions: POS purchase at merchant
- Credit card payments, bill payments, EMI, loan payments

For EACH transaction found, extract:
- date: Transaction date (convert to DD/MM/YYYY format)
- description: Full merchant/payee description (include UPI IDs, reference numbers, merchant names)
- amount: Transaction amount in INR (positive number, remove commas and currency symbols)
- type: "debit" for money going out (withdrawals, purchases, payments), "credit" for money coming in (deposits, refunds, salary)
- balance: Running balance after this transaction (if available, else use 0)
- raw_text: Original line from statement

IMPORTANT RULES:
1. Extract EVERY single transaction - don't skip any
2. If a field is unclear or missing, use reasonable defaults
3. For UPI transactions, extract the merchant name from the UPI string
4. Amounts must be numbers only (no commas, no ₹ symbol)
5. Determine debit/credit from context: withdrawals/purchases are debits, deposits/refunds are credits
6. Return ONLY a valid JSON array, no explanatory text before or after
7. If balance is not shown, use 0

Example output format:
[
  {{"date": "15/01/2024", "description": "UPI/P2M/123456/SWIGGY@axisbank", "amount": 450.00, "type": "debit", "balance": 25000.00, "raw_text": "15-01-2024 UPI/P2M/123456/SWIGGY 450.00 25000.00"}},
  {{"date": "16/01/2024", "description": "NEFT-SALARY-ACME CORP", "amount": 50000.00, "type": "credit", "balance": 75000.00, "raw_text": "16-01-2024 NEFT CR ACME CORP 50000.00 75000.00"}}
]"""),
        ("human", "Bank Statement Text:\n{statement_text}")
    ])

    try:
        chain = prompt | llm
        
        result = chain.invoke(
            {"statement_text": state["raw_text"]},
            config={
                "run_name": "extract_transactions_groq", 
                "tags": ["extraction", "groq", "llama-3.3-70b"]
            }
        )
        
        # Parse LLM response
        response_text = result.content if hasattr(result, 'content') else str(result)
        
        # Extract JSON from response - handle both ```json blocks and raw JSON
        # First try to find JSON in code blocks
        code_block_match = re.search(r'```(?:json)?\s*\n?(\[.*?\])\s*```', response_text, re.DOTALL)
        if code_block_match:
            json_str = code_block_match.group(1)
        else:
            # Try to find raw JSON array
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
            else:
                raise ValueError("LLM response did not contain valid JSON array")
        
        transactions = json.loads(json_str)
        
        if not transactions or len(transactions) == 0:
            raise ValueError("No transactions extracted from PDF")
        
        state["transactions"] = transactions
        state["extraction_method"] = "groq_llm"
        state["processing_status"] = "llm_extracted"
        
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"✅ Extracted {len(transactions)} transactions from PDF using Groq LLM")
        ]
            
    except json.JSONDecodeError as e:
        error_msg = f"JSON parsing error: {str(e)}"
        state["errors"] = state.get("errors", []) + [error_msg]
        state["transactions"] = get_sample_transactions()
        state["processing_status"] = "using_sample_transactions"
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Failed to parse LLM response as JSON, using sample data. Error: {str(e)}")
        ]
        
    except Exception as e:
        error_msg = f"Transaction extraction error: {str(e)}"
        state["errors"] = state.get("errors", []) + [error_msg]
        state["transactions"] = get_sample_transactions()
        state["processing_status"] = "using_sample_transactions"
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Failed to extract from PDF, using sample data. Error: {str(e)}")
        ]

    return state