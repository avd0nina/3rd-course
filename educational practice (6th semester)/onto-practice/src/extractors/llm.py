"""Shared LLM client + JSON-output parser + key-rotation pool."""

from __future__ import annotations

import json
import logging
import os
import re
import threading

from openai import OpenAI

log = logging.getLogger(__name__)


class QuotaExhaustedError(RuntimeError):
    """Raised when every key in the pool has hit its daily free-tier quota."""


class KeyPool:
    """Round-robin pool of OpenRouter API keys with day-quota awareness.

    A key is rotated to the back of the pool the moment it returns
    `free-models-per-day` 429. The pool is global to the process; on restart
    every key gets a fresh chance.
    """

    def __init__(self, keys: list[str]) -> None:
        if not keys:
            raise RuntimeError(
                "No OpenRouter API keys configured. Set OPENROUTER_API_KEYS "
                "(comma-separated) or OPENROUTER_API_KEY in .env."
            )
        self._keys = list(keys)
        self._exhausted: set[str] = set()
        self._lock = threading.Lock()

    def active_key(self) -> str:
        """First non-exhausted key. Raises if pool is empty."""
        with self._lock:
            for k in self._keys:
                if k not in self._exhausted:
                    return k
            raise QuotaExhaustedError(
                f"All {len(self._keys)} OpenRouter keys hit free-models-per-day. "
                "Add credits at https://openrouter.ai/credits or wait for daily reset."
            )

    def mark_exhausted(self, key: str) -> None:
        with self._lock:
            if key in self._keys and key not in self._exhausted:
                self._exhausted.add(key)
                log.warning(
                    "key %s marked exhausted; %d/%d keys still active",
                    _mask(key),
                    len(self._keys) - len(self._exhausted),
                    len(self._keys),
                )

    def status(self) -> dict[str, int]:
        with self._lock:
            return {"total": len(self._keys), "exhausted": len(self._exhausted)}


_pool: KeyPool | None = None
_pool_lock = threading.Lock()


def _load_keys_from_env() -> list[str]:
    raw_multi = os.getenv("OPENROUTER_API_KEYS", "")
    raw_single = os.getenv("OPENROUTER_API_KEY", "")
    keys = [k.strip() for k in raw_multi.split(",") if k.strip()]
    if raw_single and raw_single not in keys:
        keys.insert(0, raw_single.strip())
    return keys


def get_pool() -> KeyPool:
    global _pool
    with _pool_lock:
        if _pool is None:
            _pool = KeyPool(_load_keys_from_env())
        return _pool


def reset_pool() -> None:
    """Force re-read of keys from env (for tests / config reload)."""
    global _pool
    with _pool_lock:
        _pool = None


def make_client(timeout: float = 90.0) -> OpenAI:
    """Build an OpenAI-compatible client with explicit per-phase timeouts.

    Plain `timeout=` keyword on OpenAI SDK is a soft limit and doesn't always
    cut requests where the server holds the connection open without sending
    bytes. We pass an explicit httpx.Timeout where read/write/pool are bounded
    independently — that one fires reliably on 'silent socket' hangs.
    """
    import httpx

    http_timeout = httpx.Timeout(
        timeout=timeout,
        connect=10.0,
        read=timeout,
        write=10.0,
        pool=5.0,
    )
    return OpenAI(
        api_key=get_pool().active_key(),
        base_url=os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1"),
        max_retries=0,
        timeout=http_timeout,
    )


def is_connection_error(exc: BaseException) -> bool:
    """Recognise network-level OpenRouter failures (timeout / drop / DNS)."""
    name = type(exc).__name__
    return name in ("APIConnectionError", "APITimeoutError", "ConnectionError")


def is_quota_exhausted_error(exc: BaseException) -> bool:
    """Per-key daily quota — switch to another key won't fix it on the same key."""
    msg = str(exc)
    return "free-models-per-day" in msg


def is_upstream_rate_limited(exc: BaseException) -> bool:
    """Per-minute / provider-side rate limit. Same model can succeed if we wait
    a few seconds; rotating the key does NOT help (it's the provider quota,
    not OpenRouter quota)."""
    msg = str(exc)
    if "free-models-per-day" in msg:
        return False  # quota, not transient rate-limit
    if "429" not in msg:
        return False
    return (
        "rate-limited upstream" in msg
        or "free-models-per-min" in msg
        or "Provider returned error" in msg
    )


def _mask(key: str) -> str:
    if len(key) < 12:
        return "****"
    return f"{key[:8]}...{key[-4:]}"


def parse_json_response(content: str) -> dict | None:
    """Parse LLM output into JSON, tolerating ```json fences and stray prose."""
    if not content:
        log.warning("LLM returned empty content")
        return None
    text = content.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    elif not text.startswith("{"):
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            text = m.group(0)
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        log.warning("LLM returned non-JSON (%s). First 200 chars: %.200s", e, content)
        return None
