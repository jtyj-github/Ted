from loguru import logger
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    SparseIndexParams,
    SparseVector,
    SparseVectorParams,
    VectorParams,
)

DENSE_VECTOR = "dense"
SPARSE_VECTOR = "sparse"
_UPSERT_BATCH = 64


class QdrantStore:
    def __init__(self, host: str = "localhost", port: int = 6333) -> None:
        self.client = QdrantClient(host=host, port=port)
        logger.info(f"Connected to Qdrant at {host}:{port}")

    def create_collection(
        self,
        collection_name: str,
        embedding_dim: int,
        force_recreate: bool = False,
    ) -> None:
        existing = {c.name for c in self.client.get_collections().collections}
        if collection_name in existing:
            if not force_recreate:
                logger.info(f"Collection '{collection_name}' exists — skipping creation")
                return
            logger.info(f"Dropping collection '{collection_name}' for recreation")
            self.client.delete_collection(collection_name)

        self.client.create_collection(
            collection_name=collection_name,
            vectors_config={
                DENSE_VECTOR: VectorParams(size=embedding_dim, distance=Distance.COSINE)
            },
            sparse_vectors_config={
                SPARSE_VECTOR: SparseVectorParams(
                    index=SparseIndexParams(on_disk=False)
                )
            },
        )
        logger.info(f"Created collection '{collection_name}' (dim={embedding_dim})")

    def upsert(
        self,
        collection_name: str,
        chunks: list[dict],
        dense_embeddings: list[list[float]],
        sparse_embeddings: list[dict],
    ) -> None:
        assert len(chunks) == len(dense_embeddings) == len(sparse_embeddings), (
            "Chunk, dense, and sparse lists must have the same length"
        )

        points: list[PointStruct] = []
        for chunk, dense, sparse in zip(chunks, dense_embeddings, sparse_embeddings):
            payload = {"text": chunk["text"], "parent_text": chunk.get("parent_text", "")}
            payload.update(chunk["metadata"])

            points.append(
                PointStruct(
                    id=chunk["id"],
                    vector={
                        DENSE_VECTOR: dense,
                        SPARSE_VECTOR: SparseVector(
                            indices=sparse["indices"],
                            values=sparse["values"],
                        ),
                    },
                    payload=payload,
                )
            )

        total = len(points)
        for i in range(0, total, _UPSERT_BATCH):
            batch = points[i : i + _UPSERT_BATCH]
            self.client.upsert(collection_name=collection_name, points=batch)
            logger.debug(f"  Upserted {min(i + _UPSERT_BATCH, total)}/{total}")

        logger.info(f"  Stored {total} points in '{collection_name}'")
