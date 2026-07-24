"""Centralized logging setup.

Call configure_logging() once at each process entry point:
- streamlit_app.py (module load)
- orchestrator.py (__main__ block)
- tests/conftest.py (pytest initialization)

Modules elsewhere just do:
    import logging
    logger = logging.getLogger(__name__)
    logger.debug("message"), logger.info(...), etc.
"""

from __future__ import annotations

import logging
import os


def configure_logging(level: str | None = None) -> None:
    """Configure stdlib logging for the application.

    Args:
        level: Log level as string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               Defaults to env var LOG_LEVEL, or INFO if unset.
    """
    resolved = (level or os.getenv("LOG_LEVEL", "INFO")).upper()

    logging.basicConfig(
        level=resolved,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Suppress verbose logging from third-party HTTP libraries
    for noisy_lib in ("httpx", "httpcore", "urllib3"):
        logging.getLogger(noisy_lib).setLevel(logging.WARNING)
