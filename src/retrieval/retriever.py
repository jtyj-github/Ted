from dataclasses import dataclass, field

from loguru import logger
from qdrant_client import QdrantClient

from src.config import (
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    FINAL_RETRIEVE_K,
    INITIAL_RETRIEVE_K,
    QDRANT_HOST,
    QDRANT_PORT,
    RERANKER_MODEL,
)
from src.ingestion.embedder import DenseEmbedder, SparseEmbedder
from src.retrieval.hybrid_retriever import HybridRetriever
from src.retrieval.reranker import Reranker


@dataclass
class RetrievedChunk:
    chunk_id: str
    score: float        # reranker score (higher = more relevant)
    text: str           # child chunk matched by vector search
    parent_text: str    # full parent section — pass this to the model
    metadata: dict = field(default_factory=dict)

    @property
    def source_doc(self) -> str:
        return self.metadata.get("source_doc", "")

    @property
    def clause_id(self) -> str:
        return self.metadata.get("clause_id", "")

    @property
    def page_num(self) -> int:
        return self.metadata.get("page_num", 0)

    def citation(self) -> str:
        """Human-readable citation string for this chunk."""
        parts = [self.source_doc]
        if self.clause_id:
            parts.append(f"Clause {self.clause_id}")
        if self.page_num:
            parts.append(f"p.{self.page_num}")
        return ", ".join(parts)


class Retriever:
    """
    Full retrieval pipeline: hybrid search → reranker → parent-child resolution.

    Models are loaded once at construction and reused across calls.
    """

    def __init__(
        self,
        collection_name: str = COLLECTION_NAME,
        initial_k: int = INITIAL_RETRIEVE_K,
        final_k: int = FINAL_RETRIEVE_K,
    ) -> None:
        self.collection_name = collection_name
        self.initial_k = initial_k
        self.final_k = final_k

        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        dense_embedder = DenseEmbedder(model_name=EMBEDDING_MODEL)
        sparse_embedder = SparseEmbedder()

        self.hybrid = HybridRetriever(client, collection_name, dense_embedder, sparse_embedder)
        self.reranker = Reranker(model_name=RERANKER_MODEL)

        logger.info(
            f"Retriever ready — collection='{collection_name}' "
            f"initial_k={initial_k} final_k={final_k}"
        )

    def retrieve(self, query: str, k: int | None = None) -> list[RetrievedChunk]:
        """
        Retrieve the most relevant chunks for `query`.

        Args:
            query: Natural-language or clause-reference query.
            k:     Number of results to return (defaults to FINAL_RETRIEVE_K).

        Returns:
            List of RetrievedChunk sorted by relevance (best first).
        """
        k = k or self.final_k
        logger.info(f"Retrieving: '{query[:80]}'")

        candidates = self.hybrid.search(query, limit=self.initial_k)
        if not candidates:
            logger.warning("  No candidates returned from hybrid search")
            return []

        reranked = self.reranker.rerank(query, candidates, top_k=k)

        chunks = [
            RetrievedChunk(
                chunk_id=r["id"],
                score=r["rerank_score"],
                text=r["text"],
                parent_text=r["parent_text"],
                metadata=r["metadata"],
            )
            for r in reranked
        ]

        logger.info(
            f"  Top result: [{chunks[0].citation()}] score={chunks[0].score:.3f}"
        )
        return chunks
