from __future__ import annotations

import asyncio

from httpx import AsyncClient


class TaskYieldingASGIClient:
    """Yield once before awaiting an in-process request and bound transport stalls."""

    def __init__(self, async_client: AsyncClient, timeout: float = 15):
        self.async_client = async_client
        self.timeout = timeout

    async def request(self, method: str, url: str, **kwargs):
        request = asyncio.create_task(self.async_client.request(method, url, **kwargs))
        await asyncio.sleep(0.1)
        return await asyncio.wait_for(request, timeout=self.timeout)

    async def get(self, url: str, **kwargs):
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs):
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs):
        return await self.request("PUT", url, **kwargs)

    async def patch(self, url: str, **kwargs):
        return await self.request("PATCH", url, **kwargs)

    async def delete(self, url: str, **kwargs):
        return await self.request("DELETE", url, **kwargs)

    async def options(self, url: str, **kwargs):
        return await self.request("OPTIONS", url, **kwargs)
