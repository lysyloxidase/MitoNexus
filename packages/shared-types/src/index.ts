export type ApiHealthResponse = {
  status: "ok";
};

export type MarkerCategory =
  | "complete_blood_count"
  | "hormones"
  | "prostate"
  | "metabolic"
  | "liver"
  | "kidney"
  | "lipids"
  | "urinalysis"
  | "vitamins"
  | "electrolytes"
  | "thyroid"
  | "inflammation";

export type MarkerStatus =
  | "critically_low"
  | "low"
  | "suboptimal_low"
  | "optimal"
  | "suboptimal_high"
  | "high"
  | "critically_high";

export type RangeBounds = {
  min: number | null;
  max: number | null;
};

export type ReferenceRange = RangeBounds & {
  sex_specific: boolean;
  male?: RangeBounds | null;
  female?: RangeBounds | null;
};

export type OptimalRange = ReferenceRange;

export type MarkerInterpretationDefinition = {
  mito_impact: string;
  priority_therapies: string[];
};

export type MarkerDefinition = {
  id: string;
  name: string;
  category: MarkerCategory;
  unit_si: string;
  unit_conventional: string;
  conversion_factor: number;
  reference_range: ReferenceRange;
  optimal_range: OptimalRange;
  mito_cascades: string[];
  mito_genes: string[];
  kegg_pathways: string[];
  mito_mechanism: string;
  interpretations: Record<string, MarkerInterpretationDefinition>;
  derived_from?: string[];
  literature_refs?: string[];
  metadata?: Record<string, unknown>;
};

export type BloodMarkerInputPayload = {
  marker_id: string;
  value: number;
  unit: string;
};

export type BloodTestInputPayload = {
  patient_age: number;
  patient_sex: "M" | "F";
  test_date: string;
  markers: BloodMarkerInputPayload[];
};

export type AnalysisResponse = {
  report_id: string;
  task_id: string;
  status: "processing" | "complete" | "failed";
};

export type MarkerAnalysis = {
  marker_id: string;
  marker_name: string;
  value: number;
  unit: string;
  reference_min: number | null;
  reference_max: number | null;
  optimal_min: number | null;
  optimal_max: number | null;
  status: MarkerStatus;
  flag: "↑" | "↓" | "✓";
  affected_cascades: string[];
  affected_genes: string[];
  affected_kegg_pathways: string[];
  mito_interpretation: string;
  confidence: "high" | "medium" | "low";
};

export type CascadeStatus =
  | "optimal"
  | "mildly_affected"
  | "moderately_affected"
  | "severely_affected";

export type CascadeAssessment = {
  cascade_id: string;
  name: string;
  status: CascadeStatus;
  contributing_markers: string[];
  affected_genes: string[];
  kegg_pathway_id: string | null;
  impact_explanation: string;
  therapeutic_targets: string[];
};

export type GraphNodeType = "marker" | "gene" | "cascade" | "therapy" | "pathway";

export type GraphEdgeType =
  | "activation"
  | "inhibition"
  | "regulation"
  | "correlation"
  | "treats";

export type GraphNode = {
  id: string;
  type: GraphNodeType;
  label: string;
  centrality: number;
  color: string;
  size: number;
  abnormal: boolean;
  metadata: Record<string, unknown>;
};

export type GraphEdge = {
  source: string;
  target: string;
  type: GraphEdgeType;
  confidence: number;
  color: string;
  width: number;
};

export type KnowledgeGraphLayout = "forceatlas2" | "umap" | "hybrid";

export type KnowledgeGraphData = {
  nodes: GraphNode[];
  edges: GraphEdge[];
  layout: KnowledgeGraphLayout;
  precomputed_positions: Record<string, [number, number, number]> | null;
};

export type ETCComplexId = "I" | "II" | "III" | "IV" | "V";

export type ETCComplexState = {
  complex_id: ETCComplexId;
  activity: number;
  contributing_markers: string[];
  explanation: string;
};

export type MitochondrionAnnotation = {
  marker_id?: string;
  label?: string;
  status?: string;
  explanation?: string;
  [key: string]: unknown;
};

export type MitochondrionVisualization = {
  etc_complexes: ETCComplexState[];
  overall_health: number;
  annotations: MitochondrionAnnotation[];
};

export type ReportVisualizationPayload = {
  knowledge_graph: KnowledgeGraphData;
  mitochondrion: MitochondrionVisualization;
};

export type ReportStatus = "pending" | "processing" | "complete" | "failed";

export type AnalysisReportPayload = {
  report_id: string;
  patient_id: string;
  status: ReportStatus;
  workflow_task_id: string | null;
  error_message: string | null;
  mitoscore: number | null;
  mitoscore_components: Record<string, number> | null;
  affected_cascades: string[];
  literature_evidence: Record<string, unknown>[];
  marker_analyses: MarkerAnalysis[];
  cascade_assessments: CascadeAssessment[];
  therapy_plan: Record<string, unknown> | null;
  pdf_path: string | null;
  visualization_data: ReportVisualizationPayload | null;
  created_at: string;
  updated_at: string;
};
