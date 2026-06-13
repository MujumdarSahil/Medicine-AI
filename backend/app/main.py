"""
MedMentor AI — FastAPI Application Entry Point
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from app.database import connect_db, close_db
from app.chroma_client import init_chroma
from app.routers import topics, cases, tests, progress

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    await connect_db()
    init_chroma()
    print("[+] MedMentor AI backend started.")
    yield
    await close_db()
    print("[+] MedMentor AI backend shutdown.")


app = FastAPI(
    title="MedMentor AI",
    description="MBBS Medicine AI Tutor — RAG-powered learning platform",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(topics.router, prefix="/api", tags=["Topics"])
app.include_router(cases.router, prefix="/api", tags=["Cases"])
app.include_router(tests.router, prefix="/api", tags=["Tests"])
app.include_router(progress.router, prefix="/api", tags=["Progress"])


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "message": "MedMentor AI backend is running"}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy", "version": "1.0.0"}
