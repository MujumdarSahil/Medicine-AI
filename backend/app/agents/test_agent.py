"""
MedMentor AI — Test/MCQ Generation Agent (Phase 4)
Generates NEXT-exam-pattern MCQs with explanations.
"""

import json
import re
from app.chroma_client import query_by_topic
from app.llm import chat_completion

TEST_SYSTEM_PROMPT = """You are MedMentor AI, an expert MCQ writer for MBBS NEXT (National Exit Test) exam preparation.

Using the provided textbook context, generate high-quality MCQs.

## Question Types
- Single best answer (SBA) — 1 correct out of A/B/C/D
- Clinical scenario based — start with a patient presentation
- Image-based description (describe the finding textually)

## NEXT Exam Pattern Rules
- Questions should test APPLICATION, not rote recall
- Include clinical reasoning, interpretation of investigations
- Distractors should be plausible (commonly confused conditions)
- Difficulty levels: Easy (recall), Medium (application), Hard (analysis)

## Output Format (return ONLY valid JSON array)

[
  {{
    "question": "A 45-year-old male presents with...",
    "options": {{
      "A": "...",
      "B": "...",
      "C": "...",
      "D": "..."
    }},
    "correct_answer": "A",
    "explanation": "Detailed explanation of why A is correct and why others are wrong...",
    "difficulty": "Medium",
    "section": "Clinical Features",
    "page_reference": "p. X"
  }}
]

## Textbook Context
{context}
"""


def extract_json_array(text: str) -> list:
    text = re.sub(r'```(?:json)?\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    text = text.strip()
    start = text.find('[')
    end = text.rfind(']') + 1
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError as e:
            print(f"[!] JSON parse error in test gen: {e}")
    return []


def build_context(chunks: list[dict]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, 1):
        meta = chunk["metadata"]
        page = meta.get("page_number", "?")
        section = meta.get("section_type", "General")
        parts.append(f"[Page {page} | {section}]\n{chunk['text']}")
    return "\n---\n".join(parts)


async def generate_mcqs(topic_title: str, count: int = 5, difficulty: str = "Mixed") -> list[dict]:
    """Generate MCQs for the given topic."""
    chunks = query_by_topic(topic_title, n_results=15)
    context = build_context(chunks)
    system_prompt = TEST_SYSTEM_PROMPT.format(context=context)

    diff_instruction = ""
    if difficulty != "Mixed":
        diff_instruction = f"Generate all questions at {difficulty} difficulty level."

    user_message = (
        f"Generate {count} high-quality NEXT-pattern MCQs about: {topic_title}\n"
        f"{diff_instruction}\n"
        f"Mix question types: pure knowledge, clinical scenario, investigation interpretation.\n"
        f"Make distractors clinically plausible."
    )

    raw = await chat_completion(system_prompt, user_message, temperature=0.5, max_tokens=3000)
    questions = extract_json_array(raw)

    # Enrich with metadata
    for q in questions:
        q["topic_title"] = topic_title
        q["topic_system"] = chunks[0]["metadata"].get("system", "") if chunks else ""

    return questions
