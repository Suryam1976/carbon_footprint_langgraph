"""Configuration and constants"""

import os

# LangSmith Configuration
LANGSMITH_PROJECT = os.getenv("LANGCHAIN_PROJECT", "carbon-footprint-analyzer")

def get_langsmith_config():
    """Get LangSmith configuration for tracing"""
    return {
        "callbacks": [],
        "tags": ["carbon-footprint", "indian-bank-statement"],
        "metadata": {
            "version": "2.0",
            "features": ["pii-redaction", "hybrid-categorization", "min-max-ranges"]
        }
    }

# Default models
DEFAULT_ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"

# Pipeline configuration
HIGH_VALUE_THRESHOLD = 50000  # ₹ — transactions >= this are excluded from
# spend-based carbon estimation (activity-based estimation would be needed instead)

LLM_CATEGORIZATION_BATCH_SIZE = 25  # max transactions sent to LLM per call
# (keeping token budget safe for uncategorized transaction batches)