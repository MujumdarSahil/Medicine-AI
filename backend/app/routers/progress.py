"""
MedMentor AI — Progress Router (Phase 4)
Spaced repetition progress tracking, stats, streak.
"""

from datetime import datetime, timezone, date, timedelta
from fastapi import APIRouter
from bson import ObjectId

from app.database import progress_col, test_attempts_col, topics_col

router = APIRouter()


def serialize(doc: dict) -> dict:
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


@router.get("/progress")
async def get_overall_progress():
    """Overall progress stats: accuracy by system, streak, topics studied."""
    today = date.today()

    # Accuracy by system
    cursor = progress_col().find({})
    system_stats = {}
    topics_reviewed = 0
    total_reviews = 0

    async for doc in cursor:
        topics_reviewed += 1
        system = doc.get("system", "General")
        history = doc.get("accuracy_history", [])
        correct = sum(1 for h in history if h.get("correct"))
        total = len(history)
        total_reviews += total

        if system not in system_stats:
            system_stats[system] = {"correct": 0, "total": 0, "topics": 0}
        system_stats[system]["correct"] += correct
        system_stats[system]["total"] += total
        system_stats[system]["topics"] += 1

    # Calculate accuracy percentage per system
    for sys_name in system_stats:
        s = system_stats[sys_name]
        s["accuracy"] = round((s["correct"] / s["total"] * 100), 1) if s["total"] > 0 else 0

    # Calculate streak (consecutive days with attempts)
    streak = await calculate_streak()

    # Topics due today
    today_iso = today.isoformat()
    due_count = await progress_col().count_documents({"next_due_date": {"$lte": today_iso}})

    # Total attempts
    total_attempts = await test_attempts_col().count_documents({})
    correct_attempts = await test_attempts_col().count_documents({"is_correct": True})
    overall_accuracy = round(correct_attempts / total_attempts * 100, 1) if total_attempts > 0 else 0

    return {
        "overall_accuracy": overall_accuracy,
        "total_attempts": total_attempts,
        "topics_reviewed": topics_reviewed,
        "total_reviews": total_reviews,
        "due_today": due_count,
        "streak_days": streak,
        "system_stats": system_stats,
        "today": today_iso
    }


async def calculate_streak() -> int:
    """Calculate consecutive days with at least one attempt."""
    # Get all unique attempt dates
    pipeline = [
        {"$group": {"_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}}}},
        {"$sort": {"_id": -1}},
        {"$limit": 100}
    ]
    cursor = test_attempts_col().aggregate(pipeline)
    dates = []
    async for doc in cursor:
        dates.append(doc["_id"])

    if not dates:
        return 0

    today = date.today()
    streak = 0
    check_date = today

    for d in dates:
        d_date = date.fromisoformat(d)
        if d_date == check_date or d_date == check_date - timedelta(days=1):
            if d_date == check_date - timedelta(days=1):
                check_date = d_date
            streak += 1
            check_date = d_date - timedelta(days=1)
        else:
            break

    return streak


@router.get("/progress/due")
async def get_due_topics():
    """Get topics due for revision today."""
    today = date.today().isoformat()
    cursor = progress_col().find({"next_due_date": {"$lte": today}}).sort("next_due_date", 1)
    topics = []
    async for doc in cursor:
        topics.append(serialize(doc))
    return {"due_topics": topics, "count": len(topics)}


@router.get("/progress/topic/{topic_id}")
async def get_topic_progress(topic_id: str):
    """Get spaced repetition progress for a specific topic."""
    doc = await progress_col().find_one({"topic_id": topic_id})
    if not doc:
        return {"topic_id": topic_id, "reviewed": False, "message": "No attempts yet"}
    return serialize(doc)


@router.get("/progress/history")
async def get_attempt_history(limit: int = 50):
    """Get recent test attempt history."""
    cursor = test_attempts_col().find({}).sort("timestamp", -1).limit(limit)
    attempts = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        doc["timestamp"] = doc["timestamp"].isoformat() if hasattr(doc.get("timestamp"), "isoformat") else str(doc.get("timestamp", ""))
        attempts.append(doc)
    return {"attempts": attempts, "count": len(attempts)}


@router.get("/progress/calendar")
async def get_calendar_heatmap():
    """Get daily attempt counts for heatmap (last 90 days)."""
    pipeline = [
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
            "count": {"$sum": 1},
            "correct": {"$sum": {"$cond": ["$is_correct", 1, 0]}}
        }},
        {"$sort": {"_id": 1}},
        {"$limit": 90}
    ]
    cursor = test_attempts_col().aggregate(pipeline)
    calendar = []
    async for doc in cursor:
        calendar.append({
            "date": doc["_id"],
            "count": doc["count"],
            "correct": doc["correct"],
            "accuracy": round(doc["correct"] / doc["count"] * 100, 0) if doc["count"] > 0 else 0
        })
    return {"calendar": calendar}
