from __future__ import annotations

import httpx

from mitonexus.agents.base import _resolve_ollama_model


def test_resolve_ollama_model_falls_back_when_requested_model_missing(
    monkeypatch,
) -> None:
    _resolve_ollama_model.cache_clear()

    def fake_get(url: str, timeout: float) -> httpx.Response:
        del url, timeout
        request = httpx.Request("GET", "http://ollama.local/api/tags")
        return httpx.Response(
            200,
            json={"models": [{"name": "qwen2.5:14b"}, {"name": "qwen2.5:7b"}]},
            request=request,
        )

    monkeypatch.setattr("mitonexus.agents.base.httpx.get", fake_get)

    resolved = _resolve_ollama_model(
        "deepseek-r1:14b",
        "http://ollama.local",
        "qwen2.5:14b",
        "qwen2.5:7b",
    )

    assert resolved == "qwen2.5:14b"
