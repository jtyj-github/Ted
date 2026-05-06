#!/usr/bin/env python3
"""CLI entry point for the ingestion pipeline."""

import argparse
import sys
from pathlib import Path

from loguru import logger

from src.config import DOCS_DIR, LOG_LEVEL
from src.ingestion.pipeline import run_ingestion


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest Singapore building code PDFs into Qdrant"
    )
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=DOCS_DIR,
        help=f"Root directory containing PDF documents (default: {DOCS_DIR})",
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=None,
        help="Ingest a single PDF file (useful for testing)",
    )
    parser.add_argument(
        "--force-recreate",
        action="store_true",
        help="Drop and recreate the Qdrant collection before ingesting",
    )
    args = parser.parse_args()

    logger.remove()
    logger.add(sys.stderr, level=LOG_LEVEL, colorize=True)
    Path("logs").mkdir(exist_ok=True)
    logger.add("logs/ingestion.log", level="DEBUG", rotation="10 MB", retention=3)

    if args.file and not args.file.exists():
        logger.error(f"File not found: {args.file}")
        sys.exit(1)

    run_ingestion(
        docs_dir=args.docs_dir,
        single_file=args.file,
        force_recreate=args.force_recreate,
    )


if __name__ == "__main__":
    main()
