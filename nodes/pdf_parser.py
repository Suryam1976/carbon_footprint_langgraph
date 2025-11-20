"""Node 1: PDF Parsing"""

import re
from langchain_core.messages import AIMessage
from core.state import GraphState
from utils.sample_data import get_sample_statement_text, get_sample_transactions

def parse_pdf_node(state: GraphState) -> GraphState:
    """
    Node 1: Parse PDF bank statement or use sample data
    Extracts raw text from PDF for LLM processing
    """
    
    pdf_path = state.get("pdf_path")
    
    if not pdf_path:
        # Use sample data
        state["raw_text"] = get_sample_statement_text()
        state["transactions"] = get_sample_transactions()
        state["processing_status"] = "using_sample_data"
        state["messages"] = [
            AIMessage(content="📄 Using sample bank statement data for demonstration")
        ]
        return state
    
    try:
        # Try to parse PDF
        import fitz  # PyMuPDF
        
        raw_text = ""
        
        # Use PyMuPDF for text extraction
        try:
            doc = fitz.open(pdf_path)
            
            # Check if password protected
            if doc.is_encrypted:
                password = state.get("pdf_password", "")
                if password:
                    if not doc.authenticate(password):
                        raise ValueError("Invalid PDF password")
                else:
                    raise ValueError("PDF is password protected but no password provided")
            
            for page in doc:
                raw_text += page.get_text()
            doc.close()
            
            if raw_text.strip():
                state["raw_text"] = raw_text
                state["processing_status"] = "pdf_parsed"
                state["messages"] = [
                    AIMessage(content=f"📄 Successfully parsed PDF: {pdf_path}")
                ]
                return state
            else:
                raise ValueError("No text extracted from PDF - may be scanned/image-based")
                
        except Exception as e:
            raise ValueError(f"Failed to parse PDF: {str(e)}")
            
    except Exception as e:
        # Fallback to sample data
        error_msg = f"PDF parsing error: {str(e)}"
        state["errors"] = [error_msg]
        state["raw_text"] = get_sample_statement_text()
        state["transactions"] = get_sample_transactions()
        state["processing_status"] = "using_sample_data"
        state["messages"] = [
            AIMessage(content=f"⚠️ PDF parsing failed, using sample data. Error: {str(e)}")
        ]
    
    return state
