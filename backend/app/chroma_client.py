"""
MedMentor AI — ChromaDB Client
"""

import os
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
CHROMA_COLLECTION = "medicine_textbook"
EMBED_MODEL = "all-MiniLM-L6-v2"

_client = None
_collection = None


def init_chroma():
    global _client, _collection
    _client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBED_MODEL
    )
    _collection = _client.get_or_create_collection(
        name=CHROMA_COLLECTION,
        embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"}
    )
    count = _collection.count()
    print(f"[+] ChromaDB ready: collection='{CHROMA_COLLECTION}', chunks={count}")


def get_collection():
    if _collection is None:
        raise RuntimeError("ChromaDB not initialised. Call init_chroma() first.")
    return _collection


def query_chunks(query: str, n_results: int = 10, where: dict = None) -> list[dict]:
    """
    Query ChromaDB and return list of {text, metadata, distance}.
    Optionally filter by metadata with `where` dict.
    """
    col = get_collection()
    kwargs = {"query_texts": [query], "n_results": n_results}
    if where:
        kwargs["where"] = where

    results = col.query(**kwargs)
    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        chunks.append({
            "text": doc,
            "metadata": meta,
            "relevance": round((1 - dist) * 100, 1)
        })
    return chunks


def query_by_topic(topic: str, n_results: int = 12) -> list[dict]:
    """Query chunks filtered by topic name."""
    col = get_collection()
    # First try metadata filter
    try:
        results = col.query(
            query_texts=[topic],
            n_results=n_results,
            where={"topic": {"$eq": topic}}
        )
        chunks = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ):
            chunks.append({"text": doc, "metadata": meta, "relevance": round((1-dist)*100,1)})
        if chunks:
            return chunks
    except Exception:
        pass
    # Fallback: semantic search without filter
    return query_chunks(topic, n_results=n_results)
