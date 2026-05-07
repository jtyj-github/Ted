from pathlib import Path

from loguru import logger
from tqdm import tqdm

from src.config import (
    COLLECTION_NAME,
    DOCS_DIR,
    EMBEDDING_DIM,
    EMBEDDING_MODEL,
    QDRANT_HOST,
    QDRANT_PORT,
)
from src.document_registry import lookup
from src.ingestion.chunker import HierarchicalChunker
from src.ingestion.embedder import DenseEmbedder, SparseEmbedder
from src.ingestion.pdf_parser import parse_pdf
from src.ingestion.qdrant_store import QdrantStore


def run_ingestion(
    docs_dir: Path = DOCS_DIR,
    single_file: Path | None = None,
    force_recreate: bool = False,
) -> None:
    chunker = HierarchicalChunker()
    dense_embedder = DenseEmbedder(model_name=EMBEDDING_MODEL)
    sparse_embedder = SparseEmbedder()
    store = QdrantStore(host=QDRANT_HOST, port=QDRANT_PORT)
    store.create_collection(COLLECTION_NAME, EMBEDDING_DIM, force_recreate=force_recreate)

    if single_file:
        pdf_files = [single_file]
        docs_dir = single_file.parent
    else:
        pdf_files = sorted(docs_dir.rglob("*.pdf"))

    logger.info(f"Found {len(pdf_files)} PDF(s) to ingest")

    total_docs = 0
    total_children = 0
    failed: list[str] = []

    for pdf_path in tqdm(pdf_files, desc="Ingesting", unit="doc"):
        try:
            abs_path = pdf_path.resolve()
            try:
                rel_path = abs_path.relative_to(DOCS_DIR.resolve())
            except ValueError:
                rel_path = Path(pdf_path.name)
            doc_meta = lookup(rel_path)

            pages = parse_pdf(pdf_path)
            _, children = chunker.chunk_document(pages, doc_meta)

            if not children:
                logger.warning(f"  Skipping — no chunks: {pdf_path.name}")
                continue

            texts = [c["text"] for c in children]
            dense_vecs = dense_embedder.embed(texts)
            sparse_vecs = sparse_embedder.embed(texts)

            store.upsert(COLLECTION_NAME, children, dense_vecs, sparse_vecs)

            total_docs += 1
            total_children += len(children)

        except Exception as exc:
            logger.error(f"  Failed: {pdf_path.name} — {exc}")
            failed.append(pdf_path.name)

    logger.info(
        f"\nIngestion complete: {total_docs} documents, {total_children} chunks"
    )
    if failed:
        logger.warning(f"Failed documents ({len(failed)}): {', '.join(failed)}")
