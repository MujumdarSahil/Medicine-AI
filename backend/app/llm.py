"""
MedMentor AI — LLM Provider Wrapper
Groq (primary) → Google Gemini Flash (fallback)
"""

import os
import asyncio
from typing import AsyncGenerator
from groq import AsyncGroq
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"
GEMINI_MODEL = "gemini-1.5-flash"

_groq_client: AsyncGroq | None = None


def get_groq_client() -> AsyncGroq:
    global _groq_client
    if _groq_client is None:
        _groq_client = AsyncGroq(api_key=GROQ_API_KEY)
    return _groq_client


def _init_gemini():
    genai.configure(api_key=GEMINI_API_KEY)


async def chat_completion(
    system_prompt: str,
    user_message: str,
    temperature: float = 0.4,
    max_tokens: int = 2048
) -> str:
    """Single-turn chat completion with Groq → Gemini fallback."""
    # Try Groq first
    if GROQ_API_KEY:
        try:
            client = get_groq_client()
            response = await client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[!] Groq error: {e} — falling back to Gemini")

    # Fallback: Gemini Flash
    if GEMINI_API_KEY:
        try:
            _init_gemini()
            model = genai.GenerativeModel(
                model_name=GEMINI_MODEL,
                system_instruction=system_prompt
            )
            response = await asyncio.to_thread(
                model.generate_content,
                user_message,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens
                )
            )
            return response.text
        except Exception as e:
            print(f"[!] Gemini error: {e}")
            raise

    raise RuntimeError("No LLM provider available. Set GROQ_API_KEY or GEMINI_API_KEY in .env")


async def stream_completion(
    system_prompt: str,
    user_message: str,
    temperature: float = 0.4,
    max_tokens: int = 2048
) -> AsyncGenerator[str, None]:
    """Streaming chat completion with Groq → Gemini fallback."""
    # Try Groq streaming
    if GROQ_API_KEY:
        try:
            client = get_groq_client()
            stream = await client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
            return
        except Exception as e:
            print(f"[!] Groq streaming error: {e} — falling back to Gemini")

    # Fallback: Gemini (non-streaming, then yield full text)
    if GEMINI_API_KEY:
        try:
            full = await chat_completion(system_prompt, user_message, temperature, max_tokens)
            # Simulate streaming by yielding words
            for word in full.split(" "):
                yield word + " "
                await asyncio.sleep(0.01)
            return
        except Exception as e:
            print(f"[!] Gemini fallback error: {e}")
            raise

    raise RuntimeError("No LLM provider available.")
