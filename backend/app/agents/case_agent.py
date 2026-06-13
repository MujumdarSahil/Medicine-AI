"""
MedMentor AI — Clinical Case Correlation Agent (Phase 3)
Generates realistic clinical vignettes with differential diagnosis and textbook references.
"""

from app.chroma_client import query_by_topic
from app.llm import chat_completion

CASE_SYSTEM_PROMPT = """You are MedMentor AI, an expert clinical case generator for MBBS students.

Using the provided textbook context, generate a realistic, clinically accurate case vignette.

## Output Format (STRICTLY follow this JSON structure)

Return ONLY valid JSON with these fields:

{{
  "vignette": {{
    "chief_complaint": "...",
    "history": "A detailed HPI paragraph (age, sex, duration, symptoms, severity, associated symptoms, timeline)...",
    "past_history": "...",
    "examination": {{
      "general": "...",
      "vitals": "HR: X/min, BP: X/Y mmHg, RR: X/min, Temp: X°C, SpO2: X%",
      "systemic": "...",
      "specific_findings": ["finding 1", "finding 2", "..."]
    }},
    "investigations": {{
      "bloods": ["...", "..."],
      "imaging": ["...", "..."],
      "special": ["...", "..."]
    }}
  }},
  "questions": [
    "What is the most likely diagnosis?",
    "What is the single most important investigation?",
    "Outline the management of this patient."
  ],
  "differentials": [
    {{
      "diagnosis": "...",
      "supporting_features": ["...", "..."],
      "against_features": ["...", "..."],
      "likelihood": "Most likely / Possible / Less likely"
    }}
  ],
  "final_diagnosis": "...",
  "explanation": "Brief clinical reasoning explaining why this is the diagnosis...",
  "references": [
    {{
      "section": "...",
      "page": "...",
      "note": "Textbook reference supporting the diagnosis/management"
    }}
  ],
  "key_learning_points": ["...", "...", "..."]
}}

## Textbook Context
{context}
"""


def build_context(chunks: list[dict]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, 1):
        meta = chunk["metadata"]
        page = meta.get("page_number", "?")
        section = meta.get("section_type", "General")
        parts.append(f"[Page {page} | {section}]\n{chunk['text']}")
    return "\n---\n".join(parts)


import json
import re


def extract_json(text: str) -> dict:
    """Extract JSON from LLM response, handling markdown code blocks."""
    # Remove markdown code blocks
    text = re.sub(r'```(?:json)?\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    text = text.strip()

    # Find JSON object
    start = text.find('{')
    end = text.rfind('}') + 1
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError as e:
            print(f"[!] JSON parse error: {e}")

    # Return minimal fallback
    return {
        "vignette": {"chief_complaint": "See explanation below", "history": text},
        "differentials": [],
        "final_diagnosis": "Unable to parse",
        "explanation": text,
        "references": [],
        "key_learning_points": []
    }


async def generate_case(topic_title: str) -> dict:
    """Generate a clinical case for the given topic."""
    chunks = query_by_topic(topic_title, n_results=15)
    context = build_context(chunks)
    system_prompt = CASE_SYSTEM_PROMPT.format(context=context)
    user_message = (
        f"Generate a clinical case vignette for a MBBS student about: {topic_title}\n"
        f"Make it realistic, clinically accurate, and exam-relevant (NEXT exam pattern).\n"
        f"Include subtle but classic findings that distinguish this from differentials."
    )

    raw = await chat_completion(system_prompt, user_message, temperature=0.6, max_tokens=3000)
    case_data = extract_json(raw)
    case_data["topic_title"] = topic_title
    case_data["raw_context_pages"] = list({
        c["metadata"].get("page_number") for c in chunks if c["metadata"].get("page_number")
    })
    return case_data
