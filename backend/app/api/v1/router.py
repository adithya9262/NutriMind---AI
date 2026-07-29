from fastapi import APIRouter

from .ai_coach import router as ai_coach_router
from .auth import router as auth_router
from .body_weights import router as body_weights_router
from .food_recognition import router as food_recognition_router
from .food_search import router as food_search_router
from .goals import router as goals_router
from .health import router as health_router
from .nutrition_logs import router as nutrition_logs_router
from .nutrition_profile import router as nutrition_profile_router
from .reports import router as reports_router
from .search import router as search_router
from .settings import router as settings_router
from .tasks import router as tasks_router

router = APIRouter()
router.include_router(ai_coach_router)
router.include_router(auth_router)
router.include_router(body_weights_router)
router.include_router(food_recognition_router)
router.include_router(food_search_router)
router.include_router(goals_router)
router.include_router(health_router)
router.include_router(nutrition_logs_router)
router.include_router(nutrition_profile_router)
router.include_router(search_router)
router.include_router(settings_router)
router.include_router(tasks_router)
router.include_router(reports_router)
