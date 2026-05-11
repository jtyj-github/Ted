from pathlib import Path
from typing import Any

import fitz  # PyMuPDF — fallback parser
import pymupdf4llm
from loguru import logger


def parse_pdf(pdf_path: Path) -> list[dict[str, Any]]:
    """
    Parse a PDF to a list of per-page dicts.

    Tries pymupdf4llm first (better table and layout handling). If OCR path unavailable — fall back
    to direct PyMuPDF extraction, skip image-only pages silently.

    Returns:
        List of dicts with keys:
            - text: str  (markdown for that page)
            - metadata: dict  (page index, file_path)
    """
    logger.info(f"Parsing: {pdf_path.name}")
    try:
        raw = pymupdf4llm.to_markdown(
            str(pdf_path),
            page_chunks=True,
            write_images=False,
        )

        if raw is None or isinstance(raw, str):
            logger.warning(
                f"  pymupdf4llm returned unexpected type ({type(raw).__name__}) "
                f"— falling back to fitz: {pdf_path.name}"
            )
            return _parse_with_fitz(pdf_path)

        pages: list[dict] = raw
        non_empty = sum(1 for p in pages if (p.get("text") or "").strip())
        logger.info(f"  {len(pages)} pages, {non_empty} non-empty")

        if non_empty == 0:
            logger.warning(f"  No extractable text — may be a scanned image PDF: {pdf_path.name}")

        return pages

    except Exception as exc:
        logger.warning(
            f"  pymupdf4llm failed ({exc}) — falling back to fitz: {pdf_path.name}"
        )
        return _parse_with_fitz(pdf_path)


def _parse_with_fitz(pdf_path: Path) -> list[dict[str, Any]]:
    """
    Extract text page-by-page using PyMuPDF directly.

    image-only pages are silently skipped by the chunker. 
    Uses get_text("markdown") which preserves basic table structure natively.
    """
    pages: list[dict] = []
    try:
        doc = fitz.open(str(pdf_path))
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            try:
                text = page.get_text("markdown")
            except Exception:
                text = page.get_text("text")

            pages.append({
                "text": text or "",
                "metadata": {
                    "page": page_idx,   # 0-indexed, matching pymupdf4llm convention
                    "file_path": str(pdf_path),
                },
            })
        doc.close()

        non_empty = sum(1 for p in pages if p["text"].strip())
        logger.info(f"  fitz fallback: {len(pages)} pages, {non_empty} non-empty")

        if non_empty == 0:
            logger.warning(
                f"  No extractable text — may be a scanned image PDF: {pdf_path.name}"
            )

        return pages

    except Exception as exc:
        logger.exception(f"  fitz fallback also failed for {pdf_path.name}: {exc}")
        raise
