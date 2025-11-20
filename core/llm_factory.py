"""LLM factory for different providers"""

import os
from .config import DEFAULT_ANTHROPIC_MODEL, DEFAULT_GROQ_MODEL

def get_llm(provider: str = "anthropic", model: str = None):
    """
    Initialize LLM with choice between Groq and Anthropic
    
    Args:
        provider: "anthropic" or "groq"
        model: Specific model name (optional)
    
    Returns:
        Configured LLM instance
    """
    if provider.lower() == "groq":
        from langchain_groq import ChatGroq
        
        if not model:
            model = DEFAULT_GROQ_MODEL
        
        return ChatGroq(
            model=model,
            temperature=0.1,
            max_tokens=4096,
            groq_api_key=os.getenv("GROQ_API_KEY")
        )
    
    elif provider.lower() == "anthropic":
        from langchain_anthropic import ChatAnthropic
        
        if not model:
            model = DEFAULT_ANTHROPIC_MODEL
        
        return ChatAnthropic(
            model=model,
            temperature=0.1,
            max_tokens=4096,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
        )
    
    else:
        raise ValueError(f"Unsupported provider: {provider}. Choose 'anthropic' or 'groq'")