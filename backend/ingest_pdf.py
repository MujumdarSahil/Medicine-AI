"""
MedMentor AI — PDF Ingestion Script (Phase 1)
Run once to populate ChromaDB and MongoDB with textbook content.
Usage: python ingest_pdf.py [--reset]
"""

import os
import re
import sys
import json
import argparse
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import fitz  # PyMuPDF
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
MEDICINE_PDF_PATH = os.getenv("MEDICINE_PDF_PATH", "")
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "jarvis")
CHROMA_COLLECTION = "medicine_textbook"
EMBED_MODEL = "all-MiniLM-L6-v2"

# ── Known Medical Systems / Chapters ─────────────────────────────────────────
MEDICAL_SYSTEMS = [
    "Cardiology", "Cardiovascular", "Respiratory", "Pulmonology",
    "Nephrology", "Renal", "Neurology", "Neurological",
    "Gastroenterology", "Gastrointestinal", "Hepatology",
    "Endocrinology", "Endocrine", "Infectious Diseases", "Infections",
    "Hematology", "Haematology", "Rheumatology", "Musculoskeletal",
    "Dermatology", "Psychiatry", "Oncology", "Immunology",
    "Geriatrics", "Emergency Medicine", "Clinical Pharmacology",
    "Tropical Medicine", "Sexually Transmitted Diseases",
    "Nutritional Disorders", "Environmental Medicine"
]

SECTION_KEYWORDS = {
    "Definition": ["definition", "defined as", "refers to", "is a condition"],
    "Etiology": ["etiology", "aetiology", "causes", "caused by", "risk factors", "predisposing"],
    "Pathophysiology": ["pathophysiology", "pathogenesis", "mechanism", "pathology"],
    "Clinical Features": ["clinical features", "symptoms", "signs", "presentation", "manifestations", "history"],
    "Investigations": ["investigations", "diagnosis", "diagnostic", "laboratory", "tests", "findings"],
    "Management": ["management", "treatment", "therapy", "drugs", "medications", "surgical"],
    "Complications": ["complications", "prognosis", "sequelae", "outcome"]
}

CHAPTER_PATTERNS = [
    re.compile(r'^(CHAPTER\s+\d+)', re.IGNORECASE),
    re.compile(r'^(\d+\s+)(' + '|'.join(MEDICAL_SYSTEMS) + r')', re.IGNORECASE),
    re.compile(r'^(' + '|'.join(MEDICAL_SYSTEMS) + r')\s*$', re.IGNORECASE),
    re.compile(r'^SECTION\s+\d+', re.IGNORECASE),
]

CHUNK_SIZE = 800  # characters per chunk
CHUNK_OVERLAP = 150


# ── Helper Functions ──────────────────────────────────────────────────────────

def detect_system(text: str) -> str:
    """Detect which medical system a text block belongs to."""
    text_lower = text.lower()
    for system in MEDICAL_SYSTEMS:
        if system.lower() in text_lower:
            return system
    return "General Medicine"


def detect_section_type(text: str) -> str:
    """Detect which clinical section this chunk falls under."""
    text_lower = text.lower()
    for section, keywords in SECTION_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                return section
    return "General"


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start = end - overlap
        if start >= len(text):
            break
    return chunks


_chunk_counter = 0

def generate_chunk_id(topic: str, page: int, chunk_idx: int, text: str) -> str:
    global _chunk_counter
    _chunk_counter += 1
    raw = f"{_chunk_counter}_{topic}_{page}_{chunk_idx}_{text[:40]}"
    return hashlib.md5(raw.encode()).hexdigest()


def is_chapter_boundary(line: str) -> tuple[bool, str]:
    """Check if a line is a chapter/system boundary."""
    line = line.strip()
    for pattern in CHAPTER_PATTERNS:
        m = pattern.match(line)
        if m:
            return True, line
    return False, ""


def extract_topic_from_heading(line: str) -> str:
    """Extract a clean topic/disease name from a heading line."""
    line = re.sub(r'^(chapter\s+\d+[\.\:]\s*)', '', line, flags=re.IGNORECASE)
    line = re.sub(r'^\d+[\.\:]\s*', '', line)
    return line.strip().title()


