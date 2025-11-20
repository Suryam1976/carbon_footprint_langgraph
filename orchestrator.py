"""
🌱 LangGraph Orchestrator for Carbon Footprint Analysis

Simple, clean orchestration of the 8-node workflow:
PDF → Extract → Redact → Rule → LLM → Carbon → Aggregate → Insights
"""

from datetime import datetime
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from core.state import GraphState
from nodes import (
    parse_pdf_node,
    extract_transactions_node,
    redact_pii_node,
    rule_based_categorization_node,
    llm_categorization_node,
    estimate_carbon_node,
    aggregate_results_node,
    generate_insights_node
)

def create_carbon_footprint_graph() -> StateGraph:
    """
    Create the LangGraph workflow for carbon footprint estimation
    
    Graph Flow (8 Nodes):
    START → parse_pdf → extract_transactions → redact_pii 
          → rule_based_categorization → llm_categorization 
          → estimate_carbon → aggregate_results → generate_insights → END
    """
    
    workflow = StateGraph(GraphState)
    
    # Add all 8 nodes
    workflow.add_node("parse_pdf", parse_pdf_node)
    workflow.add_node("extract_transactions", extract_transactions_node)
    workflow.add_node("redact_pii", redact_pii_node)
    workflow.add_node("rule_based_categorization", rule_based_categorization_node)
    workflow.add_node("llm_categorization", llm_categorization_node)
    workflow.add_node("estimate_carbon", estimate_carbon_node)
    workflow.add_node("aggregate_results", aggregate_results_node)
    workflow.add_node("generate_insights", generate_insights_node)
    
    # Define linear flow
    workflow.set_entry_point("parse_pdf")
    workflow.add_edge("parse_pdf", "extract_transactions")
    workflow.add_edge("extract_transactions", "redact_pii")
    workflow.add_edge("redact_pii", "rule_based_categorization")
    workflow.add_edge("rule_based_categorization", "llm_categorization")
    workflow.add_edge("llm_categorization", "estimate_carbon")
    workflow.add_edge("estimate_carbon", "aggregate_results")
    workflow.add_edge("aggregate_results", "generate_insights")
    workflow.add_edge("generate_insights", END)
    
    return workflow

def run_carbon_analysis(pdf_path: str = None, password: str = None, 
                       llm_provider: str = "anthropic", llm_model: str = None) -> dict:
    """
    🚀 Main entry point to run carbon footprint analysis
    
    Args:
        pdf_path: Path to PDF bank statement (optional)
        password: PDF password if required (optional)
        llm_provider: "anthropic" or "groq" (default: "anthropic")
        llm_model: Specific model name (optional)
    
    Returns:
        Complete analysis results
    """
    # Create and compile graph
    workflow = create_carbon_footprint_graph()
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    # Initialize state
    initial_state = {
        "pdf_path": pdf_path or "",
        "pdf_password": password or "",
        "llm_provider": llm_provider,
        "llm_model": llm_model or "",
        "bank_type": "",
        "extraction_method": "",
        "raw_text": "",
        "transactions": [],
        "redacted_transactions": [],
        "rule_categorized": [],
        "uncategorized": [],
        "categorized_transactions": [],
        "carbon_estimates": [],
        "total_carbon_kg_min": 0.0,
        "total_carbon_kg_max": 0.0,
        "total_carbon_kg_avg": 0.0,
        "category_breakdown": {},
        "monthly_breakdown": {},
        "rule_based_count": 0,
        "llm_based_count": 0,
        "pii_redacted_count": 0,
        "recommendations": [],
        "insights": [],
        "messages": [],
        "errors": [],
        "processing_status": "initialized"
    }
    
    # Run with LangSmith tracing
    config = {
        "configurable": {"thread_id": f"carbon-analysis-{datetime.now().strftime('%Y%m%d-%H%M%S')}"},
        "run_name": "carbon_footprint_analysis",
        "tags": ["carbon-footprint", "indian-bank", "pii-redaction", llm_provider],
        "metadata": {
            "pdf_provided": bool(pdf_path),
            "password_provided": bool(password),
            "llm_provider": llm_provider,
            "llm_model": llm_model or "default",
            "timestamp": datetime.now().isoformat()
        }
    }
    
    result = app.invoke(initial_state, config)
    return result

if __name__ == "__main__":
    print("🌱 Carbon Footprint LangGraph Orchestrator")
    print("=" * 50)
    
    # Simple test run
    result = run_carbon_analysis()
    
    print(f"✅ Analysis complete!")
    print(f"📊 Carbon Range: {result['total_carbon_kg_min']:.2f} - {result['total_carbon_kg_max']:.2f} kg CO2e")
    print(f"🔒 PII Redacted: {result.get('pii_redacted_count', 0)} fields")
    print(f"🚀 Rule-based: {result.get('rule_based_count', 0)} transactions")
    print(f"🤖 LLM-based: {result.get('llm_based_count', 0)} transactions")