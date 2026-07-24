"""Tests for nodes/carbon_estimator.py"""

from __future__ import annotations

from core.state import GraphState, CategorizedTransaction
from nodes.carbon_estimator import estimate_carbon_node


class TestCarbonEstimator:
    """Test carbon estimation math and flat transaction handling."""

    def test_known_value_math(self):
        """MATH VERIFICATION: amount=1000, factor min=10/max=20 → min=10/max=20/avg=15."""
        state = GraphState(
            categorized_transactions=[
                CategorizedTransaction(
                    date="01/11/2024",
                    description="TEST",
                    amount=1000.0,
                    type="debit",
                    balance=50000.0,
                    original_description="TEST",
                    category="transport",
                    categorization_method="rule_based",
                )
            ],
            pdf_path="",
            pdf_password="",
            raw_text="",
            llm_provider="",
            llm_model="",
            bank_type="",
            extraction_method="",
            transactions=[],
            redacted_transactions=[],
            filtered_transactions=[],
            rule_categorized=[],
            uncategorized=[],
            carbon_estimates=[],
            total_carbon_kg_min=0.0,
            total_carbon_kg_max=0.0,
            total_carbon_kg_avg=0.0,
            category_breakdown={},
            monthly_breakdown={},
            rule_based_count=0,
            llm_based_count=0,
            pii_redacted_count=0,
            high_value_transactions=[],
            high_value_count=0,
            recommendations=[],
            insights=[],
            messages=[],
            errors=[],
            processing_status="",
        )

        result = estimate_carbon_node(state)

        # Transport factors: min=20, max=40 per ₹1000
        # amount=1000 → 1 unit of 1000, so:
        # min = 1 * 20 = 20, max = 1 * 40 = 40, avg = 30
        assert result["carbon_estimates"][0]["carbon_kg_min"] == 20.0
        assert result["carbon_estimates"][0]["carbon_kg_max"] == 40.0
        assert result["carbon_estimates"][0]["carbon_kg_avg"] == 30.0

        # Totals should match the single estimate
        assert result["total_carbon_kg_min"] == 20.0
        assert result["total_carbon_kg_max"] == 40.0
        assert result["total_carbon_kg_avg"] == 30.0

    def test_flat_structure_access(self):
        """REGRESSION: flat transaction structure (no nested access) works."""
        state = GraphState(
            categorized_transactions=[
                CategorizedTransaction(
                    date="01/11/2024",
                    description="SWIGGY",
                    amount=500.0,
                    type="debit",
                    balance=50000.0,
                    original_description="SWIGGY",
                    category="food_and_groceries",
                    categorization_method="rule_based",
                )
            ],
            pdf_path="",
            pdf_password="",
            raw_text="",
            llm_provider="",
            llm_model="",
            bank_type="",
            extraction_method="",
            transactions=[],
            redacted_transactions=[],
            filtered_transactions=[],
            rule_categorized=[],
            uncategorized=[],
            carbon_estimates=[],
            total_carbon_kg_min=0.0,
            total_carbon_kg_max=0.0,
            total_carbon_kg_avg=0.0,
            category_breakdown={},
            monthly_breakdown={},
            rule_based_count=0,
            llm_based_count=0,
            pii_redacted_count=0,
            high_value_transactions=[],
            high_value_count=0,
            recommendations=[],
            insights=[],
            messages=[],
            errors=[],
            processing_status="",
        )

        # Should not raise any errors about nested 'transaction' access
        result = estimate_carbon_node(state)

        assert len(result["carbon_estimates"]) == 1
        assert result["carbon_estimates"][0]["carbon_kg_min"] > 0  # Food factors: min=7
        assert result["carbon_estimates"][0]["carbon_kg_max"] > result["carbon_estimates"][0]["carbon_kg_min"]