# ── PDF Extraction ────────────────────────────────────────────────────────────

def extract_pdf_pages(pdf_path: str) -> list[dict]:
    """Extract all pages from PDF as list of {page_num, text}."""
    print(f"[*] Opening PDF: {pdf_path}")
    doc = fitz.open(pdf_path)
    pages = []
    total = len(doc)
    for i, page in enumerate(doc):
        text = page.get_text("text")
        pages.append({"page_num": i + 1, "text": text})
        if (i + 1) % 100 == 0:
            print(f"    Extracted {i+1}/{total} pages...")
    doc.close()
    print(f"[+] Extracted {total} pages total.")
    return pages


def parse_structure(pages: list[dict]) -> list[dict]:
    """
    Parse pages into structured blocks:
    [{chapter, system, topic, section_type, page_num, text}]
    """
    blocks = []
    current_chapter = "Introduction"
    current_system = "General Medicine"
    current_topic = "General"
    buffer_text = []
    buffer_page = 1

    heading_re = re.compile(r'^[A-Z][A-Z\s\-\/]{4,}$')  # ALL CAPS lines

    def flush_buffer():
        nonlocal buffer_text, buffer_page
        if buffer_text:
            full_text = " ".join(buffer_text).strip()
            if len(full_text) > 50:
                section = detect_section_type(full_text)
                blocks.append({
                    "chapter": current_chapter,
                    "system": current_system,
                    "topic": current_topic,
                    "section_type": section,
                    "page_num": buffer_page,
                    "text": full_text
                })
        buffer_text = []

    for page_data in pages:
        page_num = page_data["page_num"]
        lines = page_data["text"].split("\n")

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            is_boundary, boundary_text = is_chapter_boundary(stripped)

            if is_boundary or (heading_re.match(stripped) and len(stripped) > 6):
                flush_buffer()
                current_chapter = extract_topic_from_heading(stripped)
                current_system = detect_system(stripped)
                current_topic = current_chapter
                buffer_page = page_num
            else:
                if buffer_page != page_num and not buffer_text:
                    buffer_page = page_num
                buffer_text.append(stripped)

    flush_buffer()
    print(f"[+] Parsed {len(blocks)} content blocks.")
    return blocks


# ── ChromaDB Ingestion ────────────────────────────────────────────────────────

def ingest_to_chroma(blocks: list[dict], reset: bool = False):
    """Embed and store chunks in ChromaDB."""
    print(f"[*] Initialising ChromaDB at: {CHROMA_PERSIST_DIR}")
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

    if reset:
        try:
            client.delete_collection(CHROMA_COLLECTION)
            print(f"[!] Deleted existing collection '{CHROMA_COLLECTION}'")
        except Exception:
            pass

    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBED_MODEL
    )
    collection = client.get_or_create_collection(
        name=CHROMA_COLLECTION,
        embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"}
    )

    print(f"[*] Embedding and storing chunks (this may take a while)...")
    batch_ids, batch_docs, batch_metas = [], [], []
    total_chunks = 0
    seen_ids = set()  # global dedup guard

    for block in blocks:
        chunks = chunk_text(block["text"])
        for idx, chunk in enumerate(chunks):
            chunk_id = generate_chunk_id(block["topic"], block["page_num"], idx, chunk)
            if chunk_id in seen_ids:
                continue
            seen_ids.add(chunk_id)

            batch_ids.append(chunk_id)
            batch_docs.append(chunk)
            batch_metas.append({
                "chapter": block["chapter"],
                "system": block["system"],
                "topic": block["topic"],
                "section_type": block["section_type"],
                "page_number": block["page_num"],
                "chunk_index": idx
            })

            if len(batch_ids) >= 50:  # smaller batch = safer
                collection.upsert(
                    ids=batch_ids,
                    documents=batch_docs,
                    metadatas=batch_metas
                )
                total_chunks += len(batch_ids)
                print(f"    Stored {total_chunks} chunks...")
                batch_ids, batch_docs, batch_metas = [], [], []

    if batch_ids:
        collection.upsert(ids=batch_ids, documents=batch_docs, metadatas=batch_metas)
        total_chunks += len(batch_ids)

    print(f"[+] ChromaDB: stored {total_chunks} chunks in '{CHROMA_COLLECTION}'")
    return collection, total_chunks


