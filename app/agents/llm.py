"""Claude JSON calls with retries. Schema failures retry with the error (spec 13 REQ-008)."""

from __future__ import annotations

import json
import re
import time
from typing import Protocol, TypeVar

from pydantic import BaseModel, ValidationError

from app.config import get_settings
from app.services.bedrock import invoke_claude
from app.services.local_ai import complete_local, local_freeform
from app.services.openai_client import invoke_openai_chat

T = TypeVar("T", bound=BaseModel)
STEP_TIMEOUT_SECONDS = 120
MAX_ATTEMPTS = 3
JSON_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.I | re.M)


class LLM(Protocol):
    def complete(self, prompt: str) -> str:
        ...


class ClaudeLLM:
    def complete(self, prompt: str) -> str:
        provider = get_settings().llm_provider
        if provider == "openai":
            return invoke_openai_chat(prompt, max_tokens=4096)
        if provider == "local":
            return local_freeform(prompt)
        return invoke_claude(prompt, max_tokens=4096)


def parse_json_object(text: str) -> dict:
    cleaned = JSON_FENCE.sub("", text.strip()).strip()
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1:
            raise
        payload = json.loads(cleaned[start : end + 1])
    if not isinstance(payload, dict):
        raise ValueError("Expected a JSON object")
    return payload


def parse_model(model: type[T], text: str) -> T:
    return model.model_validate(parse_json_object(text))


def complete_model(llm: LLM, prompt: str, model: type[T], *, started_at: float) -> tuple[T, int]:
    if get_settings().llm_provider == "local":
        return complete_local(prompt, model)
    current = prompt
    last_error: Exception | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        if time.monotonic() - started_at > STEP_TIMEOUT_SECONDS:
            raise TimeoutError("Step exceeded 120 seconds")
        raw = llm.complete(current)
        try:
            return parse_model(model, raw), attempt
        except (ValidationError, json.JSONDecodeError, ValueError) as exc:
            last_error = exc
            current = (
                f"{prompt}\n\nYour previous JSON failed validation:\n{exc}\n"
                f"Previous output:\n{raw[:1500]}\nReturn corrected JSON only."
            )
    assert last_error is not None
    raise last_error
