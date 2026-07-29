from __future__ import annotations

import base64
import json
import logging
import re
from dataclasses import dataclass
from decimal import Decimal

import httpx

from app.services.food_search import FoodSearchService


@dataclass(frozen=True, slots=True)
class DetectedFood:
    food_name: str
    calories_kcal: Decimal
    protein_g: Decimal
    carbohydrate_g: Decimal
    fat_g: Decimal
    serving_size_g: Decimal
    ingredients: tuple[str, ...]
    confidence_score: Decimal


@dataclass(frozen=True, slots=True)
class RecognitionResult:
    foods: tuple[DetectedFood, ...]
    raw_response: str


FOOD_ANALYSIS_PROMPT = (
    "Analyze this food image. Identify ALL visible food items. "
    "For EACH food item, return a JSON object with these EXACT fields:\n"
    '  - food_name (string): descriptive name like "Roasted Chicken" or "Apple"\n'
    "  - calories_kcal (number): estimated calories\n"
    "  - protein_g (number): estimated protein in grams\n"
    "  - carbohydrate_g (number): estimated carbs in grams\n"
    "  - fat_g (number): estimated fat in grams\n"
    "  - serving_size_g (number): estimated serving size in grams\n"
    "  - ingredients (array of strings): main ingredients\n"
    "  - confidence_score (number 0-1): your confidence in this identification\n\n"
    "Return ONLY a raw JSON array. NO markdown, NO code fences, NO extra text.\n"
    "Examples:\n"
    '[{"food_name": "Roasted Chicken", "calories_kcal": 250, ...}]\n\n'
    "If you see food, always return it with a reasonable confidence score.\n"
    "Only return an empty array [] if there is genuinely no food visible."
)


