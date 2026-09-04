# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""
Thin LLM adapter for SPD plugins.

Reuses the instance-wide LLM configuration (god-mode > AI, or the LLM_* env
vars) through `get_llm_config`, and talks to any OpenAI-compatible endpoint
with the `openai` SDK that Plane already ships.
"""

import json
import re
from typing import Any

_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.IGNORECASE)


def parse_json(text: str | None) -> dict[str, Any] | None:
    """Parse a JSON object from a model reply, tolerating fences and prose."""
    if not text:
        return None
    candidate = _FENCE_RE.sub("", text.strip())
    try:
        data = json.loads(candidate)
        return data if isinstance(data, dict) else None
    except ValueError:
        pass
    start, end = candidate.find("{"), candidate.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        data = json.loads(candidate[start : end + 1])
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def complete_json(system_prompt: str, user_prompt: str) -> tuple[dict[str, Any] | None, str | None, str, str]:
    """
    Ask the configured model for a JSON object.

    Returns (data, error, model, raw_text). Exactly one of data/error is set.
    """
    # Lazy imports: neither the openai SDK nor the views package should load during AppConfig.ready().
    from openai import BadRequestError, OpenAI

    from plane.app.views.external.base import get_llm_config

    api_key, model, provider, base_url = get_llm_config()
    if not api_key or not model:
        return None, "LLM is not configured (LLM_API_KEY / LLM_MODEL)", "", ""

    # Mirror get_llm_response(): Gemini models are addressed with a prefix.
    if (provider or "").lower() == "gemini":
        model = f"gemini/{model}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    client = OpenAI(api_key=api_key, base_url=base_url)
    try:
        try:
            completion = client.chat.completions.create(
                model=model, messages=messages, response_format={"type": "json_object"}
            )
        except BadRequestError:
            # Some OpenAI-compatible providers reject response_format; retry plain.
            completion = client.chat.completions.create(model=model, messages=messages)
    except Exception as e:  # noqa: BLE001
        return None, f"{e.__class__.__name__}: {e}", model, ""

    text = completion.choices[0].message.content or ""
    data = parse_json(text)
    if data is None:
        return None, "Model reply was not a JSON object", model, text
    return data, None, model, text
