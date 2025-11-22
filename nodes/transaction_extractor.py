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
        model="llama-3.3-70b-versatile",
        temperature=0,  # Make output more deterministic
        max_tokens=8000  # Increase from default to handle long statements
    )
    
    # Universal bank statement extraction prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert Indian bank statement parser. Extract ALL transactions from this bank statement.

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
5. Return ONLY JSON array

Example HDFC (notice Withdrawal column has amount):
Input: "01/10/25 UPI-BBNOW-BBNOW.EBZ@HDFCBANK 0000527452791103 01/10/25 945.55 263,745.00"
Columns: Date | Narration | Ref | Value Dt | Withdrawal | Deposit | Balance
Output: {{"date": "01/10/2025", "description": "BBNOW", "amount": 945.55, "type": "debit", "balance": 263745.00}}

Example HDFC Credit (Deposit column has amount):
Input: "15/10/25 NEFT-SALARY-ACME CORP 123456 15/10/25 50000.00 313,745.00"
Output: {{"date": "15/10/2025", "description": "SALARY-ACME CORP", "amount": 50000.00, "type": "credit", "balance": 313745.00}}

Return format:
[
  {{"date": "DD/MM/YYYY", "description": "...", "amount": 0.00, "type": "debit/credit", "balance": 0.00, "raw_text": "..."}}
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
        
        # Debug: Print first 1000 chars of response
        print("\n=== LLM Response (first 1000 chars) ===")
        print(response_text[:1000])
        print("\n=== End Preview ===")
        print(f"Total response length: {len(response_text)} characters")
        
        # Multiple strategies to extract JSON array
        json_str = None
        
        # Strategy 1: MOST RELIABLE - Find first [ to last ]
        # This works even when LLM adds explanatory text
        first_bracket = response_text.find('[')
        last_bracket = response_text.rfind(']')
        print(f"\nBracket positions: first=[{first_bracket}], last=[{last_bracket}]")
        
        if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
            json_str = response_text[first_bracket:last_bracket + 1]
            print(f"Extracted JSON string length: {len(json_str)} characters")
            print(f"First 200 chars of extracted JSON: {json_str[:200]}")
            print(f"Last 200 chars of extracted JSON: {json_str[-200:]}")
            print("✓ Found JSON using bracket matching")
        else:
            print("✗ Bracket matching failed")
        # Strategy 2: Find JSON in code blocks (```json ... ```)
        if not json_str:
            code_block_match = re.search(r'```(?:json)?\s*\n?(\[.*?\])\s*```', response_text, re.DOTALL)
            if code_block_match:
                json_str = code_block_match.group(1)
                print("Found JSON in code block")
        
        if not json_str:
            # Save full response for debugging
            with open("llm_response_debug.txt", "w", encoding="utf-8") as f:
                f.write(response_text)
            raise ValueError(f"LLM response did not contain valid JSON array. Response saved to llm_response_debug.txt. Preview: {response_text[:200]}")
        
        # Clean up the JSON string
        # Remove any trailing commas before closing brackets
        json_str = re.sub(r',\s*\]', ']', json_str)
        json_str = re.sub(r',\s*\}', '}', json_str)
        
        # Try to parse JSON
        print("\nAttempting to parse JSON...")
        try:
            transactions = json.loads(json_str)
            print(f"✓ Successfully parsed JSON! Found {len(transactions)} transactions")
        except json.JSONDecodeError as je:
            print(f"✗ JSON parse failed: {str(je)}")
            print(f"Error at position {je.pos if hasattr(je, 'pos') else 'unknown'}")
            
            # Try fixing common issues
            print("\nAttempting to fix JSON...")
            
            # Fix 1: Replace single quotes with double quotes
            json_str_fixed = json_str.replace("'", '"')
            try:
                transactions = json.loads(json_str_fixed)
                print("✓ Fixed JSON by replacing single quotes")
            except:
                # Fix 2: Try removing trailing commas
                json_str_fixed = re.sub(r',\s*}', '}', json_str_fixed)
                json_str_fixed = re.sub(r',\s*\]', ']', json_str_fixed)
                try:
                    transactions = json.loads(json_str_fixed)
                    print("✓ Fixed JSON by removing trailing commas")
                except Exception as final_error:
                    # Save problematic JSON for debugging
                    with open("json_error_debug.txt", "w", encoding="utf-8") as f:
                        f.write(json_str)
                    print(f"✗ All fixes failed. Saved to json_error_debug.txt")
                    raise ValueError(f"Failed to parse JSON after all fixes. Original error: {str(je)}. Final error: {str(final_error)}")
        
        if not transactions or len(transactions) == 0:
            raise ValueError("No transactions extracted from PDF")
        
        # Validate transaction structure
        required_fields = ['date', 'description', 'amount', 'type']
        for i, txn in enumerate(transactions):
            for field in required_fields:
                if field not in txn:
                    print(f"Warning: Transaction {i} missing field '{field}', adding default")
                    if field == 'type':
                        txn[field] = 'debit'  # Default to debit
                    elif field == 'amount':
                        txn[field] = 0.0
                    else:
                        txn[field] = ''
        
        state["transactions"] = transactions
        state["extraction_method"] = "groq_llm"
        state["processing_status"] = "llm_extracted"
        
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"✅ Extracted {len(transactions)} transactions from PDF using Groq LLM")
        ]
            
    except json.JSONDecodeError as e:
        error_msg = f"JSON parsing error: {str(e)}"
        print(f"\n[ERROR] {error_msg}")
        print("Falling back to sample data...\n")
        state["errors"] = state.get("errors", []) + [error_msg]
        state["transactions"] = get_sample_transactions()
        state["processing_status"] = "fallback_to_sample"
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Failed to parse LLM response as JSON, using sample data. Error: {str(e)}")
        ]
        
    except Exception as e:
        error_msg = f"Transaction extraction error: {str(e)}"
        print(f"\n[ERROR] {error_msg}")
        print("Falling back to sample data...\n")
        state["errors"] = state.get("errors", []) + [error_msg]
        state["transactions"] = get_sample_transactions()
        state["processing_status"] = "fallback_to_sample"
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Failed to extract from PDF, using sample data. Check llm_response_debug.txt for details. Error: {str(e)}")
        ]

    return state