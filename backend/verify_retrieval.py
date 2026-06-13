"""
MedMentor AI — Retrieval Verification Script
Usage: python verify_retrieval.py --query "heart failure" [--n 5]
"""

import argparse
import os
import sys
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
CHROMA_COLLECTION = "medicine_textbook"
EMBED_MODEL = "all-MiniLM-L6-v2"


def verify(query: str, n_results: int = 5):
    print(f"\n{'=' * 60}")
    print(f"  Query: \"{query}\"")
    print(f"{'=' * 60}\n")

    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBED_MODEL
    )

    try:
        collection = client.get_collection(
            name=CHROMA_COLLECTION,
            embedding_function=embed_fn
        )
    except Exception as e:
        print(f"[ERROR] Could not load collection '{CHROMA_COLLECTION}': {e}")
        print("        Have you run ingest_pdf.py yet?")
        sys.exit(1)

    total_docs = collection.count()
    print(f"Collection '{CHROMA_COLLECTION}' contains {total_docs} chunks.\n")

    results = collection.query(query_texts=[query], n_results=n_results)

    for i, (doc, meta, dist) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    )):
        relevance = round((1 - dist) * 100, 1)
        print(f"── Result {i+1} (relevance: {relevance}%) ──")
        print(f"   Topic     : {meta.get('topic', 'N/A')}")
        print(f"   System    : {meta.get('system', 'N/A')}")
        print(f"   Section   : {meta.get('section_type', 'N/A')}")
        print(f"   Page      : {meta.get('page_number', 'N/A')}")
        print(f"   Chapter   : {meta.get('chapter', 'N/A')}")
        print(f"   Text      : {doc[:300]}...")
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify ChromaDB retrieval quality")
    parser.add_argument("--query", "-q", required=True, help="Disease/topic to query")
    parser.add_argument("--n", type=int, default=5, help="Number of results (default: 5)")
    args = parser.parse_args()
    verify(args.query, args.n)
