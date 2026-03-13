"""OpenRouter API client for LLM completions."""

from __future__ import annotations

import os
from typing import Any

import httpx

from .errors import OpenRouterError


OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


def chat_completion(
    model: str,
    messages: list[dict[str, str]],
    *,
    api_key: str | None = None,
    site_url: str | None = None,
    site_name: str | None = None,
    api_url: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    timeout: float = 120.0,
) -> str:
    """Send a chat completion request to OpenRouter.

    Args:
        model: OpenRouter model ID (e.g. "openai/gpt-4o-mini").
        messages: List of message dicts with "role" and "content".
        api_key: OpenRouter API key. If None, reads from OPENROUTER_API_KEY env.
        site_url: Optional site URL for OpenRouter rankings.
        site_name: Optional site name for OpenRouter rankings.
        timeout: Request timeout in seconds.

    Returns:
        The assistant's response content as a string.

    Raises:
        OpenRouterError: If the API request fails.
    """

    api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise OpenRouterError("OPENROUTER_API_KEY environment variable is not set.")

    headers: dict[str, str] = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    if site_url:
        headers["HTTP-Referer"] = site_url
    if site_name:
        headers["X-Title"] = site_name

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
    }

    if temperature is not None:
        payload["temperature"] = temperature
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                api_url or OPENROUTER_API_URL, headers=headers, json=payload
            )
            response.raise_for_status()
    except httpx.TimeoutException as exc:
        raise OpenRouterError(f"OpenRouter API request timed out: {exc}") from exc
    except httpx.HTTPStatusError as exc:
        raise OpenRouterError(
            f"OpenRouter API error ({exc.response.status_code}): {exc.response.text}"
        ) from exc
    except httpx.RequestError as exc:
        raise OpenRouterError(f"OpenRouter API request failed: {exc}") from exc

    try:
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise OpenRouterError(
            f"Unexpected OpenRouter API response format: {exc}"
        ) from exc
