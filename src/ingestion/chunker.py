import re
import uuid
from typing import Any

import tiktoken
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from loguru import logger

from src.config import CHILD_CHUNK_SIZE, CHILD_CHUNK_OVERLAP, PARENT_CHUNK_SIZE, PARENT_CHUNK_OVERLAP
from src.ingestion.metadata_extractor import build_chunk_metadata

_HEADERS_TO_SPLIT_ON = [
    ("#", "h1"),
    ("##", "h2"),
    ("###", "h3"),
    ("####", "h4"),
]

# Matches a complete markdown table block (header row + separator + data rows)
_TABLE_BLOCK_RE = re.compile(
    r'(?:^\|.+\|\n)+',
    re.MULTILINE,
)


def _token_len(text: str, enc: tiktoken.Encoding) -> int:
    return len(enc.encode(text))


def _split_preserving_tables(text: str, splitter: RecursiveCharacterTextSplitter) -> list[dict]:
    """
    Split text into segments, keeping markdown tables as atomic units.
    Returns list of {"type": "table"|"text", "content": str}.
    """
    segments: list[dict] = []
    last_end = 0

    for m in _TABLE_BLOCK_RE.finditer(text):
        before = text[last_end : m.start()].strip()
        if before:
            for chunk in splitter.split_text(before):
                if chunk.strip():
                    segments.append({"type": "text", "content": chunk})
        segments.append({"type": "table", "content": m.group(0)})
        last_end = m.end()

    remaining = text[last_end:].strip()
    if remaining:
        for chunk in splitter.split_text(remaining):
            if chunk.strip():
                segments.append({"type": "text", "content": chunk})

    return segments


def _find_page_num(
    full_text: str,
    section_content: str,
    page_boundaries: list[dict],
) -> int:
    probe = section_content.strip()[:100]
    idx = full_text.find(probe)
    if idx < 0:
        return page_boundaries[0]["page_num"] if page_boundaries else 1
    for pb in page_boundaries:
        if pb["start"] <= idx < pb["end"]:
            return pb["page_num"]
    return page_boundaries[-1]["page_num"] if page_boundaries else 1


class HierarchicalChunker:
    def __init__(self) -> None:
        self._enc = tiktoken.get_encoding("cl100k_base")

        def _tok(t: str) -> int:
            return _token_len(t, self._enc)

        self._header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=_HEADERS_TO_SPLIT_ON,
            strip_headers=False,
        )
        self._child_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHILD_CHUNK_SIZE,
            chunk_overlap=CHILD_CHUNK_OVERLAP,
            length_function=_tok,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        self._parent_splitter = RecursiveCharacterTextSplitter(
            chunk_size=PARENT_CHUNK_SIZE,
            chunk_overlap=PARENT_CHUNK_OVERLAP,
            length_function=_tok,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def chunk_document(
        self,
        pages: list[dict[str, Any]],
        doc_meta: dict[str, Any],
    ) -> tuple[list[dict], list[dict]]:
        """
        Build parent and child chunks from pymupdf4llm page-level output.

        Returns:
            parents: list of section-level dicts (for context retrieval)
            children: list of clause-level dicts (for vector retrieval)
        """
        # Concatenate pages, recording character offsets for page lookup
        full_text = ""
        page_boundaries: list[dict] = []

        for i, page in enumerate(pages):
            text = page.get("text", "").strip()
            if not text:
                continue
            start = len(full_text)
            full_text += text + "\n\n"
            page_meta = page.get("metadata", {})
            page_num = page_meta.get("page", i) + 1  # pymupdf is 0-indexed
            page_boundaries.append({"start": start, "end": len(full_text), "page_num": page_num})

        if not full_text.strip():
            logger.warning(f"  No text extracted for document: {doc_meta.get('source_doc')}")
            return [], []

        header_docs = self._header_splitter.split_text(full_text)

        parents: list[dict] = []
        children: list[dict] = []

        for hdoc in header_docs:
            content: str = hdoc.page_content
            if not content.strip():
                continue

            header_meta: dict = hdoc.metadata  # {"h1": ..., "h2": ..., etc.}
            header_path = [v for v in header_meta.values() if v]
            page_num = _find_page_num(full_text, content, page_boundaries)
            parent_id = str(uuid.uuid4())

            # Parent chunks may themselves be too large — split them too
            parent_texts = self._parent_splitter.split_text(content)

            for parent_text in parent_texts:
                if not parent_text.strip():
                    continue

                current_parent_id = str(uuid.uuid4())
                parent_meta = build_chunk_metadata(
                    doc_meta, page_num, header_path, parent_text, "section"
                )
                parents.append({"id": current_parent_id, "text": parent_text, "metadata": parent_meta})

                # Split parent into child chunks, preserving tables
                segments = _split_preserving_tables(parent_text, self._child_splitter)

                for seg in segments:
                    chunk_type = "table" if seg["type"] == "table" else "clause"
                    child_meta = build_chunk_metadata(
                        doc_meta, page_num, header_path, seg["content"], chunk_type, current_parent_id
                    )
                    children.append({
                        "id": str(uuid.uuid4()),
                        "text": seg["content"],
                        "parent_text": parent_text,
                        "metadata": child_meta,
                    })

        logger.info(
            f"  Chunked → {len(parents)} parent sections, {len(children)} child chunks"
        )
        return parents, children
