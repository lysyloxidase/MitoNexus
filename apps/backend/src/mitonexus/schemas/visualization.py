from typing import Any, Literal

from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    """Node payload for the 3D knowledge graph."""

    id: str
    type: Literal["marker", "gene", "cascade", "therapy", "pathway"]
    label: str
    centrality: float = 0.5
    color: str
    size: float
    abnormal: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """Edge payload for the 3D knowledge graph."""

    source: str
    target: str
    type: Literal["activation", "inhibition", "regulation", "correlation", "treats"]
    confidence: float = Field(..., ge=0, le=1)
    color: str
    width: float


class KnowledgeGraphData(BaseModel):
    """Serializable knowledge-graph payload for frontend rendering."""

    nodes: list[GraphNode]
    edges: list[GraphEdge]
    layout: Literal["forceatlas2", "umap", "hybrid"] = "hybrid"
    precomputed_positions: dict[str, tuple[float, float, float]] | None = None


class ETCComplexState(BaseModel):
    """Patient-specific state for a single ETC complex."""

    complex_id: Literal["I", "II", "III", "IV", "V"]
    activity: float = Field(..., ge=0, le=1)
    contributing_markers: list[str]
    explanation: str


class MitochondrionVisualization(BaseModel):
    """Patient overlay data for the mitochondrion model."""

    etc_complexes: list[ETCComplexState]
    overall_health: float = Field(..., ge=0, le=100)
    annotations: list[dict[str, Any]]
