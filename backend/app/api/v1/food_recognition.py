from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, Request, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.authentication import get_current_user
from app.core.config import Settings
from app.core.middleware import get_request_id
from app.db.dependencies import get_db_session
from app.models.user import User
from app.services.food_recognition import FoodRecognitionService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/food-recognition", tags=["Food Recognition"])

MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}


@router.post("/analyze")
async def analyze_food_image(
    request: Request,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    request_id = get_request_id() or "-"

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "error": {
                    "code": "INVALID_FILE_TYPE",
                    "message": "File must be JPEG, PNG, WebP, or HEIC.",
                    "request_id": request_id,
                },
            },
        )

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={
                "success": False,
                "error": {
                    "code": "FILE_TOO_LARGE",
                    "message": "File must be under 10MB.",
                    "request_id": request_id,
                },
            },
        )

    settings = Settings()
    service = FoodRecognitionService(gemini_api_key=settings.GEMINI_API_KEY, groq_api_key=settings.GROQ_API_KEY, usda_api_key=settings.USDA_API_KEY, gemini_model=settings.GEMINI_MODEL)
    try:
        result = await service.analyze_image(contents, file.filename or "food.jpg")
        if not result.foods:
            return {
                "success": True,
                "message": "No food items detected in the image.",
                "data": {
                    "foods": [],
                    "raw_response": result.raw_response,
                },
            }
        return {
            "success": True,
            "message": "Food analysis completed.",
            "data": {
                "foods": [
                    {
                        "food_name": f.food_name,
                        "calories_kcal": str(f.calories_kcal),
                        "protein_g": str(f.protein_g),
                        "carbohydrate_g": str(f.carbohydrate_g),
                        "fat_g": str(f.fat_g),
                        "serving_size_g": str(f.serving_size_g),
                        "ingredients": list(f.ingredients),
                        "confidence_score": str(f.confidence_score),
                    }
                    for f in result.foods
                ],
                "raw_response": result.raw_response,
            },
        }
    except Exception as exc:
        logger.exception("Food recognition failed")
        return {
            "success": False,
            "message": f"Food analysis failed: {exc}",
            "data": {
                "foods": [],
                "raw_response": str(exc),
            },
        }
