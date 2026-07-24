"""Tests for utils/sample_data.py"""

from __future__ import annotations

from utils.sample_data import get_sample_categorized_transactions, get_sample_carbon_estimates
from utils.patterns import OFFICIAL_CATEGORIES


class TestSampleData:
    """Test sample data for consistency with production code."""

    def test_sample_categorized_uses_official_categories(self):
        """REGRESSION FIX: Sample data uses OFFICIAL_CATEGORIES, not legacy names."""
        categorized = get_sample_categorized_transactions()

        # All categories should be official
        for txn in categorized:
            category = txn["category"]
            assert category in OFFICIAL_CATEGORIES, \
                f"Found legacy category '{category}', should be one of {OFFICIAL_CATEGORIES}"

    def test_sample_estimates_uses_real_factors(self):
        """REGRESSION FIX: Sample estimates use real emission factors from patterns.py."""
        from utils.patterns import get_emission_factor

        estimates = get_sample_carbon_estimates()

        # Verify each estimate's factors match the real emission factors
        for est in estimates:
            category = est["category"]
            real_factors = get_emission_factor(category)

            assert est["emission_factor_min"] == real_factors["min"], \
                f"Category {category}: sample min {est['emission_factor_min']} != real {real_factors['min']}"
            assert est["emission_factor_max"] == real_factors["max"], \
                f"Category {category}: sample max {est['emission_factor_max']} != real {real_factors['max']}"

    def test_sample_data_math_consistency(self):
        """Sample data carbon math matches formula: (amount/1000) * factor."""
        estimates = get_sample_carbon_estimates()

        for est in estimates:
            amount = est["amount"]
            amount_thousands = amount / 1000
            expected_min = round(amount_thousands * est["emission_factor_min"], 2)
            expected_max = round(amount_thousands * est["emission_factor_max"], 2)

            assert est["carbon_kg_min"] == expected_min, \
                f"Min carbon mismatch for {est['description']}: {est['carbon_kg_min']} != {expected_min}"
            assert est["carbon_kg_max"] == expected_max, \
                f"Max carbon mismatch for {est['description']}: {est['carbon_kg_max']} != {expected_max}"
