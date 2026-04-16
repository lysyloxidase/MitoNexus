import os

import pytest


def pytest_sessionstart(session: pytest.Session) -> None:
    del session
    os.environ.setdefault(
        "MITONEXUS_DATABASE_URL",
        "postgresql+asyncpg://test:test@localhost:5432/test",
    )
    os.environ.setdefault("MITONEXUS_REDIS_URL", "redis://localhost:6379/0")
    os.environ.setdefault("MITONEXUS_NEO4J_PASSWORD", "test")

    from mitonexus.config import get_settings

    get_settings.cache_clear()
