from langchain_core.tools import tool

from src.retrieval.retriever import RetrievedChunk, Retriever


def _format_chunks(chunks: list[RetrievedChunk]) -> str:
    """Render retrieved chunks as a numbered list for the LLM context window."""
    if not chunks:
        return "No relevant passages found in the building code database."

    parts: list[str] = []
    for i, chunk in enumerate(chunks, 1):
        parts.append(
            f"[{i}] {chunk.citation()}\n\n"
            f"VERBATIM CLAUSE TEXT:\n"
            f"{chunk.parent_text}"
        )

    return "\n\n---\n\n".join(parts)


def make_tools(retriever: Retriever) -> list:
    """
    Return the two retrieval tools bound to a given Retriever instance.

    Using a factory keeps the tools stateless at the module level and avoids
    loading embedding/reranker models on import.
    """

    @tool
    def retrieve(query: str) -> str:
        """
        Search the Singapore building code database for passages relevant to a
        question or topic. Use this for general queries, compliance questions, and
        any time you need to find regulatory requirements. Returns the full section
        context (parent chunk) for each match, not just the matched sentence.

        Args:
            query: Natural-language question or keyword phrase.
        """
        chunks = retriever.retrieve(query)
        return _format_chunks(chunks)

    @tool
    def retrieve_clause(reference: str) -> str:
        """
        Look up a specific clause, section, or standard by its reference code.
        Use this to follow cross-references found in other retrieved passages
        (e.g. "SCDF FSR 6.4.2", "SS 578 Clause 3", "BCA Approved Document Part C").
        Returns up to 3 matching passages.

        Args:
            reference: The exact clause or standard reference string to look up.
        """
        chunks = retriever.retrieve(reference, k=3)
        return _format_chunks(chunks)

    return [retrieve, retrieve_clause]
