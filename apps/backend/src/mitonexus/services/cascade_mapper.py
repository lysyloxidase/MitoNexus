from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from mitonexus.schemas.blood_marker import MarkerAnalysis, MarkerStatus
from mitonexus.schemas.cascade import CascadeAssessment, CascadeStatus


@dataclass(frozen=True)
class CascadeDefinition:
    cascade_id: str
    name: str
    genes: tuple[str, ...]
    pathway: str | None
    targets: tuple[str, ...]


CASCADE_LIBRARY: tuple[CascadeDefinition, ...] = (
    CascadeDefinition(
        "pgc1a_sirt1_ampk",
        "PGC-1alpha / SIRT1 / AMPK",
        ("PPARGC1A", "SIRT1", "PRKAA1"),
        "hsa04152",
        ("zone2_training", "berberine", "coq10", "sleep_extension"),
    ),
    CascadeDefinition(
        "mtorc1",
        "mTORC1",
        ("MTOR", "RPTOR", "AKT1"),
        "hsa04150",
        ("time_restricted_eating", "berberine", "resistance_training"),
    ),
    CascadeDefinition(
        "mtorc2_akt",
        "mTORC2 / AKT",
        ("RICTOR", "AKT1", "IRS1"),
        "hsa04150",
        ("protein_distribution", "strength_training", "magnesium"),
    ),
    CascadeDefinition(
        "nrf2_keap1",
        "Nrf2 / Keap1",
        ("NFE2L2", "KEAP1", "HMOX1"),
        "hsa04068",
        ("nac", "sulforaphane", "selenium"),
    ),
    CascadeDefinition(
        "hif1a_retrograde",
        "HIF-1alpha Retrograde Signaling",
        ("HIF1A", "VEGFA", "PDK1"),
        "hsa04066",
        ("iron_repletion", "sleep_apnea_screen", "aerobic_conditioning"),
    ),
    CascadeDefinition(
        "uprmt",
        "UPRmt / ATF4-ATF5",
        ("ATF4", "ATF5", "HSPD1"),
        "hsa04141",
        ("taurine", "glycine_nac", "mitochondrial_protein_support"),
    ),
    CascadeDefinition(
        "cgas_sting",
        "cGAS-STING (mtDNA)",
        ("MB21D1", "TMEM173", "IFNB1"),
        "hsa04623",
        ("omega3", "sleep_optimization", "polyphenols"),
    ),
    CascadeDefinition(
        "wnt_beta_catenin",
        "Wnt / beta-catenin",
        ("CTNNB1", "LRP6", "GSK3B"),
        "hsa04310",
        ("vitamin_d_repletion", "strength_training", "magnesium"),
    ),
    CascadeDefinition(
        "notch",
        "Notch",
        ("NOTCH1", "DLL1", "HES1"),
        "hsa04330",
        ("circadian_alignment", "protein_adequacy", "zinc"),
    ),
    CascadeDefinition(
        "hippo_yap",
        "Hippo / YAP",
        ("YAP1", "LATS1", "TEAD1"),
        "hsa04390",
        ("resistance_training", "glycemic_control", "omega3"),
    ),
    CascadeDefinition(
        "fgf21",
        "FGF21",
        ("FGF21", "PPARA", "KLB"),
        "hsa04979",
        ("fasting_window", "omega3", "choline"),
    ),
    CascadeDefinition(
        "gdf15",
        "GDF15",
        ("GDF15", "GFRAL", "ATF4"),
        "hsa04350",
        ("b_complex", "mitochondrial_antioxidants", "sleep_recovery"),
    ),
    CascadeDefinition(
        "mitokines",
        "MOTS-c / Humanin / SHMOOSE",
        ("MT-RNR1", "MT-RNR2", "MOTS-C"),
        "hsa00190",
        ("exercise", "berberine", "creatine"),
    ),
    CascadeDefinition(
        "ferroptosis_gpx4",
        "Ferroptosis / GPX4",
        ("GPX4", "SLC7A11", "ACSL4"),
        "hsa04216",
        ("selenium", "nac", "omega3_balance"),
    ),
    CascadeDefinition(
        "mcu_complex",
        "MCU Complex",
        ("MCU", "MICU1", "MICU2"),
        "hsa04020",
        ("magnesium", "potassium_repletion", "electrolyte_balance"),
    ),
    CascadeDefinition(
        "mams",
        "MAMs",
        ("MFN2", "VDAC1", "ITPR1"),
        "hsa04152",
        ("omega3", "phosphatidylcholine", "sleep"),
    ),
    CascadeDefinition(
        "cardiolipin_tafazzin",
        "Cardiolipin / TAFAZZIN",
        ("TAZ", "CRLS1", "PLA2G6"),
        "hsa00564",
        ("coq10", "linoleic_acid_balance", "l_carnitine"),
    ),
    CascadeDefinition(
        "sirt2_5",
        "SIRT2-5",
        ("SIRT2", "SIRT3", "SIRT5"),
        "hsa01200",
        ("nad_precursors", "fasting_window", "exercise"),
    ),
    CascadeDefinition(
        "nad_metabolism",
        "NAD+ Metabolism",
        ("NAMPT", "NMNAT1", "PARP1"),
        "hsa00760",
        ("niacinamide", "riboflavin", "glycine"),
    ),
    CascadeDefinition(
        "protein_import",
        "Protein Import",
        ("TOMM20", "TIMM23", "DNAJC19"),
        "hsa04141",
        ("taurine", "coq10", "mitochondrial_chaperone_support"),
    ),
    CascadeDefinition(
        "oma1_yme1l_opa1",
        "OMA1 / YME1L / OPA1",
        ("OMA1", "YME1L1", "OPA1"),
        "hsa04140",
        ("coq10", "urolithin_a", "zone2_training"),
    ),
    CascadeDefinition(
        "mitophagy_bnip3_nix_fundc1",
        "Mitophagy (BNIP3 / NIX / FUNDC1)",
        ("BNIP3", "BNIP3L", "FUNDC1"),
        "hsa04137",
        ("exercise", "sleep_hypoxia_screen", "urolithin_a"),
    ),
    CascadeDefinition(
        "dynamics_drp1_mfn_opa1",
        "Dynamics (DRP1 / MFN / OPA1)",
        ("DNM1L", "MFN1", "MFN2", "OPA1"),
        "hsa04140",
        ("omega3", "exercise", "coq10"),
    ),
    CascadeDefinition(
        "micos",
        "MICOS",
        ("MIC60", "MIC19", "CHCHD3"),
        "hsa00190",
        ("coq10", "phospholipid_support", "cardiolipin_support"),
    ),
    CascadeDefinition(
        "pdc_regulation",
        "PDC Regulation",
        ("PDHA1", "PDK4", "PDP1"),
        "hsa00620",
        ("thiamine", "lipoic_acid", "glycemic_control"),
    ),
    CascadeDefinition(
        "transsulfuration",
        "Transsulfuration",
        ("CBS", "CTH", "SQOR", "MTHFR"),
        "hsa00270",
        ("methyl_folate", "methyl_b12", "p5p_b6", "tmg"),
    ),
)

