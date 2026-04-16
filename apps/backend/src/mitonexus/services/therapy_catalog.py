from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace

from mitonexus.schemas.therapy import EvidenceLevel, TherapyCategory, TherapyRecommendation


@dataclass(frozen=True)
class TherapyProfile:
    therapy_id: str
    name: str
    category: TherapyCategory
    mechanism_summary: str
    detailed_mechanism: str
    dosage: str
    timing: str | None
    evidence_level: EvidenceLevel
    fda_status: str
    nct_ids: tuple[str, ...]
    source_pmids: tuple[str, ...]
    contraindications: tuple[str, ...] = ()


THERAPY_LIBRARY: dict[str, TherapyProfile] = {
    "berberine": TherapyProfile(
        therapy_id="berberine",
        name="Berberine",
        category=TherapyCategory.SUPPLEMENTATION,
        mechanism_summary="Improves glycemic control and AMPK signaling.",
        detailed_mechanism=(
            "Activates AMPK, reduces hepatic glucose output, and supports PDC-regulated "
            "substrate selection under insulin-resistant mitochondrial states."
        ),
        dosage="500 mg twice daily with meals",
        timing="Morning and evening meals",
        evidence_level=EvidenceLevel.B,
        fda_status="Dietary supplement",
        nct_ids=("NCT03385148",),
        source_pmids=("36110879", "38804789"),
        contraindications=(
            "Monitor for low glucose when combined with fasting or other glucose-lowering therapies.",
        ),
    ),
    "coq10": TherapyProfile(
        therapy_id="coq10",
        name="Coenzyme Q10",
        category=TherapyCategory.SUPPLEMENTATION,
        mechanism_summary="Supports electron transport chain redox transfer.",
        detailed_mechanism=(
            "Acts within the inner mitochondrial membrane as an electron carrier and can support "
            "cardiolipin stability, ETC throughput, and antioxidant buffering."
        ),
        dosage="100-200 mg daily",
        timing="With a fat-containing meal",
        evidence_level=EvidenceLevel.B,
        fda_status="Dietary supplement",
        nct_ids=("NCT05189977",),
        source_pmids=("31066976", "36602932"),
    ),
    "glycine_nac": TherapyProfile(
        therapy_id="glycine_nac",
        name="GlyNAC",
        category=TherapyCategory.SUPPLEMENTATION,
        mechanism_summary="Replenishes glutathione precursors and lowers oxidative burden.",
        detailed_mechanism=(
            "Provides glycine and cysteine substrate for glutathione synthesis, supporting Nrf2-linked "
            "redox balance and helping limit ROS-mediated damage to ETC proteins."
        ),
        dosage="Glycine 3-6 g plus NAC 600-1200 mg daily",
        timing="Split across 1-2 doses",
        evidence_level=EvidenceLevel.B,
        fda_status="Dietary supplement combination",
        nct_ids=("NCT05158868",),
        source_pmids=("35975308", "38549731"),
    ),
    "methyl_b12": TherapyProfile(
        therapy_id="methyl_b12",
        name="Methylcobalamin",
        category=TherapyCategory.SUPPLEMENTATION,
        mechanism_summary="Supports one-carbon metabolism and homocysteine clearance.",
        detailed_mechanism=(
            "Supports methionine synthase activity and downstream methylation capacity, helping reduce "
            "homocysteine-linked redox stress and preserve mitochondrial membrane potential."
        ),
        dosage="1000 mcg daily",
        timing="Morning",
        evidence_level=EvidenceLevel.C,
        fda_status="Dietary supplement",
        nct_ids=(),
        source_pmids=("31234679", "39510126"),
    ),
    "methyl_folate": TherapyProfile(
        therapy_id="methyl_folate",
        name="L-methylfolate",
        category=TherapyCategory.SUPPLEMENTATION,
        mechanism_summary="Supports methylation flux and transsulfuration balance.",
        detailed_mechanism=(
            "Supports remethylation of homocysteine, helps maintain SAM-dependent signaling, and reduces "
            "pressure on sulfur handling pathways tied to mitochondrial oxidative damage."
        ),
        dosage="1-5 mg daily",
        timing="Morning",
        evidence_level=EvidenceLevel.C,
        fda_status="Medical food / supplement depending formulation",
        nct_ids=(),
        source_pmids=("31234679", "39510126"),
    ),
    "p5p_b6": TherapyProfile(
        therapy_id="p5p_b6",
        name="Pyridoxal-5-phosphate",
        category=TherapyCategory.SUPPLEMENTATION,
        mechanism_summary="Supports transsulfuration enzyme function.",
        detailed_mechanism=(
            "Supports CBS and related B6-dependent enzymes, reinforcing transsulfuration and glutathione "
            "substrate generation when homocysteine pressure is high."
        ),
        dosage="25-50 mg daily",
        timing="With food",
        evidence_level=EvidenceLevel.C,
        fda_status="Dietary supplement",
        nct_ids=(),
        source_pmids=("31234679",),
    ),
    "tmg": TherapyProfile(
        therapy_id="tmg",
        name="Trimethylglycine",
        category=TherapyCategory.SUPPLEMENTATION,
        mechanism_summary="Provides alternate methyl donation for homocysteine recycling.",
        detailed_mechanism=(
            "Supports BHMT-mediated remethylation of homocysteine and can lower one-carbon stress that "
            "feeds mitochondrial ROS production."
        ),
        dosage="500-1000 mg daily",
        timing="Morning",
        evidence_level=EvidenceLevel.C,
        fda_status="Dietary supplement",
        nct_ids=(),
        source_pmids=("29995818",),
    ),
    "omega3": TherapyProfile(
        therapy_id="omega3",
        name="Omega-3 fatty acids",
        category=TherapyCategory.SUPPLEMENTATION,
        mechanism_summary="Supports membrane remodeling and inflammatory tone.",
        detailed_mechanism=(
            "Can improve mitochondrial membrane composition, modulate inflammatory lipid mediators, and "
            "support oxidative resilience across MAMs, ferroptosis, and cardiolipin-linked stress."
        ),
        dosage="1-2 g EPA+DHA daily",
        timing="With meals",
        evidence_level=EvidenceLevel.B,
        fda_status="Dietary supplement",
        nct_ids=("NCT05293535",),
        source_pmids=("34372670", "38133837"),
        contraindications=("Use caution with bleeding disorders or anticoagulant therapy.",),
    ),
    "selenium": TherapyProfile(
        therapy_id="selenium",
        name="Selenium",
        category=TherapyCategory.SUPPLEMENTATION,
        mechanism_summary="Supports GPX4 and antioxidant enzyme systems.",
        detailed_mechanism=(
            "Supports selenoproteins involved in peroxide detoxification and ferroptosis control, especially "
            "when oxidative stress markers or thyroid-linked mitochondrial strain are present."
        ),
        dosage="100-200 mcg daily",
        timing="With food",
        evidence_level=EvidenceLevel.C,
        fda_status="Dietary supplement",
        nct_ids=(),
        source_pmids=("33296867",),
    ),
    "sulforaphane": TherapyProfile(
        therapy_id="sulforaphane",
        name="Sulforaphane",
        category=TherapyCategory.SUPPLEMENTATION,
        mechanism_summary="Activates Nrf2-mediated stress response pathways.",
        detailed_mechanism=(
            "Promotes Nrf2/Keap1 signaling, increasing transcription of antioxidant and detoxification genes "
            "that help buffer oxidative stress and support mitochondrial proteostasis."
        ),
        dosage="20-40 mg sulforaphane daily",
        timing="Morning",
        evidence_level=EvidenceLevel.C,
        fda_status="Dietary supplement",
        nct_ids=("NCT04824326",),
        source_pmids=("32179642",),
    ),
    "urolithin_a": TherapyProfile(
        therapy_id="urolithin_a",
        name="Urolithin A",
        category=TherapyCategory.TARGETED_MITO_DRUGS,
        mechanism_summary="Supports mitophagy and mitochondrial quality control.",
        detailed_mechanism=(
            "Promotes mitophagy and mitochondrial turnover, supporting recovery in dynamics, OPA1, and "
            "quality-control pathways under chronic metabolic stress."
        ),
        dosage="500-1000 mg daily",
        timing="Morning",
        evidence_level=EvidenceLevel.B,
        fda_status="Dietary supplement / investigational wellness ingredient",
        nct_ids=("NCT05569681",),
        source_pmids=("37076147", "39910532"),
    ),
    "nad_precursors": TherapyProfile(
        therapy_id="nad_precursors",
        name="NAD+ precursor support",
        category=TherapyCategory.SUPPLEMENTATION,
        mechanism_summary="Supports NAD-dependent mitochondrial enzymes.",
        detailed_mechanism=(
            "Supports NAD-dependent dehydrogenases and sirtuin activity, with downstream effects on redox "
            "balance, mitochondrial protein acetylation, and metabolic flexibility."
        ),
        dosage="500-1000 mg daily",
        timing="Morning",
        evidence_level=EvidenceLevel.B,
        fda_status="Dietary supplement",
        nct_ids=("NCT05419570",),
        source_pmids=("36155782", "40211822"),
    ),
    "vitamin_d_repletion": TherapyProfile(
        therapy_id="vitamin_d_repletion",
        name="Vitamin D repletion",
        category=TherapyCategory.SUPPLEMENTATION,
        mechanism_summary="Supports immune regulation and membrane resilience.",
        detailed_mechanism=(
            "Helps regulate inflammatory signaling, calcium handling, and redox tone, particularly when "
            "vitamin D-linked membrane and signaling deficits are present."
        ),
        dosage="2000-4000 IU daily, titrated to labs",
        timing="With a meal",
        evidence_level=EvidenceLevel.B,
        fda_status="Dietary supplement",
        nct_ids=("NCT05601089",),
        source_pmids=("35822476",),
        contraindications=(
            "Avoid escalation when vitamin D is already high unless supervised clinically.",
        ),
    ),
    "magnesium": TherapyProfile(
        therapy_id="magnesium",
        name="Magnesium glycinate",
        category=TherapyCategory.SUPPLEMENTATION,
        mechanism_summary="Supports ATP handling, membrane stability, and glucose metabolism.",
        detailed_mechanism=(
            "Acts as a cofactor for ATP-dependent enzymes, can support ion gradient stability, and may help "
            "buffer stress across MCU, thyroid, and glycemic-control pathways."
        ),
        dosage="200-400 mg elemental magnesium daily",
        timing="Evening",
        evidence_level=EvidenceLevel.B,
        fda_status="Dietary supplement",
        nct_ids=(),
        source_pmids=("35370874",),
    ),
    "potassium_repletion": TherapyProfile(
        therapy_id="potassium_repletion",
        name="Potassium repletion",
        category=TherapyCategory.SUPPLEMENTATION,
        mechanism_summary="Restores membrane polarization and excitability support.",
        detailed_mechanism=(
            "Supports membrane potential, muscular function, and mitochondrial calcium handling when potassium "
            "deficit is limiting energetic stability."
        ),
        dosage="Dose individualized to labs",
        timing="Split doses with food",
        evidence_level=EvidenceLevel.C,
        fda_status="OTC / prescription depending formulation",
        nct_ids=(),
        source_pmids=("30290927",),
        contraindications=(
            "Avoid unsupervised repletion when potassium is already high or renal reserve is reduced.",
        ),
    ),
    "zone2_training": TherapyProfile(
        therapy_id="zone2_training",
        name="Zone 2 aerobic training",
        category=TherapyCategory.EXERCISE,
        mechanism_summary="Improves mitochondrial density and oxidative capacity.",
        detailed_mechanism=(
            "Supports mitochondrial biogenesis, capillary density, and fat oxidation while usually remaining "
            "tolerable in patients with moderate metabolic or mitochondrial strain."
        ),
        dosage="30-45 minutes 3-5 times weekly",
        timing="Most days, adjusted to recovery",
        evidence_level=EvidenceLevel.B,
        fda_status="Lifestyle intervention",
        nct_ids=("NCT05484583",),
        source_pmids=("36884502",),
        contraindications=(
            "Scale carefully if severe anemia, unstable cardiopulmonary symptoms, or acute illness are present.",
        ),
    ),
    "resistance_training": TherapyProfile(
        therapy_id="resistance_training",
        name="Resistance training",
        category=TherapyCategory.EXERCISE,
        mechanism_summary="Improves muscle mitochondrial reserve and insulin sensitivity.",
        detailed_mechanism=(
            "Builds muscle mass, improves glucose disposal, and supports mitophagy and fusion-fission balance "
            "through repeated energetic adaptation."
        ),
        dosage="2-4 sessions weekly",
        timing="Non-consecutive days preferred",
        evidence_level=EvidenceLevel.B,
        fda_status="Lifestyle intervention",
        nct_ids=("NCT05660044",),
        source_pmids=("37711939",),
    ),
    "strength_training": TherapyProfile(
        therapy_id="strength_training",
        name="Strength-focused resistance training",
        category=TherapyCategory.EXERCISE,
        mechanism_summary="Supports anabolic signaling and mitochondrial reserve.",
        detailed_mechanism=(
            "Supports muscle mitochondrial content, improves insulin sensitivity, and helps recover low-anabolic "
            "states reflected in hormone and creatinine patterns."
        ),
        dosage="3 sessions weekly",
        timing="Daytime with recovery between sessions",
        evidence_level=EvidenceLevel.B,
        fda_status="Lifestyle intervention",
        nct_ids=("NCT05660044",),
        source_pmids=("37711939",),
    ),
    "time_restricted_eating": TherapyProfile(
        therapy_id="time_restricted_eating",
        name="Time-restricted eating",
        category=TherapyCategory.DIET,
        mechanism_summary="Improves metabolic flexibility and circadian mitochondrial coordination.",
        detailed_mechanism=(
            "Supports AMPK and sirtuin signaling, reduces late-day glucose exposure, and may improve hepatic "
            "and skeletal muscle mitochondrial efficiency when matched to adequate total intake."
        ),
        dosage="8-10 hour eating window",
        timing="Earlier daytime window preferred",
        evidence_level=EvidenceLevel.B,
        fda_status="Lifestyle intervention",
        nct_ids=("NCT05393362",),
        source_pmids=("36314294", "39102857"),
        contraindications=(
            "Avoid aggressive restriction when glucose is low, energy availability is poor, or disordered eating risk is present.",
        ),
    ),
    "fiber_intake": TherapyProfile(
        therapy_id="fiber_intake",
        name="Soluble fiber emphasis",
        category=TherapyCategory.DIET,
        mechanism_summary="Supports lipid and glycemic handling.",
        detailed_mechanism=(
            "Improves postprandial glucose and lipid handling, reduces hepatic substrate pressure, and supports "
            "short-chain-fatty-acid signaling linked to mitochondrial resilience."
        ),
        dosage="25-35 g total fiber daily",
        timing="Distributed across meals",
        evidence_level=EvidenceLevel.B,
        fda_status="Lifestyle intervention",
        nct_ids=(),
        source_pmids=("35512988",),
    ),
    "post_meal_walks": TherapyProfile(
        therapy_id="post_meal_walks",
        name="Post-meal walking",
        category=TherapyCategory.EXERCISE,
        mechanism_summary="Blunts postprandial glucose and insulin excursions.",
        detailed_mechanism=(
            "Light movement after meals increases glucose disposal and reduces acute mitochondrial substrate "
            "overload in insulin-resistant states."
        ),
        dosage="10-15 minutes after major meals",
        timing="Within 30 minutes of meals",
        evidence_level=EvidenceLevel.B,
        fda_status="Lifestyle intervention",
        nct_ids=(),
        source_pmids=("36584561",),
    ),
    "sleep_optimization": TherapyProfile(
        therapy_id="sleep_optimization",
        name="Sleep optimization",
        category=TherapyCategory.LIFESTYLE,
        mechanism_summary="Supports circadian repair and mitokine recovery.",
        detailed_mechanism=(
            "Improves circadian coordination of mitochondrial biogenesis, hormone rhythms, inflammation control, "
            "and recovery from oxidative stress."
        ),
        dosage="7.5-9 hours nightly with consistent timing",
        timing="Nightly",
        evidence_level=EvidenceLevel.B,
        fda_status="Lifestyle intervention",
        nct_ids=(),
        source_pmids=("35768224",),
    ),
    "sleep_recovery": TherapyProfile(
        therapy_id="sleep_recovery",
        name="Sleep recovery",
        category=TherapyCategory.LIFESTYLE,
        mechanism_summary="Improves recovery from inflammatory and oxidative stress.",
        detailed_mechanism=(
            "Targets sleep debt and recovery capacity to reduce mtROS burden, inflammatory tone, and autonomic "
            "stress that amplify abnormal marker patterns."
        ),
        dosage="Prioritize sleep extension for 2-4 weeks",
        timing="Nightly",
        evidence_level=EvidenceLevel.B,
        fda_status="Lifestyle intervention",
        nct_ids=(),
        source_pmids=("35768224",),
    ),
    "hydration": TherapyProfile(
        therapy_id="hydration",
        name="Hydration strategy",
        category=TherapyCategory.LIFESTYLE,
        mechanism_summary="Reduces hemoconcentration and renal stress.",
        detailed_mechanism=(
            "Supports renal clearance, plasma volume, and electrolyte balance when hemoconcentration, urea, "
            "or osmotic stress patterns are present."
        ),
        dosage="Target urine-pale hydration status",
        timing="Across the day",
        evidence_level=EvidenceLevel.C,
        fda_status="Lifestyle intervention",
        nct_ids=(),
        source_pmids=("32718649",),
    ),
    "creatine": TherapyProfile(
        therapy_id="creatine",
        name="Creatine monohydrate",
        category=TherapyCategory.SUPPLEMENTATION,
        mechanism_summary="Supports phosphocreatine buffering and muscular bioenergetics.",
        detailed_mechanism=(
            "Improves phosphagen reserve, supports muscular high-energy phosphate buffering, and can complement "
            "mitochondrial reserve building in low-muscle-mass states."
        ),
        dosage="3-5 g daily",
        timing="Any time, consistently",
        evidence_level=EvidenceLevel.B,
        fda_status="Dietary supplement",
        nct_ids=("NCT05501067",),
        source_pmids=("38576989",),
    ),
}


