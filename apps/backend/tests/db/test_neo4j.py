from collections.abc import AsyncIterator

import pytest_asyncio

from mitonexus.db.neo4j_session import Neo4jClient, get_neo4j_client


@pytest_asyncio.fixture
async def neo4j_client() -> AsyncIterator[Neo4jClient]:
    client = get_neo4j_client()
    await client.verify_connectivity()
    await client.execute_write("MATCH (n) DETACH DELETE n")
    yield client
    await client.execute_write("MATCH (n) DETACH DELETE n")


async def test_neo4j_write_and_read(neo4j_client: Neo4jClient) -> None:
    created_records = await neo4j_client.execute_write(
        """
        MERGE (cascade:Cascade {id: $cascade_id, name: $cascade_name})
        MERGE (gene:Gene {id: $gene_id, symbol: $gene_symbol})
        MERGE (cascade)-[:REGULATES]->(gene)
        RETURN cascade.id AS cascade_id, gene.id AS gene_id
        """,
        cascade_id="ampk",
        cascade_name="AMPK Signaling",
        gene_id="ppargc1a",
        gene_symbol="PPARGC1A",
    )

    assert created_records == [{"cascade_id": "ampk", "gene_id": "ppargc1a"}]

    read_records = await neo4j_client.execute_read(
        """
        MATCH (cascade:Cascade {id: $cascade_id})-[:REGULATES]->(gene:Gene)
        RETURN cascade.name AS cascade_name, gene.symbol AS gene_symbol
        """,
        cascade_id="ampk",
    )

    assert read_records == [
        {
            "cascade_name": "AMPK Signaling",
            "gene_symbol": "PPARGC1A",
        }
    ]
