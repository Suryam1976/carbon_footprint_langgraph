"""Tests for utils/patterns.py"""

from __future__ import annotations

import pytest

from utils.patterns import (
    categorize_transaction,
    get_emission_factor,
    normalize_category,
    OFFICIAL_CATEGORIES,
    EMISSION_FACTORS,
)


class TestCategorizeTransaction:
    """Test rule-based transaction categorization."""

    @pytest.mark.parametrize("merchant,expected_category", [
        ("SWIGGY", "food_and_groceries"),
        ("ZOMATO", "food_and_groceries"),
        ("UBER", "transport"),
        ("OLA", "transport"),
        ("ELECTRICITY", "housing_and_utilities"),
        ("AMAZON", "household_goods_and_appliances"),
        ("MYNTRA", "clothing_and_footwear"),
        ("PVR CINEMAS", "recreation_and_leisure"),
    ])
    def test_known_merchants(self, merchant, expected_category):
        """Known merchants are categorized correctly."""
        assert categorize_transaction(merchant) == expected_category

    def test_case_insensitive(self):
        """Categorization is case-insensitive."""
        assert categorize_transaction("swiggy") == "food_and_groceries"
        assert categorize_transaction("SWIGGY") == "food_and_groceries"
        assert categorize_transaction("Swiggy") == "food_and_groceries"

    def test_unknown_merchant_returns_none(self):
        """Unknown merchant returns None (needs LLM categorization)."""
        assert categorize_transaction("OBSCURE-MERCHANT-XYZ") is None


class TestGetEmissionFactor:
    """Test emission factor retrieval."""

    def test_known_category(self):
        """Known categories return valid emission factors."""
        factor = get_emission_factor("transport")
        assert factor["min"] == 20
        assert factor["max"] == 40

    def test_unknown_category_returns_miscellaneous(self, caplog):
        """Unknown category falls back to miscellaneous with warning log."""
        import logging
        caplog.set_level(logging.WARNING)

        factor = get_emission_factor("nonexistent_category")

        assert factor == EMISSION_FACTORS["miscellaneous"]
        assert "Unknown category" in caplog.text

    def test_all_official_categories_have_factors(self):
        """All official categories have emission factors defined."""
        for category in OFFICIAL_CATEGORIES:
            factor = get_emission_factor(category)
            assert "min" in factor
            assert "max" in factor
            assert factor["min"] >= 0
            assert factor["max"] >= factor["min"]


class TestNormalizeCategory:
    """Test category normalization (legacy → official)."""

    @pytest.mark.parametrize("legacy_name,expected_official", [
        ("food_delivery", "food_and_groceries"),
        ("food_groceries", "food_and_groceries"),
        ("transport_ride_sharing", "transport"),
        ("transport_fuel", "transport"),
        ("housing_utilities", "housing_and_utilities"),
        ("shopping_online", "household_goods_and_appliances"),
        ("recreation_entertainment", "recreation_and_leisure"),
    ])
    def test_legacy_names_normalize(self, legacy_name, expected_official):
        """Legacy category names normalize to official categories."""
        assert normalize_category(legacy_name) == expected_official

    def test_already_official_unchanged(self):
        """Already-official category names pass through unchanged."""
        assert normalize_category("transport") == "transport"
        assert normalize_category("food_and_groceries") == "food_and_groceries"

    def test_unknown_defaults_to_miscellaneous(self):
        """Unknown category names default to miscellaneous."""
        assert normalize_category("completely_unknown_xyz") == "miscellaneous"

    def test_set_consistency(self):
        """CONSISTENCY CHECK: official categories == emission factors keys."""
        assert set(OFFICIAL_CATEGORIES) == set(EMISSION_FACTORS.keys())
