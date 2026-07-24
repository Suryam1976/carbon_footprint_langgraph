"""Tests for nodes/pii_redactor.py"""

from __future__ import annotations

from core.state import GraphState, Transaction
from nodes.pii_redactor import redact_pii_node


class TestPIIRedactor:
    """Test PII redaction and credit filtering."""

    def test_mobile_redaction(self):
        """Mobile numbers are redacted."""
        state = GraphState(
            transactions=[
                Transaction(
                    date="01/11/2024",
                    description="UPI-9876543210-MERCHANT",
                    amount=450.00,
                    type="debit",
                    balance=74550.00,
                    raw_text="UPI-9876543210-MERCHANT"
                )
            ],
            pdf_path="",
            pdf_password="",
            raw_text="",
            llm_provider="",
            llm_model="",
            bank_type="",
            extraction_method="",
            redacted_transactions=[],
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

        result = redact_pii_node(state)

        assert result["pii_redacted_count"] == 1
        assert "[MOBILE_REDACTED]" in result["redacted_transactions"][0]["description"]

    def test_amount_not_redacted_as_account(self):
        """REGRESSION: account number guard prevents redacting amounts as account numbers.
        E.g., ₹12345678 should NOT be redacted if amount=12345678."""
        state = GraphState(
            transactions=[
                Transaction(
                    date="01/11/2024",
                    description="Transaction 12345678",  # 8+ digits
                    amount=12345678.00,  # Same number as in description
                    type="debit",
                    balance=50000.00,
                    raw_text="Transaction 12345678"
                )
            ],
            pdf_path="",
            pdf_password="",
            raw_text="",
            llm_provider="",
            llm_model="",
            bank_type="",
            extraction_method="",
            redacted_transactions=[],
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

        result = redact_pii_node(state)

        # The amount itself should NOT be redacted
        assert "[ACCOUNT_REDACTED]" not in result["redacted_transactions"][0]["description"]
        assert "12345678" in result["redacted_transactions"][0]["description"]

    def test_credit_filtering(self):
        """Only DEBIT transactions processed, CREDIT transactions filtered."""
        state = GraphState(
            transactions=[
                Transaction(
                    date="01/11/2024",
                    description="UPI-SWIGGY",
                    amount=450.00,
                    type="debit",
                    balance=74550.00,
                    raw_text="UPI-SWIGGY"
                ),
                Transaction(
                    date="02/11/2024",
                    description="SALARY-CREDIT",
                    amount=50000.00,
                    type="credit",  # This should be filtered
                    balance=124550.00,
                    raw_text="SALARY-CREDIT"
                ),
            ],
            pdf_path="",
            pdf_password="",
            raw_text="",
            llm_provider="",
            llm_model="",
            bank_type="",
            extraction_method="",
            redacted_transactions=[],
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

        result = redact_pii_node(state)

        assert result["debits_processed_count"] == 1
        assert result["credits_filtered_count"] == 1
        assert len(result["redacted_transactions"]) == 1
        assert result["redacted_transactions"][0]["description"] == "UPI-SWIGGY"
