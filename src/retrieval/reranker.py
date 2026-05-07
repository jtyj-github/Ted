from loguru import logger
from sentence_transformers import CrossEncoder


class Reranker:
    """
    Cross-encoder reranker (BAAI/bge-reranker-v2-m3).

    Takes the candidate chunks from hybrid search and re-scores each
    (query, child_text) pair. Returns the top-k by rerank score.
    The child chunk text is used for scoring (small = precise signal);
    the caller still has access to parent_text for the model context.
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-v2-m3",
        batch_size: int = 32,
        max_length: int = 512,
    ) -> None:
        logger.info(f"Loading reranker: {model_name}")
        self.model = CrossEncoder(model_name, max_length=max_length)
        self.batch_size = batch_size

    def rerank(self, query: str, chunks: list[dict], top_k: int = 5) -> list[dict]:
        """
        Re-score `chunks` against `query` and return the top `top_k`.

        Adds a `rerank_score` key to each returned dict.
        """
        if not chunks:
            return []

        pairs = [(query, chunk["text"]) for chunk in chunks]
        scores = self.model.predict(pairs, batch_size=self.batch_size, show_progress_bar=False)

        for chunk, score in zip(chunks, scores):
            chunk["rerank_score"] = float(score)

        ranked = sorted(chunks, key=lambda c: c["rerank_score"], reverse=True)

        logger.debug(
            f"  Reranked {len(chunks)} → {top_k} "
            f"(top score: {ranked[0]['rerank_score']:.3f})"
        )
        return ranked[:top_k]
