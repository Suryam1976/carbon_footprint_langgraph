"""Node 7: Results Aggregation"""

from langchain_core.messages import AIMessage
from core.state import GraphState
from utils.patterns import get_category_display_name

def aggregate_results_node(state: GraphState) -> GraphState:
    """
    Node 7: Aggregate carbon footprint results by category
    """
    carbon_estimates = state.get("carbon_estimates", [])
    
    # Category breakdown
    category_totals = {}
    category_counts = {}
    
    for estimate in carbon_estimates:
        category = estimate.get("category", "miscellaneous")
        
        if category not in category_totals:
            category_totals[category] = {
                "min": 0,
                "max": 0, 
                "avg": 0,
                "amount_spent": 0,
                "emission_factor_min": estimate.get("emission_factor_min", 0),
                "emission_factor_max": estimate.get("emission_factor_max", 0)
            }
            category_counts[category] = 0
        
        category_totals[category]["min"] += estimate.get("carbon_kg_min", 0)
        category_totals[category]["max"] += estimate.get("carbon_kg_max", 0)
        category_totals[category]["avg"] += estimate.get("carbon_kg_avg", 0)
        category_totals[category]["amount_spent"] += estimate.get("amount", 0)
        category_counts[category] += 1
    
    # Round values and add display names
    for category in category_totals:
        category_totals[category]["total_co2_kg_min"] = round(category_totals[category]["min"], 2)
        category_totals[category]["total_co2_kg_max"] = round(category_totals[category]["max"], 2)
        category_totals[category]["total_co2_kg_avg"] = round(category_totals[category]["avg"], 2)
        category_totals[category]["total_spend"] = round(category_totals[category]["amount_spent"], 2)
        category_totals[category]["count"] = category_counts[category]
        category_totals[category]["display_name"] = get_category_display_name(category)
        # Keep backwards compatibility
        category_totals[category]["min"] = category_totals[category]["total_co2_kg_min"]
        category_totals[category]["max"] = category_totals[category]["total_co2_kg_max"]
        category_totals[category]["avg"] = category_totals[category]["total_co2_kg_avg"]
    
    # Sort by carbon footprint (descending)
    sorted_categories = sorted(
        category_totals.items(),
        key=lambda x: x[1]["avg"],
        reverse=True
    )
    
    # Efficiency metrics
    rule_based_count = state.get("rule_based_count", 0)
    llm_based_count = state.get("llm_based_count", 0)
    total_transactions = len(carbon_estimates)
    
    # Processing summary
    processing_summary = {
        "total_transactions": total_transactions,
        "rule_based_count": rule_based_count,
        "llm_based_count": llm_based_count,
        "pii_redacted_count": state.get("pii_redacted_count", 0),
        "credits_filtered_count": state.get("credits_filtered_count", 0),
        "processing_status": state.get("processing_status", "completed")
    }
    
    state["category_breakdown"] = dict(category_totals)
    state["sorted_categories"] = sorted_categories
    state["processing_summary"] = processing_summary
    
    # Find top emission categories
    top_3_categories = [cat[0] for cat in sorted_categories[:3]]
    top_3_display = [get_category_display_name(cat) for cat in top_3_categories]
    
    state["messages"] = state.get("messages", []) + [
        AIMessage(content=f"✅ Results aggregated across {len(category_totals)} categories"),
        AIMessage(content=f"🔥 Top emission categories: {', '.join(top_3_display)}")
    ]
    
    return state