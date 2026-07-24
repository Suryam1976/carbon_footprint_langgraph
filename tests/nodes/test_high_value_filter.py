"""Tests for nodes/high_value_filter.py"""

from __future__ import annotations

from core.state import GraphState, RedactedTransaction
from nodes.high_value_filter import filter_high_value_node, HIGH_VALUE_THRESHOLD


class TestHighValueFilter:
    """Test high-value transaction filtering."""

    def test_exactly_threshold_excluded(self):
        """BOUNDARY: amount == HIGH_VALUE_THRESHOLD (₹50,000) is excluded (>=)."""
        state = GraphState(
            redacted_transactions=[
                RedactedTransaction(
                    date="01/11/2024",
                    description="Transaction",
                    original_description="Transaction",
                    amount=float(HIGH_VALUE_THRESHOLD),  # Exactly 50000
                    type="debit",
                    balance=50000.0,
                    raw_text="Test",
                    redaction_applied=False,
                    redacted_fields=[],
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
            filtered_transactions=[],
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

        result = filter_high_value_node(state)

        # Should be in high_value, NOT in filtered
        assert len(result["filtered_transactions"]) == 0
        assert len(result["high_value_transactions"]) == 1
        assert result["high_value_count"] == 1

    def test_below_threshold_included(self):
        """amount < HIGH_VALUE_THRESHOLD is included in regular transactions."""
        state = GraphState(
            redacted_transactions=[
                RedactedTransaction(
                    date="01/11/2024",
                    description="SWIGGY",
                    original_description="SWIGGY",
                    amount=49999.99,  # Just below 50000
                    type="debit",
                    balance=50000.0,
                    raw_text="Test",
                    redaction_applied=False,
                    redacted_fields=[],
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
            filtered_transactions=[],
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

        result = filter_high_value_node(state)

        # Should be in regular filtered transactions
        assert len(result["filtered_transactions"]) == 1
        assert len(result["high_value_transactions"]) == 0

    def test_mixed_transactions(self):
        """Mix of regular and high-value transactions split correctly."""
        state = GraphState(
            redacted_transactions=[
                RedactedTransaction(
                    date="01/11/2024",
                    description="SWIGGY",
                    original_description="SWIGGY",
                    amount=450.0,
                    type="debit",
                    balance=50000.0,
                    raw_text="Test",
                    redaction_applied=False,
                    redacted_fields=[],
                ),
                RedactedTransaction(
                    date="02/11/2024",
                    description="FLIGHT",
                    original_description="FLIGHT",
                    amount=75000.0,  # High-value
                    type="debit",
                    balance=50000.0,
                    raw_text="Test",
                    redaction_applied=False,
                    redacted_fields=[],
                ),
            ],
            pdf_path="",
            pdf_password="",
            raw_text="",
            llm_provider="",
            llm_model="",
            bank_type="",
            extraction_method="",
            transactions=[],
            filtered_transactions=[],
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

        result = filter_high_value_node(state)

        assert len(result["filtered_transactions"]) == 1
        assert len(result["high_value_transactions"]) == 1
        assert result["high_value_count"] == 1
