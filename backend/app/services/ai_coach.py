from __future__ import annotations

import json
import time
from collections.abc import AsyncGenerator
from functools import lru_cache

import httpx

SYSTEM_PROMPT = """You are NutriCoach AI, a professional nutrition and fitness coach. You help users with:
- Personalized nutrition advice based on their goals
- Meal planning and healthy eating suggestions
- Workout recommendations tailored to their fitness level
- Weight management strategies
- Healthy food alternatives
- Understanding nutrition labels and macros
- Hydration and sleep optimization

Be supportive, evidence-based, and practical. Keep responses concise but informative. 
NEVER give medical advice - always recommend consulting a doctor for medical concerns.

CRITICAL: You must use structured JSON UI Cards when applicable (e.g. for macros, meals, lists). Output standard markdown text, and when a card makes sense, output it EXACTLY like this inside a markdown json block:
```json
{
  "type": "NutritionCard", // or MealSuggestionCard, ShoppingListCard, MacroProgressCard, HydrationCard, MicronutrientCard
  "title": "Card Title",
  "current_value": "String value",
  "target": "String target",
  "progress_percent": 75,
  "recommendations": ["Tip 1", "Tip 2"]
}
```

CRITICAL REQUIREMENT: At the VERY END of your response, you MUST provide exactly 3 contextual follow-up questions that the user might want to ask next. You MUST format this as a JSON code block with the exact type "FollowUpQuestions". Example:
```json
{
  "type": "FollowUpQuestions",
  "questions": ["How much water should I drink?", "What are good sources of protein?", "Can I have a cheat day?"]
}
```
Failure to include this exact JSON block at the end of every message will break the application.
"""

