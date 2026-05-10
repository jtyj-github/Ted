from pathlib import Path
from typing import Any

import pymupdf4llm
from loguru import logger


def parse_pdf(pdf_path: Path) -> list[dict[str, Any]]:
    """
    Parse a PDF to a list of per-page dicts using pymupdf4llm.

    Returns:
        List of dicts, each with keys:
            - text: str  (markdown for that page)
            - metadata: dict  (page, file_path, etc.)
    """
    logger.info(f"Parsing: {pdf_path.name}")
    try:
        raw = pymupdf4llm.to_markdown(
            str(pdf_path),
            page_chunks=True,
            write_images=False,
        )

        # to_markdown() returns None for encrypted or unreadable PDFs instead of raising
        if raw is None:
            logger.warning(f"  to_markdown() returned None — skipping: {pdf_path.name}")
            return []

        # Older builds return a plain string when page_chunks is silently ignored
        if isinstance(raw, str):
            logger.warning(f"  to_markdown() returned a string, not page chunks — skipping: {pdf_path.name}")
            return []

        pages: list[dict] = raw
        non_empty = sum(1 for p in pages if (p.get("text") or "").strip())
        logger.info(f"  {len(pages)} pages, {non_empty} non-empty")

        if non_empty == 0:
            logger.warning(f"  No extractable text — may be a scanned image PDF: {pdf_path.name}")

        return pages
    except Exception as exc:
        logger.exception(f"Failed to parse {pdf_path.name}: {exc}")
        raise
