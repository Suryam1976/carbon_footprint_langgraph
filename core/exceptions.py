"""Custom exceptions for the carbon footprint pipeline."""


class CarbonAnalysisError(Exception):
    """Base exception for the carbon footprint analysis pipeline."""

    pass


class TransactionExtractionError(CarbonAnalysisError):
    """Raised when a real uploaded PDF's transactions cannot be extracted or parsed.

    Deliberately NOT caught by falling back to sample data — silently substituting
    sample data for a real user's failed upload is misleading and masks the problem.
    Instead, the caller should surface this error to the user via st.error() or
    equivalent, giving them the option to try a different PDF or use sample data
    deliberately (via checkbox).
    """

    pass
