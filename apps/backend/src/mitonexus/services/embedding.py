from __future__ import annotations

import asyncio
from typing import Any, Protocol, cast

from ollama import AsyncClient as OllamaAsyncClient
from sentence_transformers import SentenceTransformer

from mitonexus.config import get_settings


class _EmbeddableModel(Protocol):
    def encode(self, texts: list[str], show_progress_bar: bool = False) -> Any: ...


class _OllamaEmbeddingsClient(Protocol):
    async def embed(self, model: str = "", input_text: str | list[str] = "") -> Any: ...


class EmbeddingService:
    """PubMedBERT-based embeddings for biomedical text."""

    def __init__(
        self,
        model_name: str = "NeuML/pubmedbert-base-embeddings",
        model: _EmbeddableModel | None = None,
        ollama_client: _OllamaEmbeddingsClient | None = None,
        ollama_host: str | None = None,
        ollama_model: str | None = None,
    ) -> None:
        self._model_name = model_name
        self._model = model
        self._ollama_client = ollama_client
        self._ollama_host = ollama_host
        self._ollama_model = ollama_model

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts and return 768-dimensional vectors."""
        if not texts:
            return []

        try:
            model = self._get_model()
            raw_embeddings = await asyncio.to_thread(self._encode, model, texts)
        except Exception as primary_exc:
            try:
                return await self._embed_with_ollama(texts)
            except Exception as fallback_exc:
                msg = (
                    "Embedding failed with both SentenceTransformer and Ollama fallback: "
                    f"{primary_exc}; {fallback_exc}"
                )
                raise RuntimeError(msg) from fallback_exc

        return self._coerce_embeddings(raw_embeddings)

    async def embed_single(self, text: str) -> list[float]:
        """Embed a single text sample."""
        return (await self.embed_batch([text]))[0]

    def _get_model(self) -> _EmbeddableModel:
        if self._model is None:
            self._model = SentenceTransformer(self._model_name)
        return self._model

    def _get_ollama_client(self) -> _OllamaEmbeddingsClient:
        if self._ollama_client is None:
            settings = get_settings()
            self._ollama_client = OllamaAsyncClient(host=self._ollama_host or settings.ollama_host)
        return self._ollama_client

    def _get_ollama_model_name(self) -> str:
        if self._ollama_model is not None:
            return self._ollama_model
        return get_settings().model_embedding

    async def _embed_with_ollama(self, texts: list[str]) -> list[list[float]]:
        response = await self._get_ollama_client().embed(
            model=self._get_ollama_model_name(),
            input=texts,
        )
        return self._coerce_embeddings(response.embeddings)

    def _encode(self, model: _EmbeddableModel, texts: list[str]) -> Any:
        return model.encode(texts, show_progress_bar=False)

    def _coerce_embeddings(self, raw_embeddings: Any) -> list[list[float]]:
        if hasattr(raw_embeddings, "tolist"):
            raw_embeddings = raw_embeddings.tolist()

        embeddings = cast(list[list[float]], raw_embeddings)
        return [[float(value) for value in embedding] for embedding in embeddings]
