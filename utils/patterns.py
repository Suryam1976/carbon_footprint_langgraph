"""Merchant patterns and emission factors for categorization"""

from typing import Dict, List, Optional

# Official categories from SpendCategory-EmissionFactorkgCO2e1000.csv
# These are the ONLY allowed categories - no new ones should be added

OFFICIAL_CATEGORIES = [
    "food_and_groceries",
    "housing_and_utilities",
    "transport",
    "clothing_and_footwear",
    "household_goods_and_appliances",
    "healthcare_and_personal_care",
    "education_and_communication",
    "recreation_and_leisure",
    "financial_services_and_insurance",
    "miscellaneous"
]

# Indian merchant patterns for rule-based categorization
# Maps to official categories only
INDIAN_MERCHANT_PATTERNS = {
    "food_and_groceries": [
        "swiggy", "zomato", "foodpanda", "ubereats", "dunzo",
        "bigbasket", "grofers", "amazon fresh", "flipkart grocery",
        "dmart", "reliance fresh", "spencer", "more", "grocery",
        "supermarket", "kirana", "vegetables", "fruits", "restaurant",
        "food delivery", "online food", "cafe", "bakery", "meat",
        "chicken", "fish", "dairy", "milk", "bread",
        # BigBasket variants
        "bbnow", "bbdaily", "big basket", "bb now", "bb daily",
        # Other food delivery and grocery
        "dominos", "pizza hut", "kfc", "mcdonald", "burger king",
        "akshayakalpa", "licious", "freshmenu", "faasos",
        # Local stores and markets
        "super market", "retail", "provisions", "general store"
    ],
    "housing_and_utilities": [
        "electricity", "water", "gas", "lpg", "utility", "power",
        "bescom", "mseb", "tneb", "bses", "tata power", "adani",
        "rent", "maintenance", "society", "apartment", "flat",
        "housing", "property tax", "municipal"
    ],
    "transport": [
        "uber", "ola", "rapido", "auto", "taxi", "cab", "ride",
        "indian oil", "bharat petroleum", "hindustan petroleum", "shell",
        "essar", "fuel", "petrol", "diesel", "cng", "gas station",
        "metro", "bus", "railway", "irctc", "bmtc", "best", "dtc",
        "public transport", "train", "local train", "parking", "toll",
        "fastag",
        # Travel booking platforms - primarily for transport
        "makemytrip", "goibibo", "cleartrip", "yatra", "booking.com",
        "oyo", "hotel", "airbnb", "travel", "flight", "airline",
        "airways", "indigo", "spicejet", "air india", "vistara"
    ],
    "clothing_and_footwear": [
        "myntra", "ajio", "max fashion", "lifestyle", "pantaloons",
        "westside", "clothing", "fashion", "apparel", "zara", "h&m",
        "shoes", "footwear", "bata", "nike", "adidas", "puma",
        "garments", "textile", "fabrics"
    ],
    "household_goods_and_appliances": [
        "amazon", "flipkart", "croma", "reliance digital", "vijay sales",
        "electronics", "mobile", "laptop", "tv", "appliance",
        "furniture", "ikea", "pepperfry", "urban ladder", "home decor",
        "kitchen", "utensils", "bedding"
    ],
    "healthcare_and_personal_care": [
        "apollo", "fortis", "max healthcare", "hospital", "clinic",
        "pharmacy", "medicine", "doctor", "medical", "diagnostic",
        "lab", "pathology", "dental", "eye", "optical",
        "salon", "spa", "beauty", "cosmetics", "nykaa", "personal care",
        # Salons and grooming
        "unisex salon", "unisex saloon", "hair salon", "hair studio",
        "barber", "parlour", "parlor", "grooming", "haircut",
        # Personal care services
        "urban company", "at home services", "housejoy",
        # Healthcare facilities
        "arete hospital", "care hospital", "rainbow hospital",
        "apollo pharmacy", "medplus", "netmeds", "pharmeasy"
    ],
    "education_and_communication": [
        "school", "college", "university", "course", "tuition",
        "education", "fees", "books", "stationery", "udemy", "coursera",
        "airtel", "jio", "vodafone", "vi", "bsnl", "internet",
        "mobile recharge", "broadband", "wifi", "telephone"
    ],
    "recreation_and_leisure": [
        # Entertainment and leisure activities (NOT travel booking)
        "pvr", "inox", "cinepolis", "movie", "cinema",
        "netflix", "amazon prime", "hotstar", "disney", "sony liv",
        "spotify", "gaana", "youtube premium", "entertainment",
        "game", "gaming", "steam", "playstation", "xbox",
        "sports", "gym", "fitness", "cult fit", "gold's gym",
        "holiday", "tourism", "amusement park", "zoo", "museum"
    ],
    "financial_services_and_insurance": [
        "insurance", "lic", "hdfc life", "icici prudential",
        "mutual fund", "sip", "investment", "loan", "emi",
        "credit card", "bank charges", "demat", "trading", "zerodha",
        "groww", "upstox"
    ],
    "miscellaneous": [
        "atm", "cash", "withdrawal", "transfer", "upi", "neft", "imps",
        "rtgs", "cheque", "demand draft"
    ]
}

