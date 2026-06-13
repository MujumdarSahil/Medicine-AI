"""
MedMentor AI — Tests Router (Phase 4)
MCQ generation, submission, and daily due questions.
"""

from datetime import datetime, timezone, date, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from bson import ObjectId

from app.database import topics_col, tests_col, test_attempts_col, progress_col
from app.agents.test_agent import generate_mcqs

router = APIRouter()

# Spaced repetition intervals (days)
SR_INTERVALS = [1, 3, 7, 14, 30, 60]


def serialize(doc: dict) -> dict:
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


def next_interval(current_interval: int, correct: bool) -> int:
    """Calculate next review interval."""
    if not correct:
        return 1
    idx = SR_INTERVALS.index(current_interval) if current_interval in SR_INTERVALS else 0
    next_idx = min(idx + 1, len(SR_INTERVALS) - 1)
    return SR_INTERVALS[next_idx]


# ── Generate Questions ────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    topic_id: str
    count: Optional[int] = 5
    difficulty: Optional[str] = "Mixed"  # Easy | Medium | Hard | Mixed


@router.post("/test/generate")
async def generate_test(body: GenerateRequest):
    """Generate MCQs for a topic and store in med_tests."""
    topic = await topics_col().find_one({"_id": ObjectId(body.topic_id)})
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    topic_title = topic["title"]
    questions = await generate_mcqs(topic_title, count=body.count, difficulty=body.difficulty)

    inserted_ids = []
    for q in questions:
        doc = {
            "topic_id": body.topic_id,
            "topic_title": topic_title,
            "system": topic.get("system", ""),
            "created_at": datetime.now(timezone.utc),
            **q
        }
        result = await tests_col().insert_one(doc)
        inserted_ids.append(str(result.inserted_id))

    # Fetch and return
    stored = []
    for qid in inserted_ids:
        doc = await tests_col().find_one({"_id": ObjectId(qid)})
        stored.append(serialize(doc))

    return {"questions": stored, "count": len(stored), "topic_title": topic_title}


# ── Submit Answer ─────────────────────────────────────────────────────────────

class SubmitRequest(BaseModel):
    question_id: str
    selected_answer: str  # "A", "B", "C", or "D"


@router.post("/test/submit")
async def submit_answer(body: SubmitRequest):
    """Record a test attempt and update spaced repetition progress."""
    question = await tests_col().find_one({"_id": ObjectId(body.question_id)})
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    is_correct = body.selected_answer.upper() == question["correct_answer"].upper()
    topic_id = question["topic_id"]
    now = datetime.now(timezone.utc)
    today = now.date()

    # Record attempt
    attempt = {
        "topic_id": topic_id,
        "topic_title": question.get("topic_title", ""),
        "question_id": body.question_id,
        "selected_answer": body.selected_answer.upper(),
        "correct_answer": question["correct_answer"],
        "is_correct": is_correct,
        "timestamp": now,
        "difficulty": question.get("difficulty", "Medium")
    }
    await test_attempts_col().insert_one(attempt)

    # Update spaced repetition progress
    prog = await progress_col().find_one({"topic_id": topic_id})
    if prog:
        current_interval = prog.get("current_interval", 1)
        review_count = prog.get("review_count", 0) + 1
        accuracy_history = prog.get("accuracy_history", [])
        accuracy_history.append({"date": today.isoformat(), "correct": is_correct})

        new_interval = next_interval(current_interval, is_correct)
        next_due = (today + timedelta(days=new_interval)).isoformat()

        await progress_col().update_one(
            {"topic_id": topic_id},
            {"$set": {
                "last_reviewed": today.isoformat(),
                "next_due_date": next_due,
                "current_interval": new_interval,
                "review_count": review_count,
                "accuracy_history": accuracy_history[-50:]  # keep last 50
            }}
        )
    else:
        # First attempt — create progress record
        next_due = (today + timedelta(days=1)).isoformat()
        await progress_col().insert_one({
            "topic_id": topic_id,
            "topic_title": question.get("topic_title", ""),
            "system": question.get("system", ""),
            "last_reviewed": today.isoformat(),
            "next_due_date": next_due,
            "current_interval": 1,
            "review_count": 1,
            "accuracy_history": [{"date": today.isoformat(), "correct": is_correct}]
        })

    return {
        "is_correct": is_correct,
        "correct_answer": question["correct_answer"],
        "explanation": question.get("explanation", ""),
        "selected_answer": body.selected_answer.upper(),
        "question": question.get("question", ""),
        "options": question.get("options", {})
    }


# ── Daily Due Questions ───────────────────────────────────────────────────────

@router.get("/test/daily")
async def daily_questions(limit: int = Query(20, le=50)):
    """Return today's due questions based on spaced repetition schedule."""
    today = date.today().isoformat()

    # Get topics due today
    cursor = progress_col().find({"next_due_date": {"$lte": today}})
    due_topics = []
    async for doc in cursor:
        due_topics.append(doc["topic_id"])

    if not due_topics:
        return {"questions": [], "message": "No topics due today! Great job! 🎉", "due_count": 0}

    # Get recent questions for due topics (prefer questions not recently attempted)
    all_questions = []
    per_topic = max(1, limit // len(due_topics))

    for topic_id in due_topics[:10]:  # cap at 10 topics per day
        cursor = tests_col().find({"topic_id": topic_id}).sort("created_at", -1).limit(per_topic)
        async for q in cursor:
            all_questions.append(serialize(q))

    return {
        "questions": all_questions[:limit],
        "due_count": len(due_topics),
        "today": today
    }


# ── Get Questions for Topic ───────────────────────────────────────────────────

@router.get("/test/topic/{topic_id}")
async def get_topic_questions(topic_id: str, limit: int = Query(10, le=30)):
    """Get existing questions for a topic."""
    cursor = tests_col().find({"topic_id": topic_id}).sort("created_at", -1).limit(limit)
    questions = []
    async for doc in cursor:
        questions.append(serialize(doc))
    return {"questions": questions, "count": len(questions)}
