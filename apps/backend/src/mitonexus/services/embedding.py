from __future__ import annotations

import asyncio
from typing import Any, Protocol, cast

from sentence_transformers import SentenceTransformer


class _EmbeddableModel(Protocol):
    def encode(self, texts: list[str], show_progress_bar: bool = False) -> Any: ...


class EmbeddingService:
    """PubMedBERT-based embeddings for biomedical text."""

    def __init__(
        self,
        model_name: str = "NeuML/pubmedbert-base-embeddings",
        model: _EmbeddableModel | None = None,
    ) -> None:
        self._model_name = model_name
        self._model = model

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts and return 768-dimensional vectors."""
        if not texts:
            return []

        model = self._get_model()
        raw_embeddings = await asyncio.to_thread(self._encode, model, texts)
        if hasattr(raw_embeddings, "tolist"):
            raw_embeddings = raw_embeddings.tolist()

        embeddings = cast(list[list[float]], raw_embeddings)
        return [[float(value) for value in embedding] for embedding in embeddings]

    async def embed_single(self, text: str) -> list[float]:
        """Embed a single text sample."""
        return (await self.embed_batch([text]))[0]

    def _get_model(self) -> _EmbeddableModel:
        if self._model is None:
            self._model = SentenceTransformer(self._model_name)
        return self._model

    def _encode(self, model: _EmbeddableModel, texts: list[str]) -> Any:
        return model.encode(texts, show_progress_bar=False)