def humanize_therapy_id(therapy_id: str) -> str:
    """Convert a therapy identifier into a human-readable label."""
    return therapy_id.replace("_", " ").strip().title()


def infer_category(therapy_id: str) -> TherapyCategory:
    """Best-effort category for uncatalogued therapy ids."""
    if therapy_id.endswith("_training") or "walk" in therapy_id or therapy_id == "exercise":
        return TherapyCategory.EXERCISE
    if (
        therapy_id.endswith("_eating")
        or "diet" in therapy_id
        or therapy_id
        in {
            "fiber_intake",
            "energy_availability",
            "protein_adequacy",
            "fructose_reduction",
            "meal_timing",
        }
    ):
        return TherapyCategory.DIET
    if (
        therapy_id.endswith("_review")
        or therapy_id.endswith("_screen")
        or therapy_id.endswith("_referral")
    ):
        return TherapyCategory.PHARMACOTHERAPY
    if therapy_id in {"urolithin_a", "elamipretide", "mitoq", "bam15"}:
        return TherapyCategory.TARGETED_MITO_DRUGS
    if therapy_id in {"sleep_optimization", "sleep_recovery", "hydration", "stress_reduction"}:
        return TherapyCategory.LIFESTYLE
    return TherapyCategory.SUPPLEMENTATION


