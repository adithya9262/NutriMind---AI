import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient, HTTPStatusError, Request, Response

from app.api.dependencies.authentication import get_current_user
from app.core.config import Settings
from app.db.dependencies import get_db_session
from app.main import create_app
from app.models.user import User
from app.services.food_recognition import FoodRecognitionService


class TaskYieldingASGIClient:
    def __init__(self, async_client: AsyncClient):
        self.async_client = async_client

    async def post(self, url: str, **kwargs):
        request = asyncio.create_task(self.async_client.post(url, **kwargs))
        await asyncio.sleep(0.1)
        return await asyncio.wait_for(request, timeout=15)


@pytest_asyncio.fixture
async def client():
    app = create_app(
        settings=Settings(
            APP_ENV="test",
            DEBUG=False,
            DATABASE_URL="",
            JWT_SECRET_KEY="test-secret-key-that-is-at-least-32-characters!!",
        )
    )

    async def override_current_user():
        return User(id=uuid.uuid4(), email="test@example.com")

    async def override_db_session():
        yield MagicMock()

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db_session] = override_db_session
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://test",
        ) as async_client:
            yield TaskYieldingASGIClient(async_client)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def mock_httpx_post():
    with patch("httpx.AsyncClient.post") as mock_post:
        yield mock_post


@pytest.mark.asyncio
async def test_gemini_request_format_and_headers(mock_httpx_post):
    # Setup mock response
    mock_resp = MagicMock(spec=Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [{
            "content": {
                "parts": [{
                    "text": (
                        '[{"food_name": "Apple", "calories_kcal": 95, "protein_g": 0.5, '
                        '"carbohydrate_g": 25, "fat_g": 0.3, "serving_size_g": 182, '
                        '"ingredients": ["Apple"], "confidence_score": 0.99}]'
                    )
                }]
            }
        }]
    }
    mock_httpx_post.return_value = mock_resp

    service = FoodRecognitionService(gemini_api_key="TEST_API_KEY", gemini_model="gemini-3.8-flash")

    # Test valid image
    result = await service.analyze_image(b"fake_image_data", "apple.jpg")

    # Verify request payload and headers
    mock_httpx_post.assert_called_once()
    args, kwargs = mock_httpx_post.call_args

    url = args[0]
    headers = kwargs.get("headers", {})
    payload = kwargs.get("json", {})

    # API key is not in URL
    assert "key=" not in url
    assert url == "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent"

    # API key is in headers
    assert headers.get("x-goog-api-key") == "TEST_API_KEY"

    # Payload is valid
    assert "contents" in payload
    assert "generationConfig" in payload
    assert payload["generationConfig"] == {"responseMimeType": "application/json"}

    assert "inline_data" in payload["contents"][0]["parts"][1]

    # Response parsed correctly
    assert len(result.foods) == 1
    assert result.foods[0].food_name == "Apple"


@pytest.mark.asyncio
async def test_fallback_rejects_generic_filenames():
    service = FoodRecognitionService(usda_api_key="MOCK")
    result = await service.analyze_image(b"data", "photo.jpg")
    assert len(result.foods) == 0
    assert "generic filename" in result.raw_response


async def test_provider_errors_are_sanitized_in_api(client):
    with patch(
        "app.services.food_recognition.FoodRecognitionService.analyze_image",
        new_callable=AsyncMock,
    ) as mock_analyze:
        # Simulate a 503 error from the provider
        req = Request(
            "POST",
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key=LEAKED_KEY",
        )
        resp = Response(503, request=req)
        # HTTPStatusError string representation includes the URL
        mock_analyze.side_effect = HTTPStatusError(
            "503 Service Unavailable", request=req, response=resp
        )

        response = await client.post(
            "/api/v1/food-recognition/analyze",
            files={"file": ("apple.jpg", b"fake_image_data", "image/jpeg")}
        )

        assert response.status_code == 503
        data = response.json()
        assert data["success"] is False
        assert "Service unavailable" in data["data"]["raw_response"]
        assert "Food analysis service is temporarily unavailable" in data["message"]

        # Ensure API key does not appear anywhere in the response
        assert "LEAKED_KEY" not in response.text
