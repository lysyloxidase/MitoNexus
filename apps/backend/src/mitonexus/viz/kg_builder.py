from __future__ import annotations

from math import cos, sin, tau
from typing import Any

from mitonexus.db.neo4j_session import Neo4jClient, get_neo4j_client
from mitonexus.schemas.blood_marker import MarkerAnalysis, MarkerStatus
from mitonexus.schemas.cascade import CascadeAssessment, CascadeStatus
from mitonexus.schemas.therapy import TherapyRecommendation
from mitonexus.schemas.visualization import GraphEdge, GraphNode, KnowledgeGraphData

NODE_BASE_SIZES: dict[str, float] = {
    "marker": 11.0,
    "gene": 8.5,
    "cascade": 14.0,
    "therapy": 13.0,
    "pathway": 10.5,
}

NODE_COLORS: dict[str, str] = {
    "marker": "#ef4444",
    "gene": "#3b82f6",
    "cascade": "#22c55e",
    "therapy": "#a855f7",
    "pathway": "#f59e0b",
}

EDGE_COLORS: dict[str, str] = {
    "activation": "#22c55e",
    "inhibition": "#ef4444",
    "regulation": "#3b82f6",
    "correlation": "#94a3b8",
    "treats": "#a855f7",
}

CASCADE_SEVERITY_WEIGHTS: dict[CascadeStatus, float] = {
    CascadeStatus.OPTIMAL: 0.4,
    CascadeStatus.MILDLY_AFFECTED: 0.62,
    CascadeStatus.MODERATELY_AFFECTED: 0.8,
    CascadeStatus.SEVERELY_AFFECTED: 1.0,
}

MARKER_ABNORMAL_STATUSES = {
    MarkerStatus.CRITICALLY_LOW,
    MarkerStatus.LOW,
    MarkerStatus.SUBOPTIMAL_LOW,
    MarkerStatus.SUBOPTIMAL_HIGH,
    MarkerStatus.HIGH,
    MarkerStatus.CRITICALLY_HIGH,
}


