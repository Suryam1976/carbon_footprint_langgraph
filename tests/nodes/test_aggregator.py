"""Tests for nodes/aggregator.py"""

from __future__ import annotations

from core.state import GraphState, CarbonEstimate
from nodes.aggregator import aggregate_results_node


class TestAggregator:
    """Test results aggregation by category."""

    def test_category_totals_calculation(self):
        """Carbon totals are summed correctly per category."""
        state = GraphState(
            carbon_estimates=[
                CarbonEstimate(
                    date="01/11/2024",
                    description="SWIGGY-1",
                    original_description="SWIGGY-1",
                    amount=500.0,
                    type="debit",
                    balance=50000.0,
                    raw_text="SWIGGY-1",
                    redaction_applied=False,
                    redacted_fields=[],
                    category="food_and_groceries",
                    categorization_method="rule_based",
                    carbon_kg_min=3.5,
                    carbon_kg_max=7.5,
                    carbon_kg_avg=5.5,
                    emission_factor_min=7,
                    emission_factor_max=15,
                    emission_factor_notes="",
                ),
                CarbonEstimate(
                    date="02/11/2024",
                    description="SWIGGY-2",
                    original_description="SWIGGY-2",
                    amount=300.0,
                    type="debit",
                    balance=50000.0,
                    raw_text="SWIGGY-2",
                    redaction_applied=False,
                    redacted_fields=[],
                    category="food_and_groceries",
                    categorization_method="rule_based",
                    carbon_kg_min=2.1,
                    carbon_kg_max=4.5,
                    carbon_kg_avg=3.3,
                    emission_factor_min=7,
                    emission_factor_max=15,
                    emission_factor_notes="",
                ),
                CarbonEstimate(
                    date="03/11/2024",
                    description="UBER",
                    original_description="UBER",
                    amount=280.0,
                    type="debit",
                    balance=50000.0,
                    raw_text="UBER",
                    redaction_applied=False,
                    redacted_fields=[],
                    category="transport",
                    categorization_method="rule_based",
                    carbon_kg_min=5.6,
                    carbon_kg_max=11.2,
                    carbon_kg_avg=8.4,
                    emission_factor_min=20,
                    emission_factor_max=40,
                    emission_factor_notes="",
                ),
            ],
            pdf_path="",
            pdf_password="",
            raw_text="",
            transactions=[],
            redacted_transactions=[],
            filtered_transactions=[],
            rule_categorized=[],
            uncategorized=[],
            categorized_transactions=[],
            total_carbon_kg_min=0.0,
            total_carbon_kg_max=0.0,
            total_carbon_kg_avg=0.0,
            category_breakdown={},
            monthly_breakdown={},
            llm_provider="",
            llm_model="",
            bank_type="",
            extraction_method="",
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

        result = aggregate_results_node(state)

        # Check category breakdown
        assert "food_and_groceries" in result["category_breakdown"]
        assert "transport" in result["category_breakdown"]

        # Food totals: 3.5 + 2.1 = 5.6 (min), 7.5 + 4.5 = 12.0 (max), 5.5 + 3.3 = 8.8 (avg)
        food_data = result["category_breakdown"]["food_and_groceries"]
        assert food_data["total_co2_kg_min"] == 5.6
        assert food_data["total_co2_kg_max"] == 12.0
        assert food_data["total_co2_kg_avg"] == 8.8

        # Transport: 5.6 (min), 11.2 (max), 8.4 (avg)
        transport_data = result["category_breakdown"]["transport"]
        assert transport_data["total_co2_kg_min"] == 5.6
        assert transport_data["total_co2_kg_max"] == 11.2
        assert transport_data["total_co2_kg_avg"] == 8.4

    def test_sorting_by_emissions(self):
        """Categories sorted by avg emissions (highest first)."""
        state = GraphState(
            carbon_estimates=[
                CarbonEstimate(
                    date="01/11/2024",
                    description="SMALL",
                    original_description="SMALL",
                    amount=50.0,
                    type="debit",
                    balance=50000.0,
                    raw_text="SMALL",
                    redaction_applied=False,
                    redacted_fields=[],
                    category="clothing_and_footwear",  # Low emission
                    categorization_method="rule_based",
                    carbon_kg_min=0.25,
                    carbon_kg_max=0.5,
                    carbon_kg_avg=0.375,
                    emission_factor_min=5,
                    emission_factor_max=10,
                    emission_factor_notes="",
                ),
                CarbonEstimate(
                    date="02/11/2024",
                    description="LARGE",
                    original_description="LARGE",
                    amount=1000.0,
                    type="debit",
                    balance=50000.0,
                    raw_text="LARGE",
                    redaction_applied=False,
                    redacted_fields=[],
                    category="transport",  # High emission
                    categorization_method="rule_based",
                    carbon_kg_min=20.0,
                    carbon_kg_max=40.0,
                    carbon_kg_avg=30.0,
                    emission_factor_min=20,
                    emission_factor_max=40,
                    emission_factor_notes="",
                ),
            ],
            pdf_path="",
            pdf_password="",
            raw_text="",
            transactions=[],
            redacted_transactions=[],
            filtered_transactions=[],
            rule_categorized=[],
            uncategorized=[],
            categorized_transactions=[],
            total_carbon_kg_min=0.0,
            total_carbon_kg_max=0.0,
            total_carbon_kg_avg=0.0,
            category_breakdown={},
            monthly_breakdown={},
            llm_provider="",
            llm_model="",
            bank_type="",
            extraction_method="",
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

        result = aggregate_results_node(state)

        # sorted_categories should be sorted descending by avg
        sorted_cats = result["sorted_categories"]
        assert len(sorted_cats) == 2
        # Transport (30.0) should come before clothing (0.375)
        assert sorted_cats[0][0] == "transport"
        assert sorted_cats[1][0] == "clothing_and_footwear"