# ── MongoDB Ingestion ─────────────────────────────────────────────────────────

async def ingest_to_mongodb(blocks: list[dict]):
    """Store chapter and topic metadata in MongoDB."""
    print(f"[*] Connecting to MongoDB: {MONGO_URI}")
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[MONGO_DB]

    chapters_col = db["med_chapters"]
    topics_col = db["med_topics"]

    # Build chapter/topic index
    chapter_map = {}  # chapter_name -> {system, topics[], page_start, page_end}
    topic_map = {}    # topic_name -> {system, chapter, page_refs[], sections[]}

    for block in blocks:
        ch = block["chapter"]
        tp = block["topic"]

        if ch not in chapter_map:
            chapter_map[ch] = {
                "name": ch,
                "system": block["system"],
                "topics": [],
                "page_start": block["page_num"],
                "page_end": block["page_num"],
                "created_at": datetime.now(timezone.utc)
            }
        chapter_map[ch]["page_end"] = max(chapter_map[ch]["page_end"], block["page_num"])
        if tp not in chapter_map[ch]["topics"]:
            chapter_map[ch]["topics"].append(tp)

        if tp not in topic_map:
            topic_map[tp] = {
                "title": tp,
                "chapter": ch,
                "system": block["system"],
                "page_refs": [],
                "sections": [],
                "summary": "",
                "created_at": datetime.now(timezone.utc)
            }
        if block["page_num"] not in topic_map[tp]["page_refs"]:
            topic_map[tp]["page_refs"].append(block["page_num"])
        if block["section_type"] not in topic_map[tp]["sections"]:
            topic_map[tp]["sections"].append(block["section_type"])

    # Upsert chapters
    for ch_name, ch_data in chapter_map.items():
        await chapters_col.update_one(
            {"name": ch_name},
            {"$set": ch_data},
            upsert=True
        )

    # Upsert topics
    for tp_name, tp_data in topic_map.items():
        await topics_col.update_one(
            {"title": tp_name, "chapter": tp_data["chapter"]},
            {"$set": tp_data},
            upsert=True
        )

    # Fetch IDs and add topic_id field
    chapters_count = await chapters_col.count_documents({})
    topics_count = await topics_col.count_documents({})

    client.close()
    print(f"[+] MongoDB: stored {chapters_count} chapters, {topics_count} topics in db '{MONGO_DB}'")
    return chapters_count, topics_count


# ── Main ──────────────────────────────────────────────────────────────────────

async def main(reset: bool = False):
    if not MEDICINE_PDF_PATH or not Path(MEDICINE_PDF_PATH).exists():
        print(f"[ERROR] PDF not found at: '{MEDICINE_PDF_PATH}'")
        print("        Please set MEDICINE_PDF_PATH in backend/.env")
        sys.exit(1)

    print("=" * 60)
    print("  MedMentor AI — PDF Ingestion")
    print("=" * 60)

    # Step 1: Extract pages
    pages = extract_pdf_pages(MEDICINE_PDF_PATH)

    # Step 2: Parse structure
    blocks = parse_structure(pages)

    # Step 3: Ingest to ChromaDB
    collection, chunk_count = ingest_to_chroma(blocks, reset=reset)

    # Step 4: Ingest to MongoDB
    ch_count, tp_count = await ingest_to_mongodb(blocks)

    print("\n" + "=" * 60)
    print("  Ingestion Complete!")
    print(f"  ChromaDB chunks : {chunk_count}")
    print(f"  Chapters        : {ch_count}")
    print(f"  Topics          : {tp_count}")
    print("=" * 60)
    print("\nNext step: run `python verify_retrieval.py --query \"heart failure\"`")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MedMentor AI PDF Ingestion")
    parser.add_argument("--reset", action="store_true", help="Delete and re-create ChromaDB collection")
    args = parser.parse_args()
    asyncio.run(main(reset=args.reset))
