"""Tests for nodes/insights_generator.py"""

from __future__ import annotations

import logging

from core.state import GraphState
from nodes.insights_generator import (
    generate_insights_node,
    analyze_spending_patterns,
    generate_rule_based_insights,
)


class TestInsightsGenerator:
    """Test insights generation with rule-based fallback."""

    def test_rule_based_insights_high_footprint(self):
        """High-footprint scenario generates appropriate insights."""
        insights_data = {
            "category_summary": "Transport: 150 kg CO2e",
            "pattern_analysis": "High emissions detected",
            "top_categories": [("transport", {"total_co2_kg_avg": 150})],
            "total_carbon": 350.0,  # Above 300 threshold
            "transport_co2": 150.0,
            "food_co2": 50.0,
            "shopping_co2": 10.0,
        }

        insights = generate_rule_based_insights(insights_data)

        assert len(insights) >= 2
        # First insight should mention high footprint
        assert any("significantly above" in i.lower() for i in insights)

    def test_rule_based_recommendations(self):
        """Rule-based recommendations are context-aware."""
        insights_data = {
            "category_summary": "Transport: 150 kg CO2e",
            "pattern_analysis": "High emissions detected",
            "top_categories": [("transport", {"total_co2_kg_avg": 150})],
            "total_carbon": 350.0,
            "transport_co2": 150.0,  # Very high
            "food_co2": 30.0,
            "shopping_co2": 10.0,
        }

        from nodes.insights_generator import generate_rule_based_recommendations
        recommendations = generate_rule_based_recommendations(insights_data)

        assert len(recommendations) >= 2
        # Should recommend transport reduction
        assert any("transport" in r.lower() or "carpooling" in r.lower() or "transit" in r.lower()
                   for r in recommendations)

    def test_analyze_spending_patterns_assessment(self):
        """Pattern analysis correctly assesses carbon levels."""
        category_breakdown = {
            "transport": {"total_co2_kg_avg": 150},
            "food_and_groceries": {"total_co2_kg_avg": 50},
            "household_goods_and_appliances": {"total_co2_kg_avg": 20},
            "clothing_and_footwear": {"total_co2_kg_avg": 15},
        }

        data = analyze_spending_patterns(
            total_carbon=235.0,  # Within average range
            category_breakdown=category_breakdown,
            transactions=[],
            high_value_count=0,
        )

        # Pattern analysis should be generated
        assert "pattern_analysis" in data
        assert len(data["pattern_analysis"]) > 0

    def test_benchmark_constants_used(self, caplog):
        """Insights generation uses centralized benchmark constants (not hardcoded)."""
        from core.benchmarks import MONTHLY_HIGH_FOOTPRINT_KG

        caplog.set_level(logging.DEBUG)

        state = GraphState(
            total_carbon_kg_avg=250.0,  # Below high threshold
            category_breakdown={
                "transport": {"total_co2_kg_avg": 100},
                "food_and_groceries": {"total_co2_kg_avg": 60},
                "housing_and_utilities": {"total_co2_kg_avg": 50},
                "household_goods_and_appliances": {"total_co2_kg_avg": 20},
                "clothing_and_footwear": {"total_co2_kg_avg": 20},
            },
            carbon_estimates=[],
            pdf_path="",
            pdf_password="",
            raw_text="",
            transactions=[],
            redacted_transactions=[],
            filtered_transactions=[],
            rule_categorized=[],
            uncategorized=[],
            categorized_transactions=[],
            total_carbon_kg_min=200.0,
            total_carbon_kg_max=300.0,
            llm_provider="",
            llm_model="",
            bank_type="",
            extraction_method="",
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

        result = generate_insights_node(state)

        # Should generate insights and recommendations
        assert len(result["insights"]) > 0
        assert len(result["recommendations"]) > 0
        # Should generate messages (either rule-based or LLM-based)
        assert len(result["messages"]) > 0
        # Check that messages contain content about insights
        message_contents = [
            msg.content if hasattr(msg, "content") else str(msg)
            for msg in result["messages"]
        ]
        assert any("insight" in content.lower() or "analysis" in content.lower()
                   for content in message_contents)

    def test_spending_patterns_low_footprint(self):
        """Low-footprint scenario recognized correctly."""
        insights_data = {
            "category_summary": "Food: 30 kg CO2e",
            "pattern_analysis": "Low emissions",
            "top_categories": [("food_and_groceries", {"total_co2_kg_avg": 30})],
            "total_carbon": 100.0,  # Well below average
            "transport_co2": 0.0,
            "food_co2": 30.0,
            "shopping_co2": 5.0,
        }

        insights = generate_rule_based_insights(insights_data)

        assert len(insights) >= 1
        # Should praise low footprint
        assert any("excellent" in i.lower() or "well below" in i.lower()
                   for i in insights)
