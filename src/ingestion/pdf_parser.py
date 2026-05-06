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
        pages: list[dict] = pymupdf4llm.to_markdown(
            str(pdf_path),
            page_chunks=True,
            write_images=False,
        )
        non_empty = sum(1 for p in pages if p.get("text", "").strip())
        logger.info(f"  {len(pages)} pages, {non_empty} non-empty")

        if non_empty == 0:
            logger.warning(f"  No extractable text — may be a scanned image PDF: {pdf_path.name}")

        return pages
    except Exception as exc:
        logger.error(f"Failed to parse {pdf_path.name}: {exc}")
        raise
