import os
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from mitonexus.db.session import AsyncSessionLocal, engine
from mitonexus.models import Base


def pytest_sessionstart(session: pytest.Session) -> None:
    del session
    os.environ.setdefault(
        "MITONEXUS_DATABASE_URL",
        os.getenv(
            "MITONEXUS_TEST_DATABASE_URL",
            "postgresql+asyncpg://mitonexus:mitonexus_dev@localhost:5432/mitonexus",
        ),
    )
    os.environ.setdefault(
        "MITONEXUS_REDIS_URL",
        os.getenv("MITONEXUS_TEST_REDIS_URL", "redis://localhost:6379/0"),
    )
    os.environ.setdefault(
        "MITONEXUS_NEO4J_URI",
        os.getenv("MITONEXUS_TEST_NEO4J_URI", "bolt://localhost:7687"),
    )
    os.environ.setdefault(
        "MITONEXUS_NEO4J_USER",
        os.getenv("MITONEXUS_TEST_NEO4J_USER", "neo4j"),
    )
    os.environ.setdefault(
        "MITONEXUS_NEO4J_PASSWORD",
        os.getenv("MITONEXUS_TEST_NEO4J_PASSWORD", "mitonexus_dev"),
    )
    os.environ.setdefault(
        "MITONEXUS_NEO4J_DATABASE",
        os.getenv("MITONEXUS_TEST_NEO4J_DATABASE", "neo4j"),
    )

    from mitonexus.config import get_settings

    get_settings.cache_clear()


@pytest.fixture(scope="session")
def alembic_config() -> Config:
    backend_dir = Path(__file__).resolve().parents[1]
    config = Config(str(backend_dir / "alembic.ini"))
    config.set_main_option("script_location", str(backend_dir / "alembic"))
    return config


@pytest.fixture(scope="session")
def prepared_database(alembic_config: Config) -> None:
    command.upgrade(alembic_config, "head")


@pytest.fixture(scope="session")
def db_engine(prepared_database: None) -> AsyncEngine:
    del prepared_database
    return engine


async def _truncate_tables(db_engine: AsyncEngine) -> None:
    table_names = [table.name for table in reversed(Base.metadata.sorted_tables)]
    if not table_names:
        return

    joined_tables = ", ".join(table_names)
    async with db_engine.begin() as connection:
        await connection.execute(text(f"TRUNCATE TABLE {joined_tables} RESTART IDENTITY CASCADE"))


@pytest_asyncio.fixture(autouse=True)
async def clean_database(db_engine: AsyncEngine) -> AsyncIterator[None]:
    await _truncate_tables(db_engine)
    yield
    await _truncate_tables(db_engine)


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()
