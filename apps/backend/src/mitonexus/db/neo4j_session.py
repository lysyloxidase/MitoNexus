from collections.abc import Mapping
from functools import lru_cache
from typing import Any

from neo4j import AsyncDriver, AsyncGraphDatabase, AsyncManagedTransaction

from mitonexus.config import get_settings


class Neo4jClient:
    """Thin async wrapper around the Neo4j driver."""

    def __init__(self) -> None:
        settings = get_settings()
        self._database = settings.neo4j_database
        self._driver: AsyncDriver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )

    async def verify_connectivity(self) -> None:
        """Verify the configured Neo4j connection."""
        await self._driver.verify_connectivity()

    async def close(self) -> None:
        """Close the underlying driver."""
        await self._driver.close()

    async def execute_read(self, cypher: str, **params: Any) -> list[dict[str, Any]]:
        """Execute a read query and return materialized records."""
        async with self._driver.session(database=self._database) as session:
            return await session.execute_read(self._run_query, cypher, params)

    async def execute_write(self, cypher: str, **params: Any) -> list[dict[str, Any]]:
        """Execute a write query and return materialized records."""
        async with self._driver.session(database=self._database) as session:
            return await session.execute_write(self._run_query, cypher, params)

    @staticmethod
    async def _run_query(
        tx: AsyncManagedTransaction,
        cypher: str,
        params: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        result = await tx.run(cypher, **params)
        return [record.data() async for record in result]


@lru_cache
def get_neo4j_client() -> Neo4jClient:
    """Return the shared Neo4j client."""
    return Neo4jClient()


async def close_neo4j_client() -> None:
    """Close and clear the shared Neo4j client when it exists."""
    if get_neo4j_client.cache_info().currsize:
        client = get_neo4j_client()
        await client.close()
        get_neo4j_client.cache_clear()
