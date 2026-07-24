"""Tests for nodes/rule_categorizer.py"""

from __future__ import annotations

from core.state import GraphState, RedactedTransaction
from nodes.rule_categorizer import rule_based_categorization_node


class TestRuleCategorizer:
    """Test rule-based transaction categorization."""

    def test_known_merchants_categorized(self):
        """Known merchants are categorized correctly by rules."""
        state = GraphState(
            redacted_transactions=[
                RedactedTransaction(
                    date="01/11/2024",
                    description="SWIGGY",
                    original_description="SWIGGY",
                    amount=450.0,
                    type="debit",
                    balance=74550.0,
                    raw_text="SWIGGY",
                    redaction_applied=False,
                    redacted_fields=[],
                ),
                RedactedTransaction(
                    date="03/11/2024",
                    description="UBER",
                    original_description="UBER",
                    amount=280.0,
                    type="debit",
                    balance=74270.0,
                    raw_text="UBER",
                    redaction_applied=False,
                    redacted_fields=[],
                ),
            ],
            pdf_path="",
            pdf_password="",
            raw_text="",
            transactions=[],
            filtered_transactions=[],
            llm_provider="",
            llm_model="",
            bank_type="",
            extraction_method="",
            rule_categorized=[],
            uncategorized=[],
            categorized_transactions=[],
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

        result = rule_based_categorization_node(state)

        # Both should be categorized by rules
        assert result["rule_based_count"] == 2
        assert len(result["uncategorized"]) == 0
        assert len(result["rule_categorized"]) == 2

    def test_unknown_merchants_uncategorized(self):
        """Unknown merchants left for LLM categorization."""
        state = GraphState(
            redacted_transactions=[
                RedactedTransaction(
                    date="01/11/2024",
                    description="OBSCURE-MERCHANT-XYZ",
                    original_description="OBSCURE-MERCHANT-XYZ",
                    amount=100.0,
                    type="debit",
                    balance=50000.0,
                    raw_text="OBSCURE",
                    redaction_applied=False,
                    redacted_fields=[],
                ),
            ],
            pdf_path="",
            pdf_password="",
            raw_text="",
            transactions=[],
            filtered_transactions=[],
            llm_provider="",
            llm_model="",
            bank_type="",
            extraction_method="",
            rule_categorized=[],
            uncategorized=[],
            categorized_transactions=[],
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

        result = rule_based_categorization_node(state)

        # Should be in uncategorized for LLM
        assert result["rule_based_count"] == 0
        assert len(result["uncategorized"]) == 1
        assert len(result["rule_categorized"]) == 0

    def test_mixed_categorization(self):
        """Mix of known and unknown merchants split correctly."""
        state = GraphState(
            redacted_transactions=[
                RedactedTransaction(
                    date="01/11/2024",
                    description="SWIGGY",
                    original_description="SWIGGY",
                    amount=450.0,
                    type="debit",
                    balance=74550.0,
                    raw_text="SWIGGY",
                    redaction_applied=False,
                    redacted_fields=[],
                ),
                RedactedTransaction(
                    date="02/11/2024",
                    description="MYSTERY-SHOP",
                    original_description="MYSTERY-SHOP",
                    amount=200.0,
                    type="debit",
                    balance=74350.0,
                    raw_text="MYSTERY",
                    redaction_applied=False,
                    redacted_fields=[],
                ),
            ],
            pdf_path="",
            pdf_password="",
            raw_text="",
            transactions=[],
            filtered_transactions=[],
            llm_provider="",
            llm_model="",
            bank_type="",
            extraction_method="",
            rule_categorized=[],
            uncategorized=[],
            categorized_transactions=[],
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

        result = rule_based_categorization_node(state)

        assert result["rule_based_count"] == 1
        assert len(result["uncategorized"]) == 1