class FoodRecognitionService:
    def __init__(self, gemini_api_key: str = "", groq_api_key: str = "", usda_api_key: str = "", gemini_model: str = "gemini-2.0-flash") -> None:
        self._gemini_key = gemini_api_key
        self._groq_key = groq_api_key
        self._gemini_model = gemini_model
        self._food_search = FoodSearchService(usda_api_key=usda_api_key) if usda_api_key else None

    @staticmethod
    def _detect_mime_type(filename: str, image_bytes: bytes) -> str:
        ext = (filename or "food.jpg").lower()
        if ext.endswith(".png"):
            return "image/png"
        if ext.endswith(".webp"):
            return "image/webp"
        if ext.endswith(".heic") or ext.endswith(".heif"):
            return "image/heic"
        if ext.endswith(".gif"):
            return "image/gif"
        if image_bytes[:4] == b"\x89PNG":
            return "image/png"
        if image_bytes[:2] in (b"\xff\xd8",):
            return "image/jpeg"
        if image_bytes[:4] == b"RIFF":
            return "image/webp"
        return "image/jpeg"

    async def analyze_image(self, image_bytes: bytes, filename: str = "food.jpg") -> RecognitionResult:
        mime = self._detect_mime_type(filename, image_bytes)

        errors: list[str] = []
        if self._gemini_key:
            try:
                return await self._analyze_gemini(image_bytes, mime)
            except Exception as e:
                errors.append(f"Gemini: {e}")
        if self._groq_key:
            try:
                return await self._analyze_groq(image_bytes, mime)
            except Exception as e:
                errors.append(f"Groq: {e}")

        # Last-resort fallback: extract food keywords from filename and search food database
        if self._food_search:
            try:
                return await self._fallback_from_filename(filename)
            except Exception as e:
                errors.append(f"Fallback: {e}")

        if errors:
            raise RuntimeError("All AI providers failed: " + "; ".join(errors))
        raise RuntimeError("No AI provider configured. Set GEMINI_API_KEY or GROQ_API_KEY.")

    async def _analyze_gemini(self, image_bytes: bytes, mime: str) -> RecognitionResult:
        image_b64 = base64.b64encode(image_bytes).decode()

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self._gemini_model}:generateContent?key={self._gemini_key}"
        payload = {
            "contents": [{
                "parts": [
                    {"text": FOOD_ANALYSIS_PROMPT},
                    {"inline_data": {"mime_type": mime, "data": image_b64}},
                ]
            }]
        }

        logger = logging.getLogger(__name__)
        logger.info("Gemini vision request — model=%s, mime=%s, image_size=%d, prompt_len=%d",
                     self._gemini_model, mime, len(image_bytes), len(FOOD_ANALYSIS_PROMPT))

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, json=payload)
            logger.info("Gemini response — status=%d, body=%s", resp.status_code, resp.text[:2000])
            resp.raise_for_status()
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            logger.info("Gemini parsed text — len=%d, preview=%s", len(text), text[:300])
            result = self._parse_food_json(text)
            logger.info("Gemini final result — foods=%d", len(result.foods))
            return result

    async def _analyze_groq(self, image_bytes: bytes, mime: str) -> RecognitionResult:
        image_b64 = base64.b64encode(image_bytes).decode()
        data_url = f"data:{mime};base64,{image_b64}"

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self._groq_key}"},
                json={
                    "model": "llama-3.2-90b-vision-preview",
                    "messages": [{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": FOOD_ANALYSIS_PROMPT},
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ],
                    }],
                    "max_tokens": 1024,
                    "temperature": 0.1,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["choices"][0]["message"]["content"]
            return self._parse_food_json(text)

    async def _fallback_from_filename(self, filename: str) -> RecognitionResult:
        # Extract food keywords from filename
        name = (filename or "food").rsplit(".", 1)[0]
        name = re.sub(r"[_-]", " ", name)
        name = re.sub(r"\s+", " ", name).strip()
        if not name or name.lower() in ("food", "image", "photo", "img", "pic"):
            raise RuntimeError("Could not infer food from filename")

        result = await self._food_search.search(name, max_results=5)
        if not result.foods:
            raise RuntimeError(f"No food found for '{name}' in food database")

        foods = []
        f = result.foods[0]
        foods.append(DetectedFood(
            food_name=f.food_name,
            calories_kcal=f.calories_kcal,
            protein_g=f.protein_g,
            carbohydrate_g=f.carbohydrate_g,
            fat_g=f.fat_g,
            serving_size_g=f.serving_size_g or Decimal("100"),
            ingredients=(),
            confidence_score=Decimal("0.5"),
        ))
        return RecognitionResult(foods=tuple(foods), raw_response=f"[fallback] Matched '{name}' → '{f.food_name}' from {f.source}")

    def _parse_food_json(self, text: str) -> RecognitionResult:
        import re

        cleaned = text.strip()

        # Strip markdown code fences
        cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r'\s*```$', '', cleaned, flags=re.MULTILINE)
        cleaned = cleaned.strip()

        # Find the first [ and last ] to extract the JSON array
        first_bracket = cleaned.find('[')
        last_bracket = cleaned.rfind(']')
        if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
            json_str = cleaned[first_bracket:last_bracket + 1]
        else:
            json_str = "[]"

        def _try_parse(raw: str) -> list:
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                pass
            # Try stripping trailing commas before ] and }
            try:
                fixed = re.sub(r',\s*([\]}])', r'\1', raw)
                return json.loads(fixed)
            except json.JSONDecodeError:
                pass
            return []

        foods_data = _try_parse(json_str)

        if not isinstance(foods_data, list):
            foods_data = []

        foods = []
        for fd in foods_data[:10]:
            try:
                foods.append(DetectedFood(
                    food_name=str(fd.get("food_name", "Unknown")),
                    calories_kcal=Decimal(str(fd.get("calories_kcal", 0))),
                    protein_g=Decimal(str(fd.get("protein_g", 0))),
                    carbohydrate_g=Decimal(str(fd.get("carbohydrate_g", 0))),
                    fat_g=Decimal(str(fd.get("fat_g", 0))),
                    serving_size_g=Decimal(str(fd.get("serving_size_g", 100))),
                    ingredients=tuple(str(i) for i in fd.get("ingredients", [])),
                    confidence_score=Decimal(str(fd.get("confidence_score", 0))),
                ))
            except (ValueError, TypeError):
                continue

        return RecognitionResult(foods=tuple(foods), raw_response=text)

    def _mock_analysis(self) -> RecognitionResult:  # pragma: no cover
        return RecognitionResult(foods=(), raw_response="")
