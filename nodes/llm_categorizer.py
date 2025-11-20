"""Node 5: LLM-based Categorization"""

import json
import re
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from core.state import GraphState
from core.llm_factory import get_llm
from utils.patterns import get_all_categories, normalize_category

def llm_categorization_node(state: GraphState) -> GraphState:
    """
    Node 5: Use LLM to categorize remaining transactions
    """
    uncategorized = state.get("uncategorized", [])
    
    if not uncategorized:
        state["messages"] = state.get("messages", []) + [
            AIMessage(content="✅ No transactions need LLM categorization")
        ]
        return state
    
    # Get LLM
    llm = get_llm(
        provider=state.get("llm_provider", "anthropic"),
        model=state.get("llm_model", "claude-3-5-haiku-20241022")
    )
    
    # Prepare categories list
    categories = get_all_categories()
    categories_text = "\n".join([f"- {cat}" for cat in categories])
    
    # Create categorization prompt with strict category enforcement
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are a transaction categorizer for carbon footprint analysis.

You MUST use ONLY these exact categories (no others allowed):
{categories_text}

For each transaction, assign the most appropriate category based on the merchant/description.
Return JSON array with format: [{{{{"index": 0, "category": "category_name"}}}}]

IMPORTANT: 
- Use ONLY the exact category names listed above
- Use "miscellaneous" if no category fits well
- Do NOT create new categories or variations"""),
        ("human", "Transactions to categorize:\n{transactions}")
    ])
    
    try:
        # Format transactions for LLM
        transactions_text = ""
        for i, txn in enumerate(uncategorized):
            transactions_text += f"{i}: {txn.get('description', '')} - ₹{txn.get('amount', 0)}\n"
        
        chain = prompt | llm
        result = chain.invoke(
            {"transactions": transactions_text},
            config={
                "run_name": "llm_categorization",
                "tags": ["categorization", state.get("llm_provider", "anthropic")]
            }
        )
        
        # Parse LLM response
        response_text = result.content if hasattr(result, 'content') else str(result)
        
        # Extract JSON from response
        json_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
        
        if json_match:
            categorizations = json.loads(json_match.group())
            
            # Apply categorizations with normalization
            llm_categorized = []
            for cat_result in categorizations:
                idx = cat_result.get("index", 0)
                category = cat_result.get("category", "miscellaneous")
                
                # Normalize category to official list
                category = normalize_category(category)
                
                if 0 <= idx < len(uncategorized):
                    categorized_txn = {
                        **uncategorized[idx],
                        "category": category,
                        "categorization_method": "llm_based"
                    }
                    llm_categorized.append(categorized_txn)
            
            # Combine with rule-based categorizations
            all_categorized = state.get("rule_categorized", []) + llm_categorized
            state["categorized_transactions"] = all_categorized
            state["llm_based_count"] = len(llm_categorized)
            
            state["messages"] = state.get("messages", []) + [
                AIMessage(content=f"✅ LLM categorization: {len(llm_categorized)} transactions")
            ]
        else:
            raise ValueError("LLM response did not contain valid JSON")
            
    except Exception as e:
        # Fallback: categorize as miscellaneous
        fallback_categorized = []
        for txn in uncategorized:
            fallback_txn = {
                **txn,
                "category": "miscellaneous",
                "categorization_method": "fallback"
            }
            fallback_categorized.append(fallback_txn)
        
        all_categorized = state.get("rule_categorized", []) + fallback_categorized
        state["categorized_transactions"] = all_categorized
        state["llm_based_count"] = len(fallback_categorized)
        
        error_msg = f"LLM categorization error: {str(e)}"
        state["errors"] = state.get("errors", []) + [error_msg]
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"⚠️ LLM categorization failed, using fallback. Error: {str(e)}")
        ]
    
    return state