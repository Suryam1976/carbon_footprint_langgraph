"""Node 6: Carbon Footprint Estimation"""

from langchain_core.messages import AIMessage
from core.state import GraphState
from utils.patterns import get_emission_factor, normalize_category

def estimate_carbon_node(state: GraphState) -> GraphState:
    """
    Node 6: Calculate carbon footprint for categorized transactions
    High-value transactions already filtered out in Node 3
    """
    carbon_estimates = []
    total_carbon_min = 0
    total_carbon_max = 0
    total_carbon_avg = 0
    
    for transaction in state.get("categorized_transactions", []):
        category = transaction.get("category", "miscellaneous")
        # Normalize category to ensure it's in official list
        category = normalize_category(category)
        
        # Handle both nested and flat transaction structures
        if "transaction" in transaction:
            amount = transaction["transaction"].get("amount", 0)
            description = transaction["transaction"].get("description", "")
        else:
            amount = transaction.get("amount", 0)
            description = transaction.get("description", "")
        
        # Get emission factor for category
        emission_factor = get_emission_factor(category)
        
        # Calculate carbon footprint (amount in thousands of rupees)
        amount_thousands = amount / 1000
        carbon_min = amount_thousands * emission_factor["min"]
        carbon_max = amount_thousands * emission_factor["max"]
        carbon_avg = (carbon_min + carbon_max) / 2
        
        # Create carbon estimate (no high-value checks needed)
        carbon_estimate = {
            **transaction,
            "carbon_kg_min": round(carbon_min, 2),
            "carbon_kg_max": round(carbon_max, 2),
            "carbon_kg_avg": round(carbon_avg, 2),
            "emission_factor_min": emission_factor["min"],
            "emission_factor_max": emission_factor["max"],
            "emission_factor_notes": emission_factor.get("notes", "")
        }
        
        carbon_estimates.append(carbon_estimate)
        
        # Add to totals
        total_carbon_min += carbon_min
        total_carbon_max += carbon_max
        total_carbon_avg += carbon_avg
    
    state["carbon_estimates"] = carbon_estimates
    state["total_carbon_kg_min"] = round(total_carbon_min, 2)
    state["total_carbon_kg_max"] = round(total_carbon_max, 2)
    state["total_carbon_kg_avg"] = round(total_carbon_avg, 2)
    
    # Build messages
    messages = [
        AIMessage(content=f"✅ Carbon footprint calculated for {len(carbon_estimates)} transactions"),
        AIMessage(content=f"📊 Total estimated emissions: {round(total_carbon_avg, 1)} kg CO2e")
    ]
    
    state["messages"] = state.get("messages", []) + messages
    
    return state

