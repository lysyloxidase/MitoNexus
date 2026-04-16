import math

from mitonexus.services.embedding import EmbeddingService


class FakeSentenceTransformer:
    def encode(self, texts: list[str], show_progress_bar: bool = False) -> list[list[float]]:
        del show_progress_bar
        embeddings: list[list[float]] = []
        for text in texts:
            if "mitochondria" in text.lower():
                embeddings.append([1.0, 0.0] + ([0.0] * 766))
            else:
                embeddings.append([0.0, 1.0] + ([0.0] * 766))
        return embeddings


async def test_embedding_service_returns_768_dimensions() -> None:
    service = EmbeddingService(model=FakeSentenceTransformer())

    embeddings = await service.embed_batch(["mitochondria signal", "unrelated topic"])

    assert len(embeddings) == 2
    assert len(embeddings[0]) == 768
    assert len(embeddings[1]) == 768


async def test_embedding_similarity_is_higher_for_related_text() -> None:
    service = EmbeddingService(model=FakeSentenceTransformer())

    first, second, third = await service.embed_batch(
        ["mitochondria dynamics", "mitochondria biogenesis", "cardiology review"]
    )

    assert cosine_similarity(first, second) > cosine_similarity(first, third)


def cosine_similarity(left: list[float], right: list[float]) -> float:
    dot_product = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    return dot_product / (left_norm * right_norm)
