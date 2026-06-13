"""
MedMentor AI — Cases Router (Phase 3)
Clinical case correlation generation and retrieval.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from bson import ObjectId

from app.database import topics_col, cases_col
from app.agents.case_agent import generate_case

router = APIRouter()


def serialize(doc: dict) -> dict:
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


@router.post("/topic/{topic_id}/case")
async def create_case(topic_id: str, force_new: bool = False):
    """
    Generate a clinical case for a topic.
    Returns cached case from today unless force_new=True.
    """
    topic = await topics_col().find_one({"_id": ObjectId(topic_id)})
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    topic_title = topic["title"]
    today = datetime.now(timezone.utc).date().isoformat()

    # Check for today's cached case
    if not force_new:
        existing = await cases_col().find_one(
            {"topic_id": topic_id, "date": today},
            sort=[("created_at", -1)]
        )
        if existing:
            return serialize(existing)

    # Generate new case
    case_data = await generate_case(topic_title)
    doc = {
        "topic_id": topic_id,
        "topic_title": topic_title,
        "system": topic.get("system", ""),
        "date": today,
        "created_at": datetime.now(timezone.utc),
        **case_data
    }
    result = await cases_col().insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc


@router.get("/topic/{topic_id}/cases")
async def list_cases(topic_id: str):
    """List all generated cases for a topic."""
    cursor = cases_col().find(
        {"topic_id": topic_id},
        {"vignette": 1, "final_diagnosis": 1, "date": 1, "created_at": 1, "topic_title": 1}
    ).sort("created_at", -1).limit(20)
    cases = []
    async for doc in cursor:
        cases.append(serialize(doc))
    return {"cases": cases, "count": len(cases)}


@router.get("/cases/{case_id}")
async def get_case(case_id: str):
    """Get a specific case by ID."""
    doc = await cases_col().find_one({"_id": ObjectId(case_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Case not found")
    return serialize(doc)
