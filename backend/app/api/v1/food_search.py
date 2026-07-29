from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.authentication import get_current_user
from app.core.config import Settings
from app.core.middleware import get_request_id
from app.db.dependencies import get_db_session
from app.models.user import User
from app.services.food_search import FoodSearchService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/food-search", tags=["Food Search"])


@router.get("/search")
async def search_foods(
    request: Request,
    query: str = Query(..., min_length=1, max_length=200),
    max_results: int = Query(25, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    request_id = get_request_id() or "-"
    settings = Settings()
    service = FoodSearchService(usda_api_key=settings.USDA_API_KEY)
    try:
        result = await service.search(query, max_results)
        return {
            "success": True,
            "message": "Food search completed.",
            "data": {
                "query": result.query,
                "total_results": result.total_results,
                "foods": [
                    {
                        "fdc_id": f.fdc_id,
                        "food_name": f.food_name,
                        "brand_name": f.brand_name,
                        "calories_kcal": str(f.calories_kcal),
                        "protein_g": str(f.protein_g),
                        "carbohydrate_g": str(f.carbohydrate_g),
                        "fat_g": str(f.fat_g),
                        "fiber_g": str(f.fiber_g),
                        "sugar_g": str(f.sugar_g),
                        "serving_size_g": str(f.serving_size_g) if f.serving_size_g else None,
                        "serving_description": f.serving_description,
                        "source": f.source,
                    }
                    for f in result.foods
                ],
            },
        }
    except Exception as exc:
        logger.exception("Food search failed")
        return JSONResponse(
            status_code=502,
            content={
                "success": False,
                "error": {
                    "code": "FOOD_SEARCH_FAILED",
                    "message": f"Food search failed: {exc}",
                    "request_id": request_id,
                },
            },
        )
