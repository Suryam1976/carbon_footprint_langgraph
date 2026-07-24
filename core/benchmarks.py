"""
Carbon footprint benchmark constants for comparison context.

METHODOLOGY CAVEAT — read before using these constants:
This app estimates a SPEND-BASED carbon footprint derived only from digital
bank-card/UPI debit transactions in an uploaded statement. It does NOT capture
cash spending, owned-vehicle fuel not paid by card, home energy not billed
digitally, employer-subsidized consumption, etc. Any comparison below is
DIRECTIONAL/APPROXIMATE, not a precise measurement of a user's full personal
carbon footprint — treat it as "same ballpark," not literal equivalence.

SOURCE & METHODOLOGY:
- "The scale and drivers of carbon footprints in households, cities and
  regions across India" (ScienceDirect, 2020) — urban India per-capita ~2,330
  kg CO2e/year based on consumption expenditure analysis.
- Cross-checked against ISEC Policy Brief 53 "Household Carbon Footprint of
  India" — national per-capita ranges 1,472–2,900 kg CO2e/year depending on
  income; urban middle-class households with car/AC/flights ~4,000–6,000 kg
  CO2e/year.

We anchor on ONE annual figure and derive monthly/weekly from it so every
in-app comparison stays internally consistent.
"""

ANNUAL_PER_CAPITA_CO2E_KG = 2330
MONTHLY_PER_CAPITA_CO2E_KG = round(ANNUAL_PER_CAPITA_CO2E_KG / 12, 1)   # ≈194.2
WEEKLY_PER_CAPITA_CO2E_KG = round(ANNUAL_PER_CAPITA_CO2E_KG / 52, 1)    # ≈44.8

# Directional monthly "typical range" band, centered near the anchor above,
# used by insights_generator.py's rule-based thresholds.
MONTHLY_TYPICAL_RANGE_LOW_KG = 150
MONTHLY_TYPICAL_RANGE_HIGH_KG = 250
MONTHLY_HIGH_FOOTPRINT_KG = 300          # "significantly above average" cutoff

# Tree-offset conversion (kg CO2 absorbed per tree per year, commonly cited estimate)
KG_CO2_PER_TREE_PER_YEAR = 21
