from loguru import logger
from sentence_transformers import SentenceTransformer
from fastembed import SparseTextEmbedding


class DenseEmbedder:
    def __init__(self, model_name: str = "BAAI/bge-m3", batch_size: int = 32) -> None:
        logger.info(f"Loading dense embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.batch_size = batch_size
        self.dimension: int = self.model.get_sentence_embedding_dimension()
        logger.info(f"  Embedding dimension: {self.dimension}")

    def embed(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=len(texts) > 100,
            normalize_embeddings=True,
        )
        return embeddings.tolist()


class SparseEmbedder:
    """BM25 sparse embeddings via fastembed, compatible with Qdrant sparse vectors."""

    def __init__(self, model_name: str = "Qdrant/bm25") -> None:
        logger.info(f"Loading sparse embedding model: {model_name}")
        self.model = SparseTextEmbedding(model_name=model_name)

    def embed(self, texts: list[str]) -> list[dict]:
        """
        Returns list of {"indices": [...], "values": [...]} dicts.
        One entry per input text.
        """
        results = list(self.model.embed(texts))
        return [
            {"indices": r.indices.tolist(), "values": r.values.tolist()}
            for r in results
        ]
