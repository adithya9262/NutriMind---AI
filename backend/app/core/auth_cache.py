"""
Simple in-process cache for Supabase token verification results.

Avoids repeated external HTTP calls to the Supabase auth API for the same
token within a short TTL window, which was the primary cause of request
timeouts across all authenticated endpoints.
"""
from __future__ import annotations

import time
from threading import Lock

# Cache entry: (user_payload: dict, expires_at: float)
_cache: dict[str, tuple[dict, float]] = {}
_lock = Lock()

# How long to cache a successful Supabase verification (seconds)
_TTL = 120.0
# Maximum entries before we purge old ones
_MAX_SIZE = 2048


def _evict_expired() -> None:
    """Remove expired entries. Must be called with _lock held."""
    now = time.monotonic()
    expired = [k for k, (_, exp) in _cache.items() if exp <= now]
    for k in expired:
        del _cache[k]
    # If still too large, remove oldest entries
    if len(_cache) > _MAX_SIZE:
        sorted_keys = sorted(_cache, key=lambda k: _cache[k][1])
        for k in sorted_keys[: len(_cache) - _MAX_SIZE]:
            del _cache[k]


def get_cached_payload(token: str) -> dict | None:
    """Return cached payload for *token* if present and not expired."""
    with _lock:
        entry = _cache.get(token)
        if entry is None:
            return None
        payload, expires_at = entry
        if time.monotonic() > expires_at:
            del _cache[token]
            return None
        return payload


def set_cached_payload(token: str, payload: dict) -> None:
    """Store *payload* in cache for *token*."""
    with _lock:
        _evict_expired()
        _cache[token] = (payload, time.monotonic() + _TTL)


def invalidate(token: str) -> None:
    """Remove *token* from the cache (e.g. on 401)."""
    with _lock:
        _cache.pop(token, None)
