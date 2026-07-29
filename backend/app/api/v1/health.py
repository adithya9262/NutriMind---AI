from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthData(BaseModel):
    status: str


class HealthResponse(BaseModel):
    success: bool
    message: str
    data: HealthData


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(
        success=True,
        message="NutriMind API is healthy",
        data=HealthData(status="healthy"),
    )
