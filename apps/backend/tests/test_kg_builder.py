from collections.abc import AsyncIterator

import pytest
import pytest_asyncio

from mitonexus.db.neo4j_session import Neo4jClient, get_neo4j_client
from mitonexus.schemas.blood_marker import MarkerAnalysis, MarkerStatus
from mitonexus.schemas.cascade import CascadeAssessment, CascadeStatus
from mitonexus.schemas.therapy import EvidenceLevel, TherapyCategory, TherapyRecommendation
from mitonexus.viz import KnowledgeGraphBuilder


@pytest_asyncio.fixture
async def neo4j_client() -> AsyncIterator[Neo4jClient]:
    client = get_neo4j_client()
    await client.verify_connectivity()
    await client.execute_write("MATCH (n) DETACH DELETE n")
    yield client
    await client.execute_write("MATCH (n) DETACH DELETE n")


@pytest.mark.anyio
async def test_kg_builder_merges_neo4j_subgraph_with_patient_context(
    neo4j_client: Neo4jClient,
) -> None:
    await neo4j_client.execute_write(
        """
        MERGE (marker:BloodMarker {id: $marker_id, name: $marker_name})
        MERGE (gene:Gene {id: $gene_id, symbol: $gene_symbol})
        MERGE (cascade:Cascade {id: $cascade_id, name: $cascade_name})
        MERGE (therapy:Therapy {id: $therapy_id, name: $therapy_name})
        MERGE (marker)-[:REGULATES]->(gene)
        MERGE (gene)-[:ACTIVATES]->(cascade)
        MERGE (cascade)-[:TARGETED_BY]->(therapy)
        """,
        marker_id="homocysteine",
        marker_name="Homocysteine",
        gene_id="cbs",
        gene_symbol="CBS",
        cascade_id="uprmt",
        cascade_name="UPRmt/ATF4-ATF5",
        therapy_id="glycine_nac",
        therapy_name="Glycine + NAC",
    )

    graph = await KnowledgeGraphBuilder(neo4j=neo4j_client).build(
        marker_analyses=[
            MarkerAnalysis(
                marker_id="homocysteine",
                marker_name="Homocysteine",
                value=14.8,
                unit="µmol/L",
                reference_min=5.0,
                reference_max=15.0,
                optimal_min=5.0,
                optimal_max=8.0,
                status=MarkerStatus.HIGH,
                flag="↑",
                affected_cascades=["uprmt", "nrf2_keap1"],
                affected_genes=["CBS", "MTHFR"],
                affected_kegg_pathways=["hsa00190"],
                mito_interpretation="Elevated homocysteine increases mtROS and impairs ETC flux.",
                confidence="high",
            )
        ],
        cascade_assessments=[
            CascadeAssessment(
                cascade_id="uprmt",
                name="UPRmt/ATF4-ATF5",
                status=CascadeStatus.SEVERELY_AFFECTED,
                contributing_markers=["homocysteine"],
                affected_genes=["CBS"],
                kegg_pathway_id="hsa00190",
                impact_explanation="Proteostatic stress signaling is strongly upregulated.",
                therapeutic_targets=["glycine_nac"],
            )
        ],
        therapy_recommendations=[
            TherapyRecommendation(
                therapy_id="glycine_nac",
                name="Glycine + NAC",
                category=TherapyCategory.SUPPLEMENTATION,
                mechanism_summary="Supports glutathione recycling and transsulfuration.",
                detailed_mechanism="May reduce oxidative pressure linked to elevated homocysteine.",
                dosage="600 mg / 900 mg daily",
                timing="morning and evening",
                evidence_level=EvidenceLevel.C,
                fda_status="not_fda_approved",
                nct_ids=["NCT00000000"],
                source_pmids=["12345678"],
                targets_cascades=["uprmt"],
                corrects_markers=["homocysteine"],
                contraindications=["sulfur sensitivity"],
                priority_score=88.0,
            )
        ],
    )

    node_ids = {node.id for node in graph.nodes}
    edge_triplets = {(edge.source, edge.target, edge.type) for edge in graph.edges}

    assert "marker:homocysteine" in node_ids
    assert "gene:cbs" in node_ids
    assert "cascade:uprmt" in node_ids
    assert "therapy:glycine_nac" in node_ids
    assert "pathway:hsa00190" in node_ids

    assert ("marker:homocysteine", "gene:cbs", "regulation") in edge_triplets
    assert ("gene:cbs", "cascade:uprmt", "activation") in edge_triplets
    assert ("therapy:glycine_nac", "cascade:uprmt", "treats") in edge_triplets

    assert graph.precomputed_positions is not None
    assert set(graph.precomputed_positions).issuperset(node_ids)

    marker_node = next(node for node in graph.nodes if node.id == "marker:homocysteine")
    therapy_node = next(node for node in graph.nodes if node.id == "therapy:glycine_nac")
    assert marker_node.abnormal is True
    assert therapy_node.metadata["category"] == TherapyCategory.SUPPLEMENTATION.value
