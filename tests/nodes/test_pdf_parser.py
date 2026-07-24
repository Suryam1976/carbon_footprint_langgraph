"""Tests for nodes/pdf_parser.py"""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from core.state import GraphState
from nodes.pdf_parser import parse_pdf_node


class TestPDFParser:
    """Test PDF parsing and fallback to sample data."""

    def test_no_pdf_uses_sample_data(self):
        """No PDF provided → uses sample data."""
        state = GraphState(
            pdf_path="",
            pdf_password="",
            raw_text="",
            transactions=[],
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

        result = parse_pdf_node(state)

        assert result["processing_status"] == "using_sample_data"
        assert len(result["raw_text"]) > 0
        assert len(result["transactions"]) > 0

    @patch("nodes.pdf_parser.fitz")
    def test_successful_pdf_parse(self, mock_fitz):
        """Successful PDF parsing extracts text."""
        # Mock fitz.open
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "01/11/2024 UPI-SWIGGY 450\n"
        mock_doc.__iter__ = MagicMock(return_value=iter([mock_page]))
        mock_doc.is_encrypted = False
        mock_fitz.open.return_value = mock_doc

        state = GraphState(
            pdf_path="test.pdf",
            pdf_password="",
            raw_text="",
            transactions=[],
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

        result = parse_pdf_node(state)

        assert result["processing_status"] == "pdf_parsed"
        assert "SWIGGY" in result["raw_text"]

    @patch("nodes.pdf_parser.fitz")
    def test_empty_pdf_fallback(self, mock_fitz):
        """Empty PDF (no text) falls back to sample data."""
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = ""  # Empty
        mock_doc.__iter__ = MagicMock(return_value=iter([mock_page]))
        mock_doc.is_encrypted = False
        mock_fitz.open.return_value = mock_doc

        state = GraphState(
            pdf_path="empty.pdf",
            pdf_password="",
            raw_text="",
            transactions=[],
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

        result = parse_pdf_node(state)

        # Falls back to sample data
        assert result["processing_status"] == "using_sample_data"
        assert len(result["transactions"]) > 0
