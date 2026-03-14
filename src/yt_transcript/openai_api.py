"""OpenAI API client for LLM completions."""

from __future__ import annotations

import os
from typing import Any

import httpx

from .errors import OpenAIError


OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


def chat_completion(
    model: str,
    messages: list[dict[str, str]],
    *,
    api_key: str | None = None,
    api_url: str | None = None,
    timeout: float = 120.0,
) -> str:
    """Send a chat completion request to OpenAI."""

    api_key = api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise OpenAIError("OPENAI_API_KEY environment variable is not set.")

    headers: dict[str, str] = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
    }

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(api_url or OPENAI_API_URL, headers=headers, json=payload)
            response.raise_for_status()
    except httpx.TimeoutException as exc:
        raise OpenAIError(f"OpenAI API request timed out: {exc}") from exc
    except httpx.HTTPStatusError as exc:
        raise OpenAIError(
            f"OpenAI API error ({exc.response.status_code}): {exc.response.text}"
        ) from exc
    except httpx.RequestError as exc:
        raise OpenAIError(f"OpenAI API request failed: {exc}") from exc

    try:
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise OpenAIError(f"Unexpected OpenAI API response format: {exc}") from exc