STATUS_WEIGHTS: dict[MarkerStatus, int] = {
    MarkerStatus.OPTIMAL: 0,
    MarkerStatus.SUBOPTIMAL_LOW: 1,
    MarkerStatus.SUBOPTIMAL_HIGH: 1,
    MarkerStatus.LOW: 2,
    MarkerStatus.HIGH: 2,
    MarkerStatus.CRITICALLY_LOW: 3,
    MarkerStatus.CRITICALLY_HIGH: 3,
}


class CascadeMapper:
    """Map marker patterns to mitochondrial signaling cascades."""

    def assess_cascades(self, marker_results: list[MarkerAnalysis]) -> list[CascadeAssessment]:
        grouped: dict[str, list[MarkerAnalysis]] = defaultdict(list)
        for marker_result in marker_results:
            for cascade_id in marker_result.affected_cascades:
                grouped[cascade_id].append(marker_result)

        assessments: list[CascadeAssessment] = []
        for definition in CASCADE_LIBRARY:
            contributing = grouped.get(definition.cascade_id, [])
            abnormal = [result for result in contributing if result.status != MarkerStatus.OPTIMAL]
            assessments.append(
                CascadeAssessment(
                    cascade_id=definition.cascade_id,
                    name=definition.name,
                    status=self._classify_cascade(abnormal),
                    contributing_markers=[result.marker_id for result in abnormal],
                    affected_genes=sorted(
                        {
                            *definition.genes,
                            *(gene for result in abnormal for gene in result.affected_genes),
                        }
                    ),
                    kegg_pathway_id=definition.pathway,
                    impact_explanation=self._build_explanation(definition.name, abnormal),
                    therapeutic_targets=list(definition.targets),
                )
            )

        return assessments

    def _classify_cascade(self, abnormal_markers: list[MarkerAnalysis]) -> CascadeStatus:
        if not abnormal_markers:
            return CascadeStatus.OPTIMAL

        severity = sum(STATUS_WEIGHTS[result.status] for result in abnormal_markers)
        if severity >= 6:
            return CascadeStatus.SEVERELY_AFFECTED
        if severity >= 3:
            return CascadeStatus.MODERATELY_AFFECTED
        return CascadeStatus.MILDLY_AFFECTED

    def _build_explanation(self, cascade_name: str, abnormal_markers: list[MarkerAnalysis]) -> str:
        if not abnormal_markers:
            return f"{cascade_name} has no abnormal contributing markers in this panel."

        marker_names = ", ".join(result.marker_name for result in abnormal_markers[:4])
        if len(abnormal_markers) > 4:
            marker_names = f"{marker_names}, and others"
        return f"{marker_names} collectively indicate pressure on {cascade_name}."
