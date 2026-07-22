"""Validated structured-generator adapters, including local Ollama."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Mapping, Sequence
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel

ResponseT = TypeVar("ResponseT", bound=BaseModel)


class StructuredGenerator(Protocol):
    name: str
    version: str | None

    def generate(
        self,
        response_type: type[ResponseT],
        *,
        system: str,
        prompt: str,
    ) -> ResponseT: ...


class OllamaGenerator:
    name = "ollama"

    def __init__(
        self,
        model: str,
        *,
        url: str = "http://127.0.0.1:11434",
        timeout: float = 300,
    ) -> None:
        self.model = model
        self.url = url.rstrip("/")
        self.timeout = timeout
        self.version: str | None = None

    def generate(
        self,
        response_type: type[ResponseT],
        *,
        system: str,
        prompt: str,
    ) -> ResponseT:
        payload = {
            "model": self.model,
            "stream": False,
            "format": response_type.model_json_schema(),
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "options": {"temperature": 0.2},
        }
        request = urllib.request.Request(
            self.url + "/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                result = json.load(response)
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Ollama request failed: {exc}") from exc
        message = result.get("message")
        if not isinstance(message, Mapping):
            raise RuntimeError("Ollama response is missing message")
        content = message.get("content")
        if not isinstance(content, str):
            raise RuntimeError("Ollama response content is not text")
        try:
            decoded = json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Ollama returned invalid structured JSON") from exc
        return response_type.model_validate(decoded)


class StubGenerator:
    """Deterministic queued generator for tests and offline workflow proofs."""

    name = "stub"
    version = "1"

    def __init__(self, responses: Sequence[Mapping[str, Any]]) -> None:
        self.responses = list(responses)

    def generate(
        self,
        response_type: type[ResponseT],
        *,
        system: str,
        prompt: str,
    ) -> ResponseT:
        del system, prompt
        if not self.responses:
            raise RuntimeError("stub generator has no response remaining")
        return response_type.model_validate(self.responses.pop(0))