# Emission factors (kg CO2e per ₹1000 spent)
# Based on SpendCategory-EmissionFactorkgCO2e1000.csv
EMISSION_FACTORS = {
    "food_and_groceries": {
        "min": 7, "max": 15,
        "source": "NSSO-linked supply chain studies; household footprint",
        "notes": "Varies by diet (higher for meat, lower for cereals/veg)"
    },
    "housing_and_utilities": {
        "min": 10, "max": 20,
        "source": "India GHG inventory; energy spend research",
        "notes": "Region/energy mix; urban households often higher"
    },
    "transport": {
        "min": 20, "max": 40,
        "source": "Transport emission factors; fuel use studies",
        "notes": "Vehicle type, efficiency, usage frequency"
    },
    "clothing_and_footwear": {
        "min": 5, "max": 10,
        "source": "Input-output modelling; household expenditure",
        "notes": "Imported goods, luxury items on higher side"
    },
    "household_goods_and_appliances": {
        "min": 5, "max": 10,
        "source": "Consumption and durable goods footprint studies",
        "notes": "Tech products, large furniture slightly above mean"
    },
    "healthcare_and_personal_care": {
        "min": 3, "max": 7,
        "source": "Service-based emission inventories; household study",
        "notes": "Pharmaceutics and hospital services drive upper bound"
    },
    "education_and_communication": {
        "min": 1, "max": 5,
        "source": "Expenditure/emission correlation (services)",
        "notes": "Digital/online activity lower, sector growing emissions"
    },
    "recreation_and_leisure": {
        "min": 2, "max": 8,
        "source": "Indian consumption/emission category analysis",
        "notes": "Travel (air/car) pushes value up significantly"
    },
    "financial_services_and_insurance": {
        "min": 1, "max": 3,
        "source": "Household indirect emissions; admin activities",
        "notes": "Largely administrative; negligible direct emissions"
    },
    "miscellaneous": {
        "min": 2, "max": 6,
        "source": "Retail/service studies; gifts, minor purchases",
        "notes": "Wide spread depending on nature of product/service"
    }
}

def categorize_transaction(description: str) -> Optional[str]:
    """
    Categorize transaction based on merchant patterns
    
    Args:
        description: Transaction description
        
    Returns:
        Category name if matched, None otherwise
    """
    description_lower = description.lower()
    
    for category, patterns in INDIAN_MERCHANT_PATTERNS.items():
        for pattern in patterns:
            if pattern.lower() in description_lower:
                return category
    
    return None

def get_emission_factor(category: str) -> Dict[str, float]:
    """
    Get emission factor for a category
    
    Args:
        category: Category name
        
    Returns:
        Dict with min, max emission factors
    """
    return EMISSION_FACTORS.get(category, EMISSION_FACTORS["miscellaneous"])

def get_all_categories() -> List[str]:
    """Get list of all official categories"""
    return OFFICIAL_CATEGORIES.copy()

def is_valid_category(category: str) -> bool:
    """Check if a category is in the official list"""
    return category in OFFICIAL_CATEGORIES

def normalize_category(category: str) -> str:
    """
    Normalize category name to official category
    Returns 'miscellaneous' if not found
    """
    if category in OFFICIAL_CATEGORIES:
        return category
    
    # Try to map common variations
    category_lower = category.lower().replace(" ", "_").replace("-", "_")
    
    # Common mappings
    mappings = {
        "food": "food_and_groceries",
        "groceries": "food_and_groceries",
        "food_delivery": "food_and_groceries",
        "food_groceries": "food_and_groceries",
        "utilities": "housing_and_utilities",
        "housing": "housing_and_utilities",
        "housing_utilities": "housing_and_utilities",
        "housing_rent": "housing_and_utilities",
        "transport_fuel": "transport",
        "transport_ride_sharing": "transport",
        "transport_public": "transport",
        "fuel": "transport",
        "clothing": "clothing_and_footwear",
        "footwear": "clothing_and_footwear",
        "shopping_clothing": "clothing_and_footwear",
        "electronics": "household_goods_and_appliances",
        "appliances": "household_goods_and_appliances",
        "shopping_online": "household_goods_and_appliances",
        "shopping_electronics": "household_goods_and_appliances",
        "healthcare": "healthcare_and_personal_care",
        "medical": "healthcare_and_personal_care",
        "personal_care": "healthcare_and_personal_care",
        "education": "education_and_communication",
        "communication": "education_and_communication",
        "entertainment": "recreation_and_leisure",
        "travel": "recreation_and_leisure",
        "recreation": "recreation_and_leisure",
        "recreation_entertainment": "recreation_and_leisure",
        "recreation_travel": "recreation_and_leisure",
        "financial": "financial_services_and_insurance",
        "insurance": "financial_services_and_insurance",
        "financial_services": "financial_services_and_insurance",
    }
    
    if category_lower in mappings:
        return mappings[category_lower]
    
    return "miscellaneous"

def get_category_display_name(category: str) -> str:
    """
    Get human-readable display name for category
    
    Args:
        category: Category name
        
    Returns:
        Display name
    """
    display_names = {
        "food_and_groceries": "Food & Groceries",
        "housing_and_utilities": "Housing & Utilities",
        "transport": "Transport",
        "clothing_and_footwear": "Clothing & Footwear",
        "household_goods_and_appliances": "Household Goods & Appliances",
        "healthcare_and_personal_care": "Healthcare & Personal Care",
        "education_and_communication": "Education & Communication",
        "recreation_and_leisure": "Recreation & Leisure",
        "financial_services_and_insurance": "Financial Services & Insurance",
        "miscellaneous": "Miscellaneous"
    }
    
    return display_names.get(category, category.replace("_", " ").title())

def get_category_stats() -> Dict[str, int]:
    """Get statistics about merchant patterns"""
    return {
        category: len(patterns) 
        for category, patterns in INDIAN_MERCHANT_PATTERNS.items()
    }
