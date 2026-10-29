from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.authentication import get_current_user
from app.core.config import Settings
from app.db.dependencies import get_db_session
from app.models.nutrition_log import NutritionLog
from app.models.task import Task
from app.models.user import User
from app.services.food_search import FoodSearchService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["Search"])


@router.get("")
async def global_search(
    request: Request,
    q: str = Query(..., min_length=1, max_length=200),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    query = f"%{q}%"
    results = {"foods": [], "tasks": []}

    # 1. Search personal nutrition logs
    try:
        stmt = select(NutritionLog).where(
            NutritionLog.user_id == current_user.id,
            NutritionLog.food_name.ilike(query),
        ).limit(10)
        logs_result = await session.execute(stmt)
        for log in logs_result.scalars().all():
            results["foods"].append({
                "id": str(log.id),
                "food_name": log.food_name,
                "meal_type": log.meal_type.value,
                "logged_date": log.logged_date.isoformat(),
                "calories_kcal": str(log.calories_kcal),
            })
    except Exception:
        logger.exception("Personal food log search failed")

    # 2. Search external nutrition database (USDA/OpenFoodFacts) for food suggestions
    try:
        settings = Settings()
        food_search_service = FoodSearchService(usda_api_key=settings.USDA_API_KEY)
        food_search_result = await food_search_service.search(q, max_results=10)
        for food in food_search_result.foods:
            # Add source indicator to distinguish external suggestions from personal logs
            results["foods"].append({
                "id": f"ext-{food.fdc_id}",
                "food_name": food.food_name,
                "meal_type": None,  # Not a logged meal
                "logged_date": None,
                "calories_kcal": str(food.calories_kcal),
                "source": food.source,  # "usda" or "open_food_facts"
                "is_suggestion": True,
            })
    except Exception:
        logger.exception("External nutrition database search failed")

    # 3. Search tasks
    try:
        stmt = select(Task).where(
            Task.user_id == current_user.id,
            or_(
                Task.title.ilike(query),
                Task.description.ilike(query),
            ),
        ).limit(10)
        tasks_result = await session.execute(stmt)
        for task in tasks_result.scalars().all():
            results["tasks"].append({
                "id": str(task.id),
                "task_id": str(task.task_id),
                "title": task.title,
                "status": task.status.value,
                "due_date": task.due_date.isoformat() if task.due_date else None,
            })
    except Exception:
        logger.exception("Task search failed")

    return {
        "success": True,
        "message": "Search completed.",
        "data": results,
    }