def get_therapy_profile(therapy_id: str) -> TherapyProfile:
    """Return a curated therapy profile or a reasonable fallback."""
    if therapy_id in THERAPY_LIBRARY:
        return THERAPY_LIBRARY[therapy_id]

    category = infer_category(therapy_id)
    label = humanize_therapy_id(therapy_id)
    return TherapyProfile(
        therapy_id=therapy_id,
        name=label,
        category=category,
        mechanism_summary=f"{label} may support the affected mitochondrial pathways in a supportive role.",
        detailed_mechanism=(
            f"{label} is currently represented as a fallback therapy entry. It should be reviewed against "
            "the specific cascade and marker context before clinical use."
        ),
        dosage="Individualize to clinical context",
        timing=None,
        evidence_level=EvidenceLevel.D,
        fda_status="Supportive / requires clinician review",
        nct_ids=(),
        source_pmids=(),
        contraindications=(
            "Clinical review recommended because this therapy is not yet fully curated.",
        ),
    )


def check_interactions(therapy_ids: Iterable[str]) -> dict[str, object]:
    """Return simple interaction heuristics for a set of therapy ids."""
    therapy_set = set(therapy_ids)
    interactions: list[dict[str, str]] = []

    if {"berberine", "time_restricted_eating"} <= therapy_set or {
        "berberine",
        "post_meal_walks",
    } <= therapy_set:
        interactions.append(
            {
                "severity": "moderate",
                "message": "Combined glucose-lowering strategies may require glucose monitoring.",
            }
        )

    if {"potassium_repletion", "electrolyte_balance"} <= therapy_set:
        interactions.append(
            {
                "severity": "moderate",
                "message": "Electrolyte repletion plans should be coordinated to avoid overcorrection.",
            }
        )

    if not interactions:
        return {"risk_level": "low", "interactions": []}
    return {"risk_level": "moderate", "interactions": interactions}