class KnowledgeGraphBuilder:
    """Build a patient-specific graph payload from Neo4j plus local report context."""

    def __init__(self, neo4j: Neo4jClient | None = None) -> None:
        self.neo4j = neo4j or get_neo4j_client()

    async def build(
        self,
        marker_analyses: list[MarkerAnalysis],
        cascade_assessments: list[CascadeAssessment],
        therapy_recommendations: list[TherapyRecommendation],
    ) -> KnowledgeGraphData:
        """Build the graph payload used by the frontend 3D graph scene."""
        nodes: dict[str, GraphNode] = {}
        edges: dict[tuple[str, str, str], GraphEdge] = {}

        marker_lookup = {analysis.marker_id: analysis for analysis in marker_analyses}
        cascade_lookup = {assessment.cascade_id: assessment for assessment in cascade_assessments}
        therapy_lookup = {
            recommendation.therapy_id: recommendation for recommendation in therapy_recommendations
        }

        subgraph_records = await self._query_subgraph(list(marker_lookup))
        self._apply_neo4j_subgraph(
            subgraph_records,
            nodes,
            edges,
            marker_lookup,
            cascade_lookup,
            therapy_lookup,
        )
        self._apply_local_context(
            nodes,
            edges,
            marker_analyses,
            cascade_assessments,
            therapy_recommendations,
        )

        self._apply_centrality(nodes, list(edges.values()))
        positions = self._compute_positions(list(nodes.values()), list(edges.values()))

        return KnowledgeGraphData(
            nodes=list(nodes.values()),
            edges=list(edges.values()),
            layout="hybrid",
            precomputed_positions=positions if positions else None,
        )

    async def _query_subgraph(self, marker_ids: list[str]) -> list[dict[str, Any]]:
        if not marker_ids:
            return []

        cypher = """
        MATCH (m:BloodMarker)-[r1]-(g:Gene)
        WHERE m.id IN $marker_ids
        OPTIONAL MATCH (g)-[r2]-(c:Cascade)
        OPTIONAL MATCH (c)-[r3]-(t:Therapy)
        RETURN
          properties(m) AS marker,
          properties(g) AS gene,
          properties(c) AS cascade,
          properties(t) AS therapy,
          type(r1) AS marker_gene_relation,
          type(r2) AS gene_cascade_relation,
          type(r3) AS cascade_therapy_relation
        """
        try:
            return await self.neo4j.execute_read(cypher, marker_ids=marker_ids)
        except Exception:
            return []

    def _apply_neo4j_subgraph(
        self,
        records: list[dict[str, Any]],
        nodes: dict[str, GraphNode],
        edges: dict[tuple[str, str, str], GraphEdge],
        marker_lookup: dict[str, MarkerAnalysis],
        cascade_lookup: dict[str, CascadeAssessment],
        therapy_lookup: dict[str, TherapyRecommendation],
    ) -> None:
        for record in records:
            marker_data = record.get("marker")
            gene_data = record.get("gene")
            cascade_data = record.get("cascade")
            therapy_data = record.get("therapy")

            marker_id = self._read_identifier(marker_data)
            gene_id = self._read_identifier(gene_data)
            cascade_id = self._read_identifier(cascade_data)
            therapy_id = self._read_identifier(therapy_data)

            if marker_id and marker_id in marker_lookup:
                analysis = marker_lookup[marker_id]
                self._upsert_node(
                    nodes,
                    GraphNode(
                        id=f"marker:{analysis.marker_id}",
                        type="marker",
                        label=analysis.marker_name,
                        centrality=0.5,
                        color=(
                            "#22c55e"
                            if analysis.status == MarkerStatus.OPTIMAL
                            else NODE_COLORS["marker"]
                        ),
                        size=NODE_BASE_SIZES["marker"],
                        abnormal=analysis.status in MARKER_ABNORMAL_STATUSES,
                        metadata={
                            "marker_id": analysis.marker_id,
                            "status": analysis.status.value,
                            "value": analysis.value,
                            "unit": analysis.unit,
                            "genes": analysis.affected_genes,
                        },
                    ),
                )

            if gene_id:
                gene_label = self._read_label(gene_data, fallback=gene_id.upper())
                self._upsert_node(
                    nodes,
                    GraphNode(
                        id=f"gene:{gene_id}",
                        type="gene",
                        label=gene_label,
                        centrality=0.5,
                        color=NODE_COLORS["gene"],
                        size=NODE_BASE_SIZES["gene"],
                        metadata={"gene_id": gene_id},
                    ),
                )

            if cascade_id:
                assessment = cascade_lookup.get(cascade_id)
                cascade_label = self._read_label(cascade_data, fallback=cascade_id)
                self._upsert_node(
                    nodes,
                    GraphNode(
                        id=f"cascade:{cascade_id}",
                        type="cascade",
                        label=assessment.name if assessment is not None else cascade_label,
                        centrality=0.5,
                        color=NODE_COLORS["cascade"],
                        size=NODE_BASE_SIZES["cascade"],
                        abnormal=assessment is not None
                        and assessment.status != CascadeStatus.OPTIMAL,
                        metadata={
                            "cascade_id": cascade_id,
                            "status": assessment.status.value
                            if assessment is not None
                            else "optimal",
                        },
                    ),
                )

            if therapy_id:
                recommendation = therapy_lookup.get(therapy_id)
                therapy_label = self._read_label(
                    therapy_data, fallback=therapy_id.replace("_", " ")
                )
                self._upsert_node(
                    nodes,
                    GraphNode(
                        id=f"therapy:{therapy_id}",
                        type="therapy",
                        label=recommendation.name
                        if recommendation is not None
                        else therapy_label.title(),
                        centrality=0.5,
                        color=NODE_COLORS["therapy"],
                        size=NODE_BASE_SIZES["therapy"],
                        metadata={
                            "therapy_id": therapy_id,
                            "category": recommendation.category.value
                            if recommendation is not None
                            else None,
                        },
                    ),
                )

            if marker_id and gene_id and marker_id in marker_lookup:
                self._upsert_edge(
                    edges,
                    GraphEdge(
                        source=f"marker:{marker_id}",
                        target=f"gene:{gene_id}",
                        type=self._map_relation_type(
                            record.get("marker_gene_relation"), fallback="regulation"
                        ),
                        confidence=0.74,
                        color=EDGE_COLORS["regulation"],
                        width=1.7,
                    ),
                )

            if gene_id and cascade_id:
                relation_type = self._map_relation_type(
                    record.get("gene_cascade_relation"), fallback="activation"
                )
                self._upsert_edge(
                    edges,
                    GraphEdge(
                        source=f"gene:{gene_id}",
                        target=f"cascade:{cascade_id}",
                        type=relation_type,
                        confidence=0.7,
                        color=EDGE_COLORS[relation_type],
                        width=1.6,
                    ),
                )

            if cascade_id and therapy_id:
                relation_type = self._map_relation_type(
                    record.get("cascade_therapy_relation"), fallback="treats"
                )
                self._upsert_edge(
                    edges,
                    GraphEdge(
                        source=f"therapy:{therapy_id}",
                        target=f"cascade:{cascade_id}",
                        type=relation_type,
                        confidence=0.76,
                        color=EDGE_COLORS[relation_type],
                        width=1.8,
                    ),
                )

    def _apply_local_context(
        self,
        nodes: dict[str, GraphNode],
        edges: dict[tuple[str, str, str], GraphEdge],
        marker_analyses: list[MarkerAnalysis],
        cascade_assessments: list[CascadeAssessment],
        therapy_recommendations: list[TherapyRecommendation],
    ) -> None:
        for analysis in marker_analyses:
            abnormal = analysis.status in MARKER_ABNORMAL_STATUSES
            marker_node_id = f"marker:{analysis.marker_id}"
            self._upsert_node(
                nodes,
                GraphNode(
                    id=marker_node_id,
                    type="marker",
                    label=analysis.marker_name,
                    centrality=0.5,
                    color=NODE_COLORS["marker"] if abnormal else "#22c55e",
                    size=NODE_BASE_SIZES["marker"],
                    abnormal=abnormal,
                    metadata={
                        "marker_id": analysis.marker_id,
                        "status": analysis.status.value,
                        "value": analysis.value,
                        "unit": analysis.unit,
                        "interpretation": analysis.mito_interpretation,
                    },
                ),
            )

            for gene_id in analysis.affected_genes[:10]:
                gene_node_id = f"gene:{gene_id.lower()}"
                self._upsert_node(
                    nodes,
                    GraphNode(
                        id=gene_node_id,
                        type="gene",
                        label=gene_id,
                        centrality=0.5,
                        color=NODE_COLORS["gene"],
                        size=NODE_BASE_SIZES["gene"],
                        abnormal=abnormal,
                        metadata={"gene_id": gene_id},
                    ),
                )
                self._upsert_edge(
                    edges,
                    GraphEdge(
                        source=marker_node_id,
                        target=gene_node_id,
                        type="regulation",
                        confidence=0.66,
                        color=EDGE_COLORS["regulation"],
                        width=1.2,
                    ),
                )

            for pathway_id in analysis.affected_kegg_pathways[:8]:
                pathway_node_id = f"pathway:{pathway_id}"
                self._upsert_node(
                    nodes,
                    GraphNode(
                        id=pathway_node_id,
                        type="pathway",
                        label=pathway_id.upper(),
                        centrality=0.5,
                        color=NODE_COLORS["pathway"],
                        size=NODE_BASE_SIZES["pathway"],
                        abnormal=abnormal,
                        metadata={"pathway_id": pathway_id},
                    ),
                )
                self._upsert_edge(
                    edges,
                    GraphEdge(
                        source=marker_node_id,
                        target=pathway_node_id,
                        type="correlation",
                        confidence=0.58,
                        color=EDGE_COLORS["correlation"],
                        width=1.1,
                    ),
                )

        for assessment in cascade_assessments:
            cascade_node_id = f"cascade:{assessment.cascade_id}"
            abnormal = assessment.status != CascadeStatus.OPTIMAL
            self._upsert_node(
                nodes,
                GraphNode(
                    id=cascade_node_id,
                    type="cascade",
                    label=assessment.name,
                    centrality=0.5,
                    color=NODE_COLORS["cascade"],
                    size=NODE_BASE_SIZES["cascade"],
                    abnormal=abnormal,
                    metadata={
                        "cascade_id": assessment.cascade_id,
                        "status": assessment.status.value,
                        "therapeutic_targets": assessment.therapeutic_targets,
                    },
                ),
            )

            for marker_id in assessment.contributing_markers:
                marker_node_id = f"marker:{marker_id}"
                if marker_node_id not in nodes:
                    continue
                self._upsert_edge(
                    edges,
                    GraphEdge(
                        source=marker_node_id,
                        target=cascade_node_id,
                        type="regulation",
                        confidence=CASCADE_SEVERITY_WEIGHTS[assessment.status],
                        color=EDGE_COLORS["regulation"],
                        width=1.4,
                    ),
                )

            for gene_id in assessment.affected_genes[:10]:
                gene_node_id = f"gene:{gene_id.lower()}"
                if gene_node_id not in nodes:
                    self._upsert_node(
                        nodes,
                        GraphNode(
                            id=gene_node_id,
                            type="gene",
                            label=gene_id,
                            centrality=0.5,
                            color=NODE_COLORS["gene"],
                            size=NODE_BASE_SIZES["gene"],
                            abnormal=abnormal,
                            metadata={"gene_id": gene_id},
                        ),
                    )
                self._upsert_edge(
                    edges,
                    GraphEdge(
                        source=gene_node_id,
                        target=cascade_node_id,
                        type="activation",
                        confidence=0.64,
                        color=EDGE_COLORS["activation"],
                        width=1.3,
                    ),
                )

            if assessment.kegg_pathway_id is not None:
                pathway_node_id = f"pathway:{assessment.kegg_pathway_id}"
                self._upsert_node(
                    nodes,
                    GraphNode(
                        id=pathway_node_id,
                        type="pathway",
                        label=assessment.kegg_pathway_id.upper(),
                        centrality=0.5,
                        color=NODE_COLORS["pathway"],
                        size=NODE_BASE_SIZES["pathway"],
                        abnormal=abnormal,
                        metadata={"pathway_id": assessment.kegg_pathway_id},
                    ),
                )
                self._upsert_edge(
                    edges,
                    GraphEdge(
                        source=cascade_node_id,
                        target=pathway_node_id,
                        type="correlation",
                        confidence=0.62,
                        color=EDGE_COLORS["correlation"],
                        width=1.2,
                    ),
                )

        for recommendation in therapy_recommendations[:12]:
            therapy_node_id = f"therapy:{recommendation.therapy_id}"
            self._upsert_node(
                nodes,
                GraphNode(
                    id=therapy_node_id,
                    type="therapy",
                    label=recommendation.name,
                    centrality=0.5,
                    color=NODE_COLORS["therapy"],
                    size=NODE_BASE_SIZES["therapy"],
                    metadata={
                        "therapy_id": recommendation.therapy_id,
                        "category": recommendation.category.value,
                        "evidence_level": recommendation.evidence_level.value,
                        "priority_score": recommendation.priority_score,
                    },
                ),
            )

            for cascade_id in recommendation.targets_cascades:
                cascade_node_id = f"cascade:{cascade_id}"
                if cascade_node_id not in nodes:
                    continue
                self._upsert_edge(
                    edges,
                    GraphEdge(
                        source=therapy_node_id,
                        target=cascade_node_id,
                        type="treats",
                        confidence=min(max(recommendation.priority_score / 100.0, 0.45), 0.95),
                        color=EDGE_COLORS["treats"],
                        width=1.6,
                    ),
                )

    def _apply_centrality(self, nodes: dict[str, GraphNode], edges: list[GraphEdge]) -> None:
        node_ids = list(nodes)
        if not node_ids:
            return

        adjacency: dict[str, set[str]] = {node_id: set() for node_id in node_ids}
        for edge in edges:
            adjacency.setdefault(edge.source, set()).add(edge.target)
            adjacency.setdefault(edge.target, set()).add(edge.source)

        pagerank = self._pagerank(adjacency)
        min_rank = min(pagerank.values(), default=0.0)
        max_rank = max(pagerank.values(), default=1.0)
        rank_span = max(max_rank - min_rank, 0.0001)

        for node_id, node in list(nodes.items()):
            normalized = (pagerank.get(node_id, 0.0) - min_rank) / rank_span
            node.centrality = round(normalized, 3)
            node.size = round(
                NODE_BASE_SIZES[node.type] + (normalized * 12.0) + (2.0 if node.abnormal else 0.0),
                2,
            )

    def _pagerank(self, adjacency: dict[str, set[str]]) -> dict[str, float]:
        node_ids = list(adjacency)
        if not node_ids:
            return {}

        rank = {node_id: 1.0 / len(node_ids) for node_id in node_ids}
        damping = 0.85
        teleport = (1.0 - damping) / len(node_ids)

        for _ in range(18):
            next_rank = dict.fromkeys(node_ids, teleport)
            for node_id, neighbors in adjacency.items():
                if not neighbors:
                    share = damping * rank[node_id] / len(node_ids)
                    for target_id in node_ids:
                        next_rank[target_id] += share
                    continue

                share = damping * rank[node_id] / len(neighbors)
                for target_id in neighbors:
                    next_rank[target_id] += share
            rank = next_rank

        return rank

    def _compute_positions(
        self,
        nodes: list[GraphNode],
        edges: list[GraphEdge],
    ) -> dict[str, tuple[float, float, float]]:
        if not nodes:
            return {}

        igraph_positions = self._try_igraph_layout(nodes, edges)
        if igraph_positions is not None:
            return igraph_positions

        components = self._connected_components(nodes, edges)
        positions: dict[str, tuple[float, float, float]] = {}
        component_spacing = 320.0

        for component_index, component in enumerate(components):
            component_center_x = (
                component_index - ((len(components) - 1) / 2.0)
            ) * component_spacing
            radius = 90.0 + (len(component) * 10.0)
            for node_index, node_id in enumerate(component):
                angle = tau * (node_index / max(len(component), 1))
                z_band = ((node_index % 5) - 2) * 34.0
                positions[node_id] = (
                    round(component_center_x + cos(angle) * radius, 3),
                    round(sin(angle) * radius, 3),
                    round(z_band, 3),
                )

        return positions

    def _try_igraph_layout(
        self,
        nodes: list[GraphNode],
        edges: list[GraphEdge],
    ) -> dict[str, tuple[float, float, float]] | None:
        try:
            import igraph as ig
        except Exception:
            return None

        node_index = {node.id: index for index, node in enumerate(nodes)}
        graph = ig.Graph(directed=False)
        graph.add_vertices(len(nodes))
        graph.add_edges(
            [
                (node_index[edge.source], node_index[edge.target])
                for edge in edges
                if edge.source in node_index and edge.target in node_index
            ]
        )

        try:
            layout = graph.layout_fruchterman_reingold_3d()
        except Exception:
            return None

        positions: dict[str, tuple[float, float, float]] = {}
        for node, coordinates in zip(nodes, layout.coords, strict=True):
            x_coord, y_coord, z_coord = [*coordinates, 0.0, 0.0, 0.0][:3]
            positions[node.id] = (
                round(float(x_coord) * 60.0, 3),
                round(float(y_coord) * 60.0, 3),
                round(float(z_coord) * 60.0, 3),
            )
        return positions

    def _connected_components(
        self,
        nodes: list[GraphNode],
        edges: list[GraphEdge],
    ) -> list[list[str]]:
        adjacency: dict[str, set[str]] = {node.id: set() for node in nodes}
        for edge in edges:
            adjacency.setdefault(edge.source, set()).add(edge.target)
            adjacency.setdefault(edge.target, set()).add(edge.source)

        visited: set[str] = set()
        components: list[list[str]] = []
        for node in nodes:
            if node.id in visited:
                continue

            stack = [node.id]
            component: list[str] = []
            while stack:
                current = stack.pop()
                if current in visited:
                    continue
                visited.add(current)
                component.append(current)
                stack.extend(
                    neighbor
                    for neighbor in adjacency.get(current, set())
                    if neighbor not in visited
                )

            components.append(sorted(component))

        return components

    def _upsert_node(self, nodes: dict[str, GraphNode], node: GraphNode) -> None:
        existing = nodes.get(node.id)
        if existing is None:
            nodes[node.id] = node
            return

        merged_metadata = {**existing.metadata, **node.metadata}
        nodes[node.id] = existing.model_copy(
            update={
                "label": node.label or existing.label,
                "abnormal": existing.abnormal or node.abnormal,
                "metadata": merged_metadata,
            }
        )

    def _upsert_edge(self, edges: dict[tuple[str, str, str], GraphEdge], edge: GraphEdge) -> None:
        edge_key = (edge.source, edge.target, edge.type)
        existing = edges.get(edge_key)
        if existing is None:
            edges[edge_key] = edge
            return

        edges[edge_key] = existing.model_copy(
            update={
                "confidence": max(existing.confidence, edge.confidence),
                "width": max(existing.width, edge.width),
            }
        )

    def _read_identifier(self, raw_data: object) -> str | None:
        if not isinstance(raw_data, dict):
            return None
        for key in ("id", "symbol", "name"):
            value = raw_data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip().lower() if key == "symbol" else value.strip()
        return None

    def _read_label(self, raw_data: object, fallback: str) -> str:
        if not isinstance(raw_data, dict):
            return fallback
        for key in ("label", "name", "symbol", "title"):
            value = raw_data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return fallback

    def _map_relation_type(self, relation_type: object, *, fallback: str) -> str:
        if not isinstance(relation_type, str):
            return fallback

        normalized = relation_type.upper()
        if "INHIB" in normalized:
            return "inhibition"
        if "ACTIV" in normalized:
            return "activation"
        if "TREAT" in normalized or "TARGET" in normalized:
            return "treats"
        if "CORREL" in normalized:
            return "correlation"
        return "regulation"
