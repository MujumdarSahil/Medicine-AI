"""
MedMentor AI — Explain Topic Agent (Phase 2)
RAG-powered structured explanation with page citations.
"""

from app.chroma_client import query_by_topic, query_chunks
from app.llm import chat_completion, stream_completion

EXPLAIN_SYSTEM_PROMPT = """You are MedMentor AI, an expert medical tutor for MBBS students specialising in Medicine.

Your task is to explain medical topics in a clear, professional, exam-oriented manner using ONLY the provided textbook context.

## Output Format & Structure
- Write the explanation using proper structured paragraphs for definitions, general overviews, and concepts.
- Use point-wise bullet points for lists, clinical features, etiology/causes, pathophysiology mechanisms, investigations, management steps, or complications to make it easy to read, study, and memorize.
- Organize the content logically with clear markdown headings (e.g., `### Definition`, `### Clinical Features`, `### Management`) relevant to the topic/question. Do NOT force a rigid set of headers if there is no relevant information in the context for them.
- Ensure proper spacing between headings, paragraphs, and list items to keep the formatting clean and highly readable.

## Rules
- Cite page numbers at the end of each relevant statement as **(p. X)** based on the excerpt metadata.
- Highlight key exam points with **bold text**.
- Keep language clinical but understandable for a medical student.
- Do NOT invent or speculate. If the provided context does not contain information to answer the question or a specific aspect of it, simply state that the information is not available in the textbook excerpts.
- If the user asks a follow-up question, answer it directly and clearly within the topic's clinical context using a similar clean, paragraph and point-wise structure.

## Context
The following textbook excerpts are provided:
{context}
"""


def build_context(chunks: list[dict]) -> str:
    """Format retrieved chunks into LLM context string."""
    parts = []
    for i, chunk in enumerate(chunks, 1):
        meta = chunk["metadata"]
        page = meta.get("page_number", "?")
        section = meta.get("section_type", "General")
        topic = meta.get("topic", "")
        parts.append(
            f"[Excerpt {i} | Topic: {topic} | Section: {section} | Page: {page}]\n"
            f"{chunk['text']}\n"
        )
    return "\n---\n".join(parts)


async def explain_topic(
    topic_title: str,
    user_query: str,
    conversation_history: list[dict] = None,
    stream: bool = False
):
    """
    Generate a structured explanation for a medical topic.
    Returns full text or async generator if stream=True.
    """
    # Retrieve relevant chunks
    chunks = query_by_topic(topic_title, n_results=12)

    # If we have conversation history, also search based on the user query
    if user_query and user_query.lower() not in topic_title.lower():
        extra_chunks = query_chunks(f"{topic_title} {user_query}", n_results=5)
        # Merge, deduplicate by text
        seen = {c["text"] for c in chunks}
        for c in extra_chunks:
            if c["text"] not in seen:
                chunks.append(c)
                seen.add(c["text"])

    context = build_context(chunks[:15])  # cap at 15 chunks
    system_prompt = EXPLAIN_SYSTEM_PROMPT.format(context=context)

    # Build user message with history context
    if conversation_history and len(conversation_history) > 0:
        history_text = "\n".join([
            f"{'Student' if m['role'] == 'user' else 'MedMentor'}: {m['content']}"
            for m in conversation_history[-4:]  # last 4 turns
        ])
        user_message = (
            f"Previous conversation:\n{history_text}\n\n"
            f"Student's current question: {user_query}"
        )
    else:
        if user_query:
            user_message = f"Please explain {topic_title}. Specifically: {user_query}"
        else:
            user_message = f"Please provide a comprehensive explanation of {topic_title} for my MBBS exam preparation."

    if stream:
        return stream_completion(system_prompt, user_message)
    else:
        return await chat_completion(system_prompt, user_message)
