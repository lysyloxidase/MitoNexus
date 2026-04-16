from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import TypeAdapter

from mitonexus.schemas.blood_marker import (
    BloodMarkerInput,
    BloodTestInput,
    MarkerAnalysis,
    MarkerDefinition,
    MarkerInterpretationDefinition,
    MarkerStatus,
    OptimalRange,
    RangeBounds,
    ReferenceRange,
)
from mitonexus.services.derived_calculations import (
    calculate_de_ritis,
    calculate_homa_ir,
    calculate_non_hdl,
)

MarkerDefinitionMap = TypeAdapter(dict[str, MarkerDefinition])
MarkerConfidence = Literal["high", "medium", "low"]
MarkerFlag = Literal["\u2191", "\u2193", "\u2713"]


class MarkerEngine:
    """Core blood marker analysis engine."""

    def __init__(self, data_path: Path | None = None) -> None:
        path = data_path or Path(__file__).parent.parent / "data" / "markers.json"
        self._definitions: dict[str, MarkerDefinition] = MarkerDefinitionMap.validate_json(
            path.read_text(encoding="utf-8")
        )

    @property
    def definitions(self) -> dict[str, MarkerDefinition]:
        """Return loaded marker definitions."""
        return self._definitions

    def get_definition(self, marker_id: str) -> MarkerDefinition | None:
        """Return a single marker definition when present."""
        return self._definitions.get(marker_id)

    def normalize_markers(self, blood_test: BloodTestInput) -> dict[str, float]:
        """Normalize all submitted marker values into SI units."""
        normalized: dict[str, float] = {}
        for entry in blood_test.markers:
            definition = self._definitions.get(entry.marker_id)
            if definition is None:
                continue
            normalized[entry.marker_id] = round(self._normalize_value(entry, definition), 4)
        return normalized

    def derive_values(self, normalized_markers: dict[str, float]) -> dict[str, float]:
        """Calculate supported derived markers from normalized inputs."""
        derived_values: dict[str, float] = {}

        if {"glucose", "insulin"} <= normalized_markers.keys():
            derived_values["homa_ir"] = round(
                calculate_homa_ir(normalized_markers["glucose"], normalized_markers["insulin"]),
                2,
            )
        if {"ast", "alt"} <= normalized_markers.keys():
            derived_values["de_ritis_ratio"] = round(
                calculate_de_ritis(normalized_markers["ast"], normalized_markers["alt"]),
                2,
            )
        if {"total_cholesterol", "hdl"} <= normalized_markers.keys():
            derived_values["non_hdl"] = round(
                calculate_non_hdl(
                    normalized_markers["total_cholesterol"],
                    normalized_markers["hdl"],
                ),
                2,
            )

        return derived_values

    def analyze(self, blood_test: BloodTestInput) -> list[MarkerAnalysis]:
        """Analyze all submitted and derived markers."""
        normalized_markers = self.normalize_markers(blood_test)
        derived_values = self.derive_values(normalized_markers)
        entries = list(blood_test.markers) + [
            BloodMarkerInput(
                marker_id=marker_id,
                value=value,
                unit=self._definitions[marker_id].unit_si,
            )
            for marker_id, value in derived_values.items()
        ]

        results: list[MarkerAnalysis] = []
        for entry in entries:
            definition = self._definitions.get(entry.marker_id)
            if definition is None:
                continue
            results.append(self._analyze_single(entry, definition, blood_test.patient_sex))

        return sorted(results, key=lambda item: (item.marker_name.lower(), item.marker_id))

    def _analyze_single(
        self,
        entry: BloodMarkerInput,
        definition: MarkerDefinition,
        sex: str,
    ) -> MarkerAnalysis:
        normalized_value = self._normalize_value(entry, definition)
        reference = self._resolve_bounds(definition.reference_range, sex)
        optimal = self._resolve_bounds(definition.optimal_range, sex)
        status = self._classify_status(
            normalized_value,
            reference.min,
            reference.max,
            optimal.min,
            optimal.max,
        )
        interpretation = self._resolve_interpretation(definition, status)

        return MarkerAnalysis(
            marker_id=definition.id,
            marker_name=definition.name,
            value=round(normalized_value, 2),
            unit=definition.unit_si,
            reference_min=reference.min,
            reference_max=reference.max,
            optimal_min=optimal.min,
            optimal_max=optimal.max,
            status=status,
            flag=self._flag_for_status(status),
            affected_cascades=definition.mito_cascades,
            affected_genes=definition.mito_genes,
            affected_kegg_pathways=definition.kegg_pathways,
            mito_interpretation=interpretation.mito_impact,
            confidence=self._confidence_for_status(status),
        )

    def _normalize_value(self, entry: BloodMarkerInput, definition: MarkerDefinition) -> float:
        submitted_unit = entry.unit.strip().lower()
        si_unit = definition.unit_si.strip().lower()
        conventional_unit = definition.unit_conventional.strip().lower()
        if submitted_unit == si_unit:
            return entry.value
        if submitted_unit == conventional_unit:
            return entry.value * definition.conversion_factor
        return entry.value

    def _resolve_bounds(
        self,
        range_definition: ReferenceRange | OptimalRange,
        sex: str,
    ) -> RangeBounds:
        if range_definition.sex_specific:
            selected = range_definition.male if sex.upper() == "M" else range_definition.female
            if selected is not None:
                return selected
        return RangeBounds(min=range_definition.min, max=range_definition.max)

    def _resolve_interpretation(
        self,
        definition: MarkerDefinition,
        status: MarkerStatus,
    ) -> MarkerInterpretationDefinition:
        exact = definition.interpretations.get(status.value)
        if exact is not None:
            return exact

        if status in {MarkerStatus.CRITICALLY_LOW, MarkerStatus.LOW, MarkerStatus.SUBOPTIMAL_LOW}:
            return definition.interpretations.get("low", definition.interpretations["optimal"])
        if status in {
            MarkerStatus.CRITICALLY_HIGH,
            MarkerStatus.HIGH,
            MarkerStatus.SUBOPTIMAL_HIGH,
        }:
            return definition.interpretations.get("high", definition.interpretations["optimal"])
        return definition.interpretations["optimal"]

    def _classify_status(
        self,
        value: float,
        ref_min: float | None,
        ref_max: float | None,
        opt_min: float | None,
        opt_max: float | None,
    ) -> MarkerStatus:
        span = self._reference_span(ref_min, ref_max)
        critical_margin = span * 0.35

        if ref_min is not None and value < ref_min:
            return (
                MarkerStatus.CRITICALLY_LOW
                if value < ref_min - critical_margin
                else MarkerStatus.LOW
            )
        if ref_max is not None and value > ref_max:
            return (
                MarkerStatus.CRITICALLY_HIGH
                if value > ref_max + critical_margin
                else MarkerStatus.HIGH
            )
        if opt_min is not None and value < opt_min:
            return MarkerStatus.SUBOPTIMAL_LOW
        if opt_max is not None and value > opt_max:
            return MarkerStatus.SUBOPTIMAL_HIGH
        return MarkerStatus.OPTIMAL

    def _reference_span(self, ref_min: float | None, ref_max: float | None) -> float:
        if ref_min is not None and ref_max is not None:
            return max(ref_max - ref_min, max(abs(ref_max), abs(ref_min), 1.0) * 0.2)
        if ref_min is not None:
            return max(abs(ref_min), 1.0) * 0.3
        if ref_max is not None:
            return max(abs(ref_max), 1.0) * 0.3
        return 1.0

    def _flag_for_status(self, status: MarkerStatus) -> MarkerFlag:
        if status in {
            MarkerStatus.CRITICALLY_HIGH,
            MarkerStatus.HIGH,
            MarkerStatus.SUBOPTIMAL_HIGH,
        }:
            return "\u2191"
        if status in {MarkerStatus.CRITICALLY_LOW, MarkerStatus.LOW, MarkerStatus.SUBOPTIMAL_LOW}:
            return "\u2193"
        return "\u2713"

    def _confidence_for_status(self, status: MarkerStatus) -> MarkerConfidence:
        if status in {MarkerStatus.CRITICALLY_HIGH, MarkerStatus.CRITICALLY_LOW}:
            return "high"
        if status in {MarkerStatus.HIGH, MarkerStatus.LOW}:
            return "medium"
        return "high"


@lru_cache
def get_marker_engine() -> MarkerEngine:
    """Return the shared marker engine instance."""
    return MarkerEngine()
