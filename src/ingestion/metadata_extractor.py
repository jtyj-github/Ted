import re
from typing import Any

# Clause / section IDs like "3.2.1", "C3.2", "FSR 6.4.2"
_CLAUSE_RE = re.compile(r'\b([A-Z]{0,4}\d+(?:\.\d+){1,4})\b')

# Cross-reference patterns for Singapore regulatory documents
_CROSS_REF_PATTERNS = [
    re.compile(r'\bSS\s+\d+(?:[:\-]\d+)?(?::\d{4})?\b', re.IGNORECASE),
    re.compile(r'\bCP\s+\d+(?:\s+Part\s+\d+)?\b', re.IGNORECASE),
    re.compile(r'\bClause\s+[A-Z]?\d+(?:\.\d+)+\b', re.IGNORECASE),
    re.compile(r'\bSection\s+[A-Z]?\d+(?:\.\d+)*\b', re.IGNORECASE),
    re.compile(r'\bTable\s+[A-Z]?\d+(?:\.\d+)*\b', re.IGNORECASE),
    re.compile(r'\bFigure\s+[A-Z]?\d+(?:\.\d+)*\b', re.IGNORECASE),
    re.compile(r'\bAppendix\s+[A-Z]\b', re.IGNORECASE),
    re.compile(r'\bBCA\s+Approved\s+Document[s]?\b', re.IGNORECASE),
    re.compile(r'\bSCDF\s+Fire\s+Code\b', re.IGNORECASE),
    re.compile(r'\bURA\s+[A-Za-z\s]+Guidelines\b', re.IGNORECASE),
    re.compile(r'\bFSR\s+[\d.]+\b', re.IGNORECASE),
]

_TABLE_RE = re.compile(r'^\|.+\|', re.MULTILINE)


def extract_cross_refs(text: str) -> list[str]:
    refs: list[str] = []
    for pattern in _CROSS_REF_PATTERNS:
        refs.extend(m.strip() for m in pattern.findall(text))
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for r in refs:
        if r not in seen:
            seen.add(r)
            unique.append(r)
    return unique


def extract_clause_id(text: str, header_path: list[str]) -> str:
    """Return the most specific clause ID found in headers or text."""
    for source in [" ".join(header_path), text[:500]]:
        m = _CLAUSE_RE.search(source)
        if m:
            return m.group(1)
    return ""


def contains_table(text: str) -> bool:
    return bool(_TABLE_RE.search(text))


def build_chunk_metadata(
    doc_meta: dict[str, Any],
    page_num: int,
    header_path: list[str],
    text: str,
    chunk_type: str,
    parent_id: str = "",
) -> dict[str, Any]:
    return {
        "source_doc": doc_meta.get("source_doc", ""),
        "authority": doc_meta.get("authority", ""),
        "category": doc_meta.get("category", ""),
        "page_num": page_num,
        "section": header_path[-1] if header_path else "",
        "clause_id": extract_clause_id(text, header_path),
        "chunk_type": chunk_type,
        "parent_id": parent_id,
        "contains_table": contains_table(text),
        "cross_refs": extract_cross_refs(text),
    }
