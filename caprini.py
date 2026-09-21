#!/usr/bin/env python3
"""Caprini VTE risk score calculator.

This module implements the factor weights reproduced in the CHEST 2012
nonorthopedic-surgery guideline (Caprini RAM table) and maps the resulting
score to that guideline's general/abdominal-pelvic surgical VTE risk strata.

The score is a risk-assessment aid, not a diagnosis or prescribing engine.
Prophylaxis guidance is intentionally conditional and population-scoped.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

RISK_FACTORS: List[Tuple[str, str, int]] = [
    # 1 point each
    ("age_41_60", "Age 41–60 years", 1),
    ("minor_surgery_lt_45min", "Minor surgery (<45 min)", 1),
    ("bmi_gt_25", "BMI >25 kg/m²", 1),
    ("swollen_legs", "Swollen legs (current)", 1),
    ("varicose_veins", "Varicose veins", 1),
    ("pregnancy_or_postpartum", "Pregnancy or postpartum", 1),
    ("recurrent_miscarriage", "History of unexplained/recurrent spontaneous abortion", 1),
    ("oral_contraceptives_or_hrt", "Oral contraceptives or hormone replacement therapy", 1),
    ("sepsis_lt_1mo", "Sepsis (<1 month)", 1),
    ("serious_lung_disease_lt_1mo", "Serious lung disease, including pneumonia (<1 month)", 1),
    ("abnormal_pulmonary_function", "Abnormal pulmonary function", 1),
    ("acute_mi", "Acute myocardial infarction (<1 month)", 1),
    ("chf_lt_1mo", "Congestive heart failure (<1 month)", 1),
    ("inflammatory_bowel_disease", "History of inflammatory bowel disease", 1),
    ("medical_patient_bed_rest", "Medical patient currently at bed rest", 1),
    # 2 points each
    ("age_61_74", "Age 61–74 years", 2),
    ("arthroscopic_surgery", "Arthroscopic surgery", 2),
    ("major_open_surgery_gt_45min", "Major open surgery (>45 min)", 2),
    ("laparoscopic_surgery_gt_45min", "Laparoscopic surgery (>45 min)", 2),
    ("malignancy", "Malignancy (present or previous)", 2),
    ("bed_rest_gt_72h", "Confined to bed (>72 h)", 2),
    ("immobilizing_plaster_cast", "Immobilizing plaster cast", 2),
    ("central_venous_access", "Central venous access", 2),
    # 3 points each
    ("age_75_plus", "Age ≥75 years", 3),
    ("history_of_vte", "History of VTE (DVT/PE)", 3),
    ("family_history_of_vte", "Family history of VTE", 3),
    ("factor_v_leiden", "Factor V Leiden", 3),
    ("prothrombin_20210a", "Prothrombin 20210A", 3),
    ("lupus_anticoagulant", "Lupus anticoagulant", 3),
    ("anticardiolipin_antibodies", "Anticardiolipin antibodies", 3),
    ("elevated_homocysteine", "Elevated serum homocysteine", 3),
    ("hit", "Heparin-induced thrombocytopenia", 3),
    ("other_thrombophilia", "Other congenital/acquired thrombophilia", 3),
    # 5 points each
    ("stroke_lt_1mo", "Stroke (<1 month)", 5),
    ("multiple_trauma_lt_1mo", "Multiple/serious trauma (<1 month)", 5),
    ("elective_lea", "Elective major lower-extremity arthroplasty", 5),
    ("hip_pelvis_leg_fracture_lt_1mo", "Hip, pelvis, or leg fracture (<1 month)", 5),
    ("acute_spinal_cord_injury_lt_1mo", "Acute spinal cord injury with paralysis (<1 month)", 5),
]

FACTOR_POINTS: Dict[str, int] = {key: points for key, _, points in RISK_FACTORS}
FACTOR_LABELS: Dict[str, str] = {key: label for key, label, _ in RISK_FACTORS}
AGE_KEYS = {"age_41_60", "age_61_74", "age_75_plus"}

# CHEST 2012 AT9 estimated baseline symptomatic VTE risk strata for general and
# abdominal-pelvic surgery in the absence of prophylaxis.
TIERS = [
    (0, "Very Low Risk", 0.005),
    (2, "Low Risk", 0.015),
    (4, "Moderate Risk", 0.030),
    (float("inf"), "High Risk", 0.060),
]

PROPHYLAXIS_RECOMMENDATIONS = {
    "Very Low Risk": [
        "Early ambulation; no specific pharmacologic or mechanical prophylaxis is recommended for general/abdominal-pelvic surgery.",
    ],
    "Low Risk": [
        "Mechanical prophylaxis, preferably intermittent pneumatic compression (IPC), is suggested for general/abdominal-pelvic surgery.",
    ],
    "Moderate Risk": [
        "If major-bleeding risk is not high: LMWH, low-dose unfractionated heparin (LDUH), or mechanical prophylaxis (preferably IPC) may be used.",
        "If major-bleeding risk is high or bleeding consequences would be severe: use mechanical prophylaxis (preferably IPC) until bleeding risk decreases.",
    ],
    "High Risk": [
        "If major-bleeding risk is not high: pharmacologic prophylaxis with LMWH or LDUH is recommended; adding mechanical prophylaxis (IPC or elastic stockings) is suggested.",
        "If major-bleeding risk is high or bleeding consequences would be severe: use mechanical prophylaxis (preferably IPC) until bleeding risk decreases and pharmacologic prophylaxis can be considered.",
    ],
}

BLEEDING_RISK_CONSIDERATIONS = [
    "Assess major-bleeding risk and the consequences of bleeding before selecting prophylaxis.",
    "The prophylaxis mapping in this tool is scoped to CHEST 2012 general/abdominal-pelvic surgical recommendations; other surgical populations require population-specific guidance.",
    "Inferior vena cava filters are not recommended for primary VTE prevention in general/abdominal-pelvic surgical patients.",
]

NON_GENERAL_SURGERY_SCOPE_KEYS = {
    "arthroscopic_surgery",
    "elective_lea",
    "hip_pelvis_leg_fracture_lt_1mo",
    "acute_spinal_cord_injury_lt_1mo",
    "multiple_trauma_lt_1mo",
    "medical_patient_bed_rest",
}


def _is_positive(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value >= 1
    return str(value).strip().lower() in {"1", "true", "yes", "y", "present"}


def _parse_age(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        age = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("age must be numeric") from exc
    if age < 0 or age > 130:
        raise ValueError("age must be between 0 and 130 years")
    return age


def _age_key(age: float) -> Optional[str]:
    if age >= 75:
        return "age_75_plus"
    if age >= 61:
        return "age_61_74"
    if age >= 41:
        return "age_41_60"
    return None


def calculate_score(factors: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate a Caprini score from a mapping of factor keys to values.

    A numeric ``age`` takes precedence over any explicit age-bracket flags.
    Without ``age``, at most one explicit age-bracket flag may be positive.
    Unknown keys are ignored to preserve compatibility with CSV rows that
    include non-scoring columns.
    """
    if not isinstance(factors, dict):
        raise TypeError("factors must be a dictionary")

    active: Dict[str, int] = {}
    age = _parse_age(factors.get("age"))

    if age is not None:
        key = _age_key(age)
        if key:
            active[key] = FACTOR_POINTS[key]
    else:
        explicit_age_keys = [key for key in AGE_KEYS if _is_positive(factors.get(key))]
        if len(explicit_age_keys) > 1:
            raise ValueError("age brackets are mutually exclusive")
        if explicit_age_keys:
            key = explicit_age_keys[0]
            active[key] = FACTOR_POINTS[key]

    for key, points in FACTOR_POINTS.items():
        if key in AGE_KEYS:
            continue
        if _is_positive(factors.get(key)):
            active[key] = points

    total = sum(active.values())
    for max_score, risk_tier, estimated_risk in TIERS:
        if total <= max_score:
            break

    extended: List[str] = []
    if risk_tier == "High Risk" and _is_positive(factors.get("malignancy")):
        extended.append(
            "If this patient is undergoing abdominal or pelvic cancer surgery and major-bleeding risk is not high, CHEST 2012 recommends extended-duration LMWH prophylaxis for 4 weeks."
        )

    scope_notes: List[str] = []
    if any(key in active for key in NON_GENERAL_SURGERY_SCOPE_KEYS):
        scope_notes.append(
            "Orthopedic, trauma, spinal-cord-injury, and medical-inpatient contexts require population-specific prophylaxis guidance; do not apply the general/abdominal-pelvic prophylaxis mapping without checking the relevant guideline."
        )

    return {
        "score": total,
        "risk_tier": risk_tier,
        "vte_rate": estimated_risk,
        "prophylaxis": list(PROPHYLAXIS_RECOMMENDATIONS[risk_tier]),
        "active_factors": dict(sorted(active.items(), key=lambda item: (-item[1], item[0]))),
        "extended_prophylaxis": extended,
        "bleeding_considerations": list(BLEEDING_RISK_CONSIDERATIONS),
        "scope_notes": scope_notes,
    }


