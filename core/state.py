"""State definitions for LangGraph workflow"""

from typing import TypedDict, Annotated, Sequence, Literal
from langchain_core.messages import BaseMessage

class Transaction(TypedDict):
    """Individual transaction from bank statement"""
    date: str
    description: str
    amount: float
    type: str  # debit/credit
    balance: float
    raw_text: str

class RedactedTransaction(TypedDict):
    """Transaction with PII redacted for LLM processing"""
    date: str
    description: str  # Redacted description
    original_description: str  # Original for final report
    amount: float
    type: str
    balance: float
    raw_text: str
    redaction_applied: bool
    redacted_fields: list[str]

class CategorizedTransaction(RedactedTransaction):
    """Flat structure — all RedactedTransaction fields plus categorization fields.
    Matches what rule_categorizer.py and llm_categorizer.py actually produce
    via **transaction spreads. (Previously declared as nested {"transaction": {...},
    "category": ...}, which did not match runtime reality.)"""
    category: str
    categorization_method: str  # 'rule_based' | 'llm_based' | 'fallback'

class CarbonEstimate(CategorizedTransaction):
    """Flat structure — matches carbon_estimator.py's **transaction spread.
    Field names match actual runtime keys (carbon_kg_*, not co2_kg_*)."""
    carbon_kg_min: float
    carbon_kg_max: float
    carbon_kg_avg: float
    emission_factor_min: float
    emission_factor_max: float
    emission_factor_notes: str

class GraphState(TypedDict):
    """Main state for the LangGraph workflow"""
    # Input
    pdf_path: str
    pdf_password: str
    raw_text: str
    
    # LLM Configuration
    llm_provider: str  # "anthropic" or "groq"
    llm_model: str     # Specific model name
    
    # Bank detection
    bank_type: str     # "axis_bank", "hdfc", "icici", etc.
    extraction_method: str  # "groq_axis_bank", "anthropic_generic", etc.
    
    # Processing stages
    transactions: list[Transaction]
    redacted_transactions: list[RedactedTransaction]
    filtered_transactions: list[RedactedTransaction]  # NEW: After high-value filter
    rule_categorized: list[CategorizedTransaction]
    uncategorized: list[RedactedTransaction]
    categorized_transactions: list[CategorizedTransaction]
    carbon_estimates: list[CarbonEstimate]
    
    # Aggregated results
    total_carbon_kg_min: float
    total_carbon_kg_max: float
    total_carbon_kg_avg: float
    category_breakdown: dict
    monthly_breakdown: dict
    
    # Categorization & Redaction stats
    rule_based_count: int
    llm_based_count: int
    pii_redacted_count: int
    
    # High-value transaction tracking (moved earlier in pipeline)
    high_value_transactions: list[dict]  # Transactions ≥₹50,000 (excluded from analysis)
    high_value_count: int
    
    # Processing metadata
    recommendations: list[str]
    insights: list[str]
    messages: list
    errors: list[str]
    processing_status: str