def resolve_contraindications(
    therapy_id: str,
    patient_profile: dict[str, object],
    abnormal_markers: dict[str, float | str],
) -> list[str]:
    """Return contextual contraindications for a therapy."""
    profile = get_therapy_profile(therapy_id)
    contraindications = list(profile.contraindications)

    if therapy_id == "potassium_repletion" and abnormal_markers.get("potassium_status") in {
        "high",
        "critically_high",
        "suboptimal_high",
    }:
        contraindications.append("Avoid potassium repletion when potassium is already elevated.")

    if therapy_id == "vitamin_d_repletion" and abnormal_markers.get("vitamin_d_status") in {
        "high",
        "critically_high",
        "suboptimal_high",
    }:
        contraindications.append("Avoid escalating vitamin D when current levels are already high.")

    if therapy_id == "time_restricted_eating" and abnormal_markers.get("glucose_status") in {
        "low",
        "critically_low",
        "suboptimal_low",
    }:
        contraindications.append(
            "Short feeding windows may worsen symptomatic low-glucose patterns."
        )

    age = patient_profile.get("age")
    if isinstance(age, int) and age >= 75 and therapy_id in {"zone2_training", "strength_training"}:
        contraindications.append("Start with a conservative progression in older adults.")

    return sorted(set(contraindications))


