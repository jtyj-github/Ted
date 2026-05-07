#!/usr/bin/env python3
"""Quick smoke-test for the retrieval pipeline. Not part of the production stack."""

import sys
from loguru import logger
from src.config import LOG_LEVEL
from src.retrieval.retriever import Retriever

QUERIES = [
    "What are the travel distance requirements for means of escape?",
    "fire extinguisher maintenance requirements",
    "sprinkler system requirements for high rise buildings",
    "SCDF FSR 2.1",
]


def main() -> None:
    logger.remove()
    logger.add(sys.stderr, level=LOG_LEVEL, colorize=True)

    retriever = Retriever()

    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else QUERIES[0]
    print(f"\nQuery: {query}\n{'─' * 60}")

    results = retriever.retrieve(query)
    for i, chunk in enumerate(results, 1):
        print(f"\n[{i}] {chunk.citation()}  (score={chunk.score:.3f})")
        print(f"    {chunk.parent_text[:300].strip()}…")


if __name__ == "__main__":
    main()
