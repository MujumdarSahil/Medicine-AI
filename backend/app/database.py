"""
MedMentor AI — MongoDB Database Client (Motor async)
"""

import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "jarvis")

_client: AsyncIOMotorClient | None = None
_db = None


async def connect_db():
    global _client, _db
    _client = AsyncIOMotorClient(MONGO_URI)
    _db = _client[MONGO_DB]
    # Verify connection
    await _client.admin.command("ping")
    print(f"[+] Connected to MongoDB: {MONGO_URI} / db={MONGO_DB}")


async def close_db():
    global _client
    if _client:
        _client.close()


def get_db():
    if _db is None:
        raise RuntimeError("Database not initialised. Call connect_db() first.")
    return _db


# Typed collection accessors
def chapters_col():
    return get_db()["med_chapters"]

def topics_col():
    return get_db()["med_topics"]

def chat_sessions_col():
    return get_db()["med_chat_sessions"]

def cases_col():
    return get_db()["med_cases"]

def tests_col():
    return get_db()["med_tests"]

def test_attempts_col():
    return get_db()["med_test_attempts"]

def progress_col():
    return get_db()["med_progress"]