class AICoachService:
    def __init__(self, gemini_api_key: str = "", groq_api_key: str = "", gemini_model: str = "gemini-2.0-flash") -> None:
        self._gemini_key = gemini_api_key
        self._groq_key = groq_api_key
        self._gemini_model = gemini_model
        self._health = {
            "gemini": {"failures": 0, "next_retry": 0.0},
            "groq": {"failures": 0, "next_retry": 0.0}
        }

    def _is_healthy(self, provider: str) -> bool:
        return time.time() >= self._health[provider]["next_retry"]

    def _record_success(self, provider: str) -> None:
        self._health[provider]["failures"] = 0
        self._health[provider]["next_retry"] = 0.0

    def _record_failure(self, provider: str) -> None:
        self._health[provider]["failures"] += 1
        cooldown = min(300, 10 * self._health[provider]["failures"])
        self._health[provider]["next_retry"] = time.time() + cooldown

    def _build_system_prompt(self, context: str | None) -> str:
        if context:
            return f"{SYSTEM_PROMPT}\n\nUSER CONTEXT:\n{context}"
        return SYSTEM_PROMPT

    async def chat(self, message: str, history: list[dict] | None = None, context: str | None = None) -> str:
        if self._gemini_key and self._is_healthy("gemini"):
            try:
                res = await self._chat_gemini(message, history, context)
                self._record_success("gemini")
                return res
            except Exception:
                self._record_failure("gemini")

        if self._groq_key and self._is_healthy("groq"):
            try:
                res = await self._chat_groq(message, history, context)
                self._record_success("groq")
                return res
            except Exception:
                self._record_failure("groq")

        # Force retry gemini if both failed or on cooldown
        if self._gemini_key:
            try:
                res = await self._chat_gemini(message, history, context)
                self._record_success("gemini")
                return res
            except Exception:
                self._record_failure("gemini")

        raise RuntimeError("No AI provider available or all failed.")

    async def chat_stream(self, message: str, history: list[dict] | None = None, context: str | None = None) -> AsyncGenerator[str, None]:
        if self._gemini_key and self._is_healthy("gemini"):
            try:
                async for chunk in self._stream_gemini(message, history, context):
                    yield chunk
                self._record_success("gemini")
                return
            except Exception:
                self._record_failure("gemini")

        if self._groq_key and self._is_healthy("groq"):
            try:
                async for chunk in self._stream_groq(message, history, context):
                    yield chunk
                self._record_success("groq")
                return
            except Exception:
                self._record_failure("groq")

        if self._gemini_key:
            try:
                async for chunk in self._stream_gemini(message, history, context):
                    yield chunk
                self._record_success("gemini")
                return
            except Exception:
                self._record_failure("gemini")

        raise RuntimeError("No AI provider available or all failed.")

    async def _chat_gemini(self, message: str, history: list[dict] | None = None, context: str | None = None) -> str:
        system_prompt = self._build_system_prompt(context)
        contents = []
        if history:
            for h in history[-20:]:
                role = "model" if h.get("role") == "assistant" else "user"
                contents.append({"role": role, "parts": [{"text": h["content"]}]})
        contents.append({"role": "user", "parts": [{"text": f"System Context (DO NOT REPLY DIRECTLY TO THIS, ONLY USE IT IF RELEVANT):\n{system_prompt}\n\nUser: {message}"}]})

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{self._gemini_model}:generateContent?key={self._gemini_key}",
                json={"contents": contents},
            )
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    async def _stream_gemini(self, message: str, history: list[dict] | None = None, context: str | None = None) -> AsyncGenerator[str, None]:
        system_prompt = self._build_system_prompt(context)
        contents = []
        if history:
            for h in history[-20:]:
                role = "model" if h.get("role") == "assistant" else "user"
                contents.append({"role": role, "parts": [{"text": h["content"]}]})
        contents.append({"role": "user", "parts": [{"text": f"System Context (DO NOT REPLY DIRECTLY TO THIS, ONLY USE IT IF RELEVANT):\n{system_prompt}\n\nUser: {message}"}]})

        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream(
                "POST",
                f"https://generativelanguage.googleapis.com/v1beta/models/{self._gemini_model}:streamGenerateContent?alt=sse&key={self._gemini_key}",
                json={"contents": contents},
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        try:
                            chunk = json.loads(data_str)
                            text = chunk.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                            if text:
                                yield text
                        except json.JSONDecodeError:
                            continue

    async def _chat_groq(self, message: str, history: list[dict] | None = None, context: str | None = None) -> str:
        system_prompt = self._build_system_prompt(context)
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history[-20:])
        messages.append({"role": "user", "content": message})

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self._groq_key}"},
                json={"model": "llama-3.3-70b-versatile", "messages": messages, "max_tokens": 1024, "temperature": 0.7},
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def _stream_groq(self, message: str, history: list[dict] | None = None, context: str | None = None) -> AsyncGenerator[str, None]:
        system_prompt = self._build_system_prompt(context)
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history[-20:])
        messages.append({"role": "user", "content": message})

        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream(
                "POST",
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self._groq_key}"},
                json={"model": "llama-3.3-70b-versatile", "messages": messages, "max_tokens": 1024, "temperature": 0.7, "stream": True},
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if delta:
                                yield delta
                        except json.JSONDecodeError:
                            continue

    def _mock_response(self, message: str) -> str:  # pragma: no cover
        return ""

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding using Gemini text-embedding-004."""
        if not self._gemini_key:
            return []

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={self._gemini_key}",
                json={
                    "model": "models/text-embedding-004",
                    "content": {"parts": [{"text": text}]},
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("embedding", {}).get("values", [])
            return []


@lru_cache(maxsize=1)
def _make_ai_coach_service(gemini_api_key: str, groq_api_key: str, gemini_model: str) -> AICoachService:
    """Internal cached factory — keyed on both API keys so a key rotation forces a new instance."""
    return AICoachService(gemini_api_key=gemini_api_key, groq_api_key=groq_api_key, gemini_model=gemini_model)


def get_ai_coach_service() -> AICoachService:
    """Return the module-level AICoachService singleton.

    The singleton preserves circuit-breaker failure counts and cooldown
    timestamps across requests, so provider health state survives between calls.
    Settings are read once on first call via the app.core.config singleton.
    """
    from app.core.config import get_settings  # local import to avoid circular at module level

    settings = get_settings()
    return _make_ai_coach_service(
        gemini_api_key=settings.GEMINI_API_KEY,
        groq_api_key=settings.GROQ_API_KEY,
        gemini_model=settings.GEMINI_MODEL,
    )
