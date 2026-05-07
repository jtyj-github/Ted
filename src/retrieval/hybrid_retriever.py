from loguru import logger
from qdrant_client import QdrantClient
from qdrant_client.models import Fusion, FusionQuery, Prefetch, SparseVector

from src.ingestion.embedder import DenseEmbedder, SparseEmbedder
from src.ingestion.qdrant_store import DENSE_VECTOR, SPARSE_VECTOR


class HybridRetriever:
    """
    Qdrant hybrid search: dense (bge-m3) + sparse (BM25) fused with RRF.

    At query time both vectors are computed for the query string, then
    Qdrant runs two prefetch passes (one per vector space) and merges
    results with Reciprocal Rank Fusion before returning the final list.
    """

    def __init__(
        self,
        client: QdrantClient,
        collection_name: str,
        dense_embedder: DenseEmbedder,
        sparse_embedder: SparseEmbedder,
    ) -> None:
        self.client = client
        self.collection_name = collection_name
        self.dense_embedder = dense_embedder
        self.sparse_embedder = sparse_embedder

    def search(self, query: str, limit: int = 20) -> list[dict]:
        """
        Return up to `limit` candidate chunks, sorted by RRF-fused score.

        Each result dict has:
            id, score, text, parent_text, metadata
        """
        dense_vec = self.dense_embedder.embed([query])[0]
        sparse_vec = self.sparse_embedder.embed([query])[0]

        logger.debug(f"Hybrid search: '{query[:60]}…' limit={limit}")

        response = self.client.query_points(
            collection_name=self.collection_name,
            prefetch=[
                Prefetch(
                    query=dense_vec,
                    using=DENSE_VECTOR,
                    limit=limit,
                ),
                Prefetch(
                    query=SparseVector(
                        indices=sparse_vec["indices"],
                        values=sparse_vec["values"],
                    ),
                    using=SPARSE_VECTOR,
                    limit=limit,
                ),
            ],
            query=FusionQuery(fusion=Fusion.RRF),
            limit=limit,
            with_payload=True,
        )

        results = []
        for point in response.points:
            payload: dict = point.payload or {}
            results.append({
                "id": str(point.id),
                "score": point.score,
                "text": payload.pop("text", ""),
                "parent_text": payload.pop("parent_text", ""),
                "metadata": payload,
            })

        logger.debug(f"  Retrieved {len(results)} candidates")
        return results
