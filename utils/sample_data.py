"""Sample data functions for testing and demonstration"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
import random

def get_sample_statement_text() -> str:
    """Get sample bank statement text for testing"""
    return """
AXIS BANK LIMITED
BANK STATEMENT
Account Number: 1234567890
Statement Period: 01-Nov-2024 to 30-Nov-2024

Date        Description                           Debit    Credit   Balance
01-Nov-24   SALARY CREDIT                                  75000    75000
02-Nov-24   UPI-SWIGGY-9876543210                 450               74550
03-Nov-24   UPI-UBER-JOHN@PAYTM                   280               74270
05-Nov-24   NEFT-ELECTRICITY BILL                 2500              71770
07-Nov-24   UPI-BIGBASKET-8765432109              1200              70570
10-Nov-24   ATM-CASH WITHDRAWAL                   5000              65570
12-Nov-24   UPI-ZOMATO-7654321098                 320               65250
15-Nov-24   FUEL-INDIAN OIL-1234567890            3500              61750
18-Nov-24   UPI-AMAZON-6543210987                 850               60900
20-Nov-24   MOVIE-PVR CINEMAS                     600               60300
22-Nov-24   UPI-MYNTRA-5432109876                 1200              59100
25-Nov-24   GROCERY-DMART                         2800              56300
28-Nov-24   UPI-OLA-4321098765                    180               56120
30-Nov-24   INTEREST CREDIT                                 45      56165
"""

def get_sample_transactions() -> List[Dict[str, Any]]:
    """Get sample transactions for testing"""
    return [
        {
            "date": "2024-11-02",
            "description": "UPI-SWIGGY-9876543210",
            "amount": 450,
            "type": "debit",
            "balance": 74550
        },
        {
            "date": "2024-11-03", 
            "description": "UPI-UBER-JOHN@PAYTM",
            "amount": 280,
            "type": "debit",
            "balance": 74270
        },
        {
            "date": "2024-11-05",
            "description": "NEFT-ELECTRICITY BILL",
            "amount": 2500,
            "type": "debit", 
            "balance": 71770
        },
        {
            "date": "2024-11-07",
            "description": "UPI-BIGBASKET-8765432109",
            "amount": 1200,
            "type": "debit",
            "balance": 70570
        },
        {
            "date": "2024-11-10",
            "description": "ATM-CASH WITHDRAWAL",
            "amount": 5000,
            "type": "debit",
            "balance": 65570
        },
        {
            "date": "2024-11-12",
            "description": "UPI-ZOMATO-7654321098", 
            "amount": 320,
            "type": "debit",
            "balance": 65250
        },
        {
            "date": "2024-11-15",
            "description": "FUEL-INDIAN OIL-1234567890",
            "amount": 3500,
            "type": "debit",
            "balance": 61750
        },
        {
            "date": "2024-11-18",
            "description": "UPI-AMAZON-6543210987",
            "amount": 850,
            "type": "debit",
            "balance": 60900
        },
        {
            "date": "2024-11-20",
            "description": "MOVIE-PVR CINEMAS",
            "amount": 600,
            "type": "debit",
            "balance": 60300
        },
        {
            "date": "2024-11-22",
            "description": "UPI-MYNTRA-5432109876",
            "amount": 1200,
            "type": "debit",
            "balance": 59100
        },
        {
            "date": "2024-11-25",
            "description": "GROCERY-DMART",
            "amount": 2800,
            "type": "debit",
            "balance": 56300
        },
        {
            "date": "2024-11-28",
            "description": "UPI-OLA-4321098765",
            "amount": 180,
            "type": "debit",
            "balance": 56120
        },
        # Credit transactions (should be filtered out)
        {
            "date": "2024-11-01",
            "description": "SALARY CREDIT",
            "amount": 75000,
            "type": "credit",
            "balance": 75000
        },
        {
            "date": "2024-11-30",
            "description": "INTEREST CREDIT", 
            "amount": 45,
            "type": "credit",
            "balance": 56165
        }
    ]

def get_sample_redacted_transactions() -> List[Dict[str, Any]]:
    """Get sample redacted transactions (debits only)"""
    transactions = get_sample_transactions()
    
    # Filter only debits and redact PII
    redacted = []
    for txn in transactions:
        if txn["type"] == "debit":
            redacted_desc = redact_description(txn["description"])
            redacted.append({
                **txn,
                "description": redacted_desc,
                "original_description": txn["description"]
            })
    
    return redacted

def redact_description(description: str) -> str:
    """Redact PII from transaction description"""
    import re
    
    # Redact mobile numbers (10 digits)
    description = re.sub(r'\b\d{10}\b', '[MOBILE_REDACTED]', description)
    
    # Redact UPI IDs (email-like patterns)
    description = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\b', '[UPI_ID_REDACTED]', description)
    
    # Redact account numbers (longer digit sequences)
    description = re.sub(r'\b\d{8,}\b', '[ACCOUNT_REDACTED]', description)
    
    return description

def get_sample_categorized_transactions() -> List[Dict[str, Any]]:
    """Get sample categorized transactions"""
    redacted = get_sample_redacted_transactions()
    
    # Add categories based on merchant patterns
    categories = {
        "SWIGGY": "food_delivery",
        "UBER": "transport_ride_sharing", 
        "ELECTRICITY": "housing_utilities",
        "BIGBASKET": "food_groceries",
        "CASH WITHDRAWAL": "miscellaneous",
        "ZOMATO": "food_delivery",
        "INDIAN OIL": "transport_fuel",
        "AMAZON": "shopping_online",
        "PVR CINEMAS": "recreation_entertainment",
        "MYNTRA": "shopping_clothing",
        "DMART": "food_groceries",
        "OLA": "transport_ride_sharing"
    }
    
    categorized = []
    for txn in redacted:
        category = "miscellaneous"
        for merchant, cat in categories.items():
            if merchant in txn["description"].upper():
                category = cat
                break
        
        categorized.append({
            **txn,
            "category": category,
            "categorization_method": "rule_based" if category != "miscellaneous" else "llm_based"
        })
    
    return categorized

def get_sample_carbon_estimates() -> List[Dict[str, Any]]:
    """Get sample carbon estimates"""
    categorized = get_sample_categorized_transactions()
    
    # Emission factors (kg CO2e per ₹1000)
    emission_factors = {
        "food_delivery": {"min": 8, "max": 15},
        "transport_ride_sharing": {"min": 25, "max": 40},
        "housing_utilities": {"min": 12, "max": 20},
        "food_groceries": {"min": 6, "max": 12},
        "transport_fuel": {"min": 30, "max": 45},
        "shopping_online": {"min": 5, "max": 10},
        "recreation_entertainment": {"min": 3, "max": 8},
        "shopping_clothing": {"min": 8, "max": 15},
        "miscellaneous": {"min": 5, "max": 10}
    }
    
    estimates = []
    for txn in categorized:
        factor = emission_factors.get(txn["category"], {"min": 5, "max": 10})
        amount_thousands = txn["amount"] / 1000
        
        carbon_min = amount_thousands * factor["min"]
        carbon_max = amount_thousands * factor["max"]
        carbon_avg = (carbon_min + carbon_max) / 2
        
        estimates.append({
            **txn,
            "carbon_kg_min": round(carbon_min, 2),
            "carbon_kg_max": round(carbon_max, 2),
            "carbon_kg_avg": round(carbon_avg, 2),
            "emission_factor_min": factor["min"],
            "emission_factor_max": factor["max"]
        })
    
    return estimates

def get_sample_analysis_result() -> Dict[str, Any]:
    """Get complete sample analysis result"""
    carbon_estimates = get_sample_carbon_estimates()
    
    # Calculate totals
    total_min = sum(est["carbon_kg_min"] for est in carbon_estimates)
    total_max = sum(est["carbon_kg_max"] for est in carbon_estimates)
    total_avg = sum(est["carbon_kg_avg"] for est in carbon_estimates)
    
    # Category breakdown
    category_totals = {}
    for est in carbon_estimates:
        cat = est["category"]
        if cat not in category_totals:
            category_totals[cat] = {"min": 0, "max": 0, "avg": 0, "count": 0}
        category_totals[cat]["min"] += est["carbon_kg_min"]
        category_totals[cat]["max"] += est["carbon_kg_max"] 
        category_totals[cat]["avg"] += est["carbon_kg_avg"]
        category_totals[cat]["count"] += 1
    
    # Efficiency stats
    rule_based_count = sum(1 for est in carbon_estimates if est["categorization_method"] == "rule_based")
    llm_based_count = len(carbon_estimates) - rule_based_count
    
    return {
        "carbon_estimates": carbon_estimates,
        "total_carbon_kg_min": round(total_min, 2),
        "total_carbon_kg_max": round(total_max, 2),
        "total_carbon_kg_avg": round(total_avg, 2),
        "category_breakdown": category_totals,
        "rule_based_count": rule_based_count,
        "llm_based_count": llm_based_count,
        "total_transactions": len(carbon_estimates),
        "processing_status": "using_sample_data",
        "pii_redacted_count": 8,
        "credits_filtered_count": 2,
        "recommendations": [
            "Switch to metro/public transport to reduce ride-sharing emissions by 30%",
            "Consider meal planning to reduce food delivery frequency by 25%", 
            "Use energy-efficient appliances to lower utility emissions by 15%",
            "Buy local products when possible to reduce shopping emissions by 10%"
        ],
        "messages": [
            {"role": "assistant", "content": "Using sample bank statement data for demonstration"},
            {"role": "assistant", "content": f"Processed {len(carbon_estimates)} debit transactions"},
            {"role": "assistant", "content": f"Rule-based categorization: {rule_based_count} transactions"},
            {"role": "assistant", "content": f"LLM categorization: {llm_based_count} transactions"}
        ]
    }