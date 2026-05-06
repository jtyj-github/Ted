from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

ROOT_DIR = Path(__file__).parent.parent

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
COLLECTION_NAME = "archi_rag_chunks"

DOCS_DIR = ROOT_DIR / os.getenv("DOCS_DIR", "docs")
CHUNKS_DIR = ROOT_DIR / os.getenv("CHUNKS_DIR", "data/chunks")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
EMBEDDING_DIM = 1024  # bge-m3 output dimension

# small chunks used for embedding + precise retrieval
CHILD_CHUNK_SIZE = 400
CHILD_CHUNK_OVERLAP = 50

# large chunks returned as context to the model
PARENT_CHUNK_SIZE = 1600
PARENT_CHUNK_OVERLAP = 100

HYBRID_ALPHA = float(os.getenv("HYBRID_ALPHA", "0.5").split("#")[0].strip())
