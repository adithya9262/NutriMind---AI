import pytest
from unittest.mock import patch, MagicMock

from httpx import Response
from app.services.ai_coach import AICoachService

@pytest.fixture
def mock_httpx_post():
    with patch("httpx.AsyncClient.post") as mock_post:
        yield mock_post


@pytest.mark.asyncio
async def test_ai_coach_gemini_request_format_and_headers(mock_httpx_post):
    # Setup mock response
    mock_resp = MagicMock(spec=Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [{
            "content": {
                "parts": [{
                    "text": "Hello, this is your coach."
                }]
            }
        }]
    }
    mock_httpx_post.return_value = mock_resp
    
    service = AICoachService(gemini_api_key="TEST_COACH_KEY", gemini_model="gemini-2.0-flash")
    
    # Test chat
    result = await service._chat_gemini("Hi there")
    
    # Verify request payload and headers
    mock_httpx_post.assert_called_once()
    args, kwargs = mock_httpx_post.call_args
    
    url = args[0]
    headers = kwargs.get("headers", {})
    payload = kwargs.get("json", {})
    
    # API key is not in URL
    assert "key=" not in url
    assert url == "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    
    # API key is in headers
    assert headers.get("x-goog-api-key") == "TEST_COACH_KEY"
    
    assert "contents" in payload
    assert result == "Hello, this is your coach."


@pytest.mark.asyncio
async def test_ai_coach_gemini_stream_headers():
    with patch("httpx.AsyncClient.stream") as mock_stream:
        # We don't need a full stream implementation here, just check the URL and headers
        mock_ctx = MagicMock()
        mock_stream.return_value = mock_ctx
        mock_resp = MagicMock()
        mock_ctx.__aenter__.return_value = mock_resp
        
        # Make the aiters yield empty so it returns immediately
        async def mock_aiter_lines():
            if False: yield ""
        mock_resp.aiter_lines.return_value = mock_aiter_lines()
        
        service = AICoachService(gemini_api_key="TEST_STREAM_KEY", gemini_model="gemini-2.0-flash")
        
        async for _ in service._stream_gemini("Hello"):
            pass
            
        mock_stream.assert_called_once()
        args, kwargs = mock_stream.call_args
        
        url = args[1] # url is the 2nd arg for stream("POST", url, ...)
        headers = kwargs.get("headers", {})
        
        assert "key=" not in url
        assert headers.get("x-goog-api-key") == "TEST_STREAM_KEY"


@pytest.mark.asyncio
async def test_ai_coach_generate_embedding_headers(mock_httpx_post):
    mock_resp = MagicMock(spec=Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"embedding": {"values": [0.1, 0.2]}}
    mock_httpx_post.return_value = mock_resp
    
    service = AICoachService(gemini_api_key="TEST_EMBED_KEY")
    result = await service.generate_embedding("some text")
    
    mock_httpx_post.assert_called_once()
    args, kwargs = mock_httpx_post.call_args
    
    url = args[0]
    headers = kwargs.get("headers", {})
    
    assert "key=" not in url
    assert url == "https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent"
    assert headers.get("x-goog-api-key") == "TEST_EMBED_KEY"
    assert result == [0.1, 0.2]
