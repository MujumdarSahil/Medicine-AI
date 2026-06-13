"""
MedMentor AI — Topics Router (Phase 2)
Endpoints: chapters, topics, and explain (RAG streaming chat)
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from bson import ObjectId

from app.database import chapters_col, topics_col, chat_sessions_col
from app.agents.explain_agent import explain_topic

router = APIRouter()


def serialize(doc: dict) -> dict:
    """Convert MongoDB document to JSON-serializable dict."""
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


# ── Chapter Endpoints ─────────────────────────────────────────────────────────

@router.get("/chapters")
async def list_chapters():
    """List all chapters/systems."""
    cursor = chapters_col().find({}, {"_id": 1, "name": 1, "system": 1, "topics": 1, "page_start": 1, "page_end": 1})
    chapters = []
    async for doc in cursor:
        chapters.append(serialize(doc))
    return {"chapters": chapters, "count": len(chapters)}


@router.get("/chapters/{chapter_id}")
async def get_chapter(chapter_id: str):
    """Get chapter details by ID."""
    doc = await chapters_col().find_one({"_id": ObjectId(chapter_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return serialize(doc)


# ── Topic Endpoints ───────────────────────────────────────────────────────────

@router.get("/topics")
async def list_topics(chapter_id: Optional[str] = Query(None), system: Optional[str] = Query(None)):
    """List topics, optionally filtered by chapter or system."""
    query = {}
    if chapter_id:
        chapter = await chapters_col().find_one({"_id": ObjectId(chapter_id)})
        if chapter:
            query["chapter"] = chapter["name"]
    if system:
        query["system"] = {"$regex": system, "$options": "i"}

    cursor = topics_col().find(query, {"_id": 1, "title": 1, "system": 1, "chapter": 1, "page_refs": 1, "sections": 1})
    topics = []
    async for doc in cursor:
        topics.append(serialize(doc))
    return {"topics": topics, "count": len(topics)}


@router.get("/topics/search")
async def search_topics(q: str = Query(..., min_length=2)):
    """Search topics by title."""
    cursor = topics_col().find(
        {"title": {"$regex": q, "$options": "i"}},
        {"_id": 1, "title": 1, "system": 1, "chapter": 1}
    ).limit(20)
    topics = []
    async for doc in cursor:
        topics.append(serialize(doc))
    return {"topics": topics}


@router.get("/topic/{topic_id}")
async def get_topic(topic_id: str):
    """Get full topic metadata."""
    doc = await topics_col().find_one({"_id": ObjectId(topic_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Topic not found")
    return serialize(doc)


# ── Explain Endpoint (RAG Chat) ───────────────────────────────────────────────

class ExplainRequest(BaseModel):
    query: Optional[str] = ""
    session_id: Optional[str] = None
    stream: Optional[bool] = True


@router.post("/topic/{topic_id}/explain")
async def explain(topic_id: str, body: ExplainRequest):
    """
    RAG-powered topic explanation.
    Streams response as Server-Sent Events (SSE).
    """
    # Get topic
    topic = await topics_col().find_one({"_id": ObjectId(topic_id)})
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    topic_title = topic["title"]
    session_id = body.session_id or str(uuid.uuid4())

    # Fetch conversation history for this session
    session = await chat_sessions_col().find_one({"session_id": session_id})
    history = session["messages"] if session else []

    if body.stream:
        async def event_stream():
            full_response = []
            generator = await explain_topic(
                topic_title=topic_title,
                user_query=body.query or "",
                conversation_history=history,
                stream=True
            )
            async for token in generator:
                full_response.append(token)
                yield f"data: {json.dumps(token)}\n\n"

            # Store conversation turn
            full_text = "".join(full_response)
            turn = [
                {"role": "user", "content": body.query or f"Explain {topic_title}", "timestamp": datetime.now(timezone.utc).isoformat()},
                {"role": "assistant", "content": full_text, "timestamp": datetime.now(timezone.utc).isoformat()}
            ]
            await chat_sessions_col().update_one(
                {"session_id": session_id},
                {"$set": {"topic_id": topic_id, "topic_title": topic_title, "updated_at": datetime.now(timezone.utc)},
                 "$push": {"messages": {"$each": turn}}},
                upsert=True
            )
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={"X-Session-ID": session_id}
        )
    else:
        # Non-streaming
        response = await explain_topic(
            topic_title=topic_title,
            user_query=body.query or "",
            conversation_history=history,
            stream=False
        )
        # Store turn
        turn = [
            {"role": "user", "content": body.query or f"Explain {topic_title}", "timestamp": datetime.now(timezone.utc).isoformat()},
            {"role": "assistant", "content": response, "timestamp": datetime.now(timezone.utc).isoformat()}
        ]
        await chat_sessions_col().update_one(
            {"session_id": session_id},
            {"$set": {"topic_id": topic_id, "topic_title": topic_title, "updated_at": datetime.now(timezone.utc)},
             "$push": {"messages": {"$each": turn}}},
            upsert=True
        )
        return {"response": response, "session_id": session_id}


@router.get("/topic/{topic_id}/sessions")
async def list_sessions(topic_id: str):
    """List chat sessions for a topic."""
    cursor = chat_sessions_col().find(
        {"topic_id": topic_id},
        {"session_id": 1, "topic_title": 1, "updated_at": 1, "messages": {"$slice": -1}}
    ).sort("updated_at", -1).limit(10)
    sessions = []
    async for doc in cursor:
        sessions.append(serialize(doc))
    return {"sessions": sessions}


@router.get("/topic/{topic_id}/session/{session_id}")
async def get_session(topic_id: str, session_id: str):
    """Get full chat session history."""
    doc = await chat_sessions_col().find_one({"session_id": session_id, "topic_id": topic_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Session not found")
    return serialize(doc)