def build_recommendation(
    therapy_id: str,
    *,
    priority_score: float,
    targets_cascades: list[str],
    corrects_markers: list[str],
    contraindications: list[str] | None = None,
) -> TherapyRecommendation:
    """Convert a therapy profile into a structured recommendation."""
    profile = get_therapy_profile(therapy_id)
    return TherapyRecommendation(
        therapy_id=profile.therapy_id,
        name=profile.name,
        category=profile.category,
        mechanism_summary=profile.mechanism_summary,
        detailed_mechanism=profile.detailed_mechanism,
        dosage=profile.dosage,
        timing=profile.timing,
        evidence_level=profile.evidence_level,
        fda_status=profile.fda_status,
        nct_ids=list(profile.nct_ids),
        source_pmids=list(profile.source_pmids),
        targets_cascades=targets_cascades,
        corrects_markers=corrects_markers,
        contraindications=sorted(set(contraindications or profile.contraindications)),
        priority_score=round(priority_score, 2),
    )


def with_extra_pmids(profile: TherapyProfile, pmids: Iterable[str]) -> TherapyProfile:
    """Return a therapy profile with additional literature references."""
    merged_pmids = tuple(dict.fromkeys([*profile.source_pmids, *pmids]))
    return replace(profile, source_pmids=merged_pmids)