def get_all_factors() -> List[Dict[str, Any]]:
    return [
        {"key": key, "label": label, "points": points}
        for key, label, points in RISK_FACTORS
    ]


def format_report(result: Dict[str, Any], patient_id: Optional[str] = None) -> str:
    lines = ["=" * 68, "CAPRINI VTE RISK ASSESSMENT", "=" * 68]
    if patient_id:
        lines.append(f"Patient ID: {patient_id}")
    lines.extend(
        [
            f"Total score: {result['score']}",
            f"CHEST/AT9 risk stratum: {result['risk_tier']}",
            f"Estimated baseline symptomatic VTE risk: {result['vte_rate']:.1%}",
            "",
            "Active factors:",
        ]
    )
    if result["active_factors"]:
        for key, points in result["active_factors"].items():
            lines.append(f"  - {FACTOR_LABELS.get(key, key)}: +{points}")
    else:
        lines.append("  - none")

    lines.append("")
    lines.append("Guideline-scoped prophylaxis summary:")
    for item in result["prophylaxis"]:
        lines.append(f"  - {item}")

    if result["extended_prophylaxis"]:
        lines.append("")
        lines.append("Extended-duration note:")
        for item in result["extended_prophylaxis"]:
            lines.append(f"  - {item}")

    if result["scope_notes"]:
        lines.append("")
        lines.append("Scope notes:")
        for item in result["scope_notes"]:
            lines.append(f"  - {item}")

    lines.extend(
        [
            "",
            "Clinical-use note:",
            "  - This tool supports risk assessment only and does not replace clinical judgment or local policy.",
            "  - Prophylaxis guidance is scoped to CHEST 2012 general/abdominal-pelvic surgery unless otherwise stated.",
            "=" * 68,
        ]
    )
    return "\n".join(lines)
