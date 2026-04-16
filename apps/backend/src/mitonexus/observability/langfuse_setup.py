from __future__ import annotations

from functools import lru_cache
from typing import Any

from langfuse import Langfuse
from langfuse.langchain import CallbackHandler

from mitonexus.config import get_settings


@lru_cache
def get_langfuse_client() -> Langfuse | None:
    """Return the shared Langfuse client when credentials are configured."""
    settings = get_settings()
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        return None

    return Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )


def get_langfuse_callback(user_id: str, session_id: str) -> Any | None:
    """Return a Langfuse callback handler for LangChain-compatible calls."""
    client = get_langfuse_client()
    if client is None:
        return None

    del user_id, session_id
    settings = get_settings()
    return CallbackHandler(public_key=settings.langfuse_public_key)
