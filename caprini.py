#!/usr/bin/env python3
"""
Caprini VTE Risk Score Calculator.

Implements the Caprini Risk Assessment Model for Venous Thromboembolism (VTE)
in surgical patients. This is a validated, point-based scoring system published
by Joseph A. Caprini (2005, revised 2009/2013) and widely adopted in surgical
practice for VTE risk stratification and prophylaxis guidance.

Reference:
  Caprini JA. Thrombosis risk assessment as a guide to quality patient care.
  Dis Mon. 2005;51(2-3):70-78.

Stdlib only — no third-party dependencies.
"""

from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Risk factor definitions: (key, display_label, points)
# ---------------------------------------------------------------------------

RISK_FACTORS: List[Tuple[str, str, int]] = [
    # --- 1 point each ---
    ("age_41_60",                       "Age 41-60",                                      1),
    ("minor_surgery_lt_45min",          "Minor surgery (<45 min)",                         1),
    ("bmi_gt_25",                       "BMI >25",                                         1),
    ("swollen_legs",                    "Swollen legs (current)",                          1),
    ("varicose_veins",                  "Varicose veins",                                  1),
    ("pregnancy_or_postpartum",         "Pregnancy or postpartum",                         1),
    ("recurrent_miscarriage",           "History of unexplained/recurrent abortion",       1),
    ("oral_contraceptives_or_hrt",      "Oral contraceptives or HRT",                      1),
    ("sepsis_lt_1mo",                   "Sepsis (<1 month)",                               1),
    ("serious_lung_disease_lt_1mo",     "Serious lung disease (<1 month, incl. pneumonia)",1),
    ("abnormal_pulmonary_function",     "Abnormal pulmonary function",                     1),
    ("acute_mi",                        "Acute MI",                                        1),
    ("chf_lt_1mo",                      "CHF (<1 month)",                                  1),
    ("inflammatory_bowel_disease",      "History of inflammatory bowel disease",           1),
    ("medical_patient_bed_rest",        "Medical patient at bed rest",                     1),

    # --- 2 points each ---
    ("age_61_74",                       "Age 61-74",                                       2),
    ("arthroscopic_surgery_gt_45min",   "Arthroscopic surgery (>45 min)",                  2),
    ("major_open_surgery_gt_45min",     "Major open surgery (>45 min)",                    2),
    ("laparoscopic_surgery_gt_45min",   "Laparoscopic surgery (>45 min)",                  2),
    ("malignancy",                      "Malignancy (present or previous)",                2),
    ("bed_rest_gt_72h",                 "Bed rest >72 hours",                              2),
    ("immobilizing_plaster_cast",       "Immobilizing plaster cast",                       2),
    ("central_venous_access",           "Central venous access",                           2),

    # --- 3 points each ---
    ("age_75_plus",                     "Age ≥75",                                         3),
    ("history_of_vte",                  "History of VTE",                                  3),
    ("family_history_of_vte",           "Family history of VTE",                           3),
    ("factor_v_leiden",                 "Factor V Leiden",                                 3),
    ("prothrombin_20210a",              "Prothrombin 20210A",                              3),
    ("lupus_anticoagulant",             "Lupus anticoagulant",                             3),
    ("anticardiolipin_antibodies",      "Anticardiolipin antibodies",                      3),
    ("elevated_homocysteine",           "Elevated serum homocysteine",                     3),
    ("hit",                             "Heparin-induced thrombocytopenia (HIT)",          3),
    ("other_thrombophilia",             "Other congenital/acquired thrombophilia",         3),

    # --- 5 points each ---
    ("stroke_lt_1mo",                   "Stroke (<1 month)",                               5),
    ("multiple_trauma_lt_1mo",          "Multiple trauma (<1 month)",                      5),
    ("elective_lea",                    "Elective major lower extremity arthroplasty",     5),
    ("hip_pelvis_leg_fracture_lt_1mo",  "Hip, pelvis, or leg fracture (<1 month)",         5),
    ("acute_spinal_cord_injury_lt_1mo", "Acute spinal cord injury (<1 month)",             5),
]

# Lookup dict: key -> points
FACTOR_POINTS: Dict[str, int] = {key: pts for key, _, pts in RISK_FACTORS}

# Age-related keys (mutually exclusive — only the highest applicable one counts)
AGE_KEYS = {"age_41_60", "age_61_74", "age_75_plus"}


# ---------------------------------------------------------------------------
# Risk tiers and clinical guidance
# ---------------------------------------------------------------------------

TIERS = [
    # (max_score_inclusive, label, estimated_vte_rate, description)
    (1,  "Very Low Risk",  0.000, "0.0% VTE rate"),
    (2,  "Low Risk",       0.007, "0.7% VTE rate"),
    (4,  "Moderate Risk",  0.018, "1.8% VTE rate"),
    (6,  "High Risk",      0.036, "3.6% VTE rate"),
    (999, "Highest Risk",  0.054, "5.4%+ VTE rate"),
]

PROPHYLAXIS_RECOMMENDATIONS = {
    "Very Low Risk": [
        "Early ambulation only",
        "No pharmacologic or mechanical prophylaxis required",
    ],
    "Low Risk": [
        "Sequential compression devices (SCDs) while in bed",
        "Encourage early and frequent ambulation",
    ],
    "Moderate Risk": [
        "Sequential compression devices (SCDs)",
        "Consider pharmacologic prophylaxis (LMWH or LDUH) based on individual assessment",
    ],
    "High Risk": [
        "Pharmacologic prophylaxis recommended (LMWH 40 mg SC daily or LDUH 5000 U SC q8-12h)",
        "Sequential compression devices (SCDs) in addition to pharmacologic prophylaxis",
        "Reassess daily for changes in risk status",
    ],
    "Highest Risk": [
        "Pharmacologic prophylaxis strongly recommended (LMWH 40 mg SC daily or LDUH 5000 U SC q8-12h)",
        "Sequential compression devices (SCDs) in addition to pharmacologic prophylaxis",
        "Extended-duration prophylaxis (up to 28-35 days post-discharge) for major cancer surgery, "
        "major orthopedic surgery, or high-risk abdominal/pelvic surgery",
        "Consider IVC filter only when anticoagulation is contraindicated",
        "Reassess daily; consider dose adjustment for renal impairment",
    ],
}

EXTENDED_PROPHYLAXIS_INDICATIONS = [
    "Major cancer surgery (abdominal/pelvic) — 28 days post-discharge",
    "Major lower extremity arthroplasty — 28-35 days post-discharge",
    "Hip fracture surgery — 28-35 days post-discharge",
    "Abdominal surgery for cancer with additional VTE risk factors — 28 days post-discharge",
    "Severe trauma with prolonged immobilization — individualized duration",
]

BLEEDING_RISK_CONSIDERATIONS = [
    "Assess bleeding risk before initiating pharmacologic prophylaxis",
    "Contraindications: active bleeding, severe thrombocytopenia (plt <50,000), "
    "uncontrolled coagulopathy, recent CNS hemorrhage",
    "Use mechanical prophylaxis only if high bleeding risk with high VTE risk",
    "Re-evaluate bleeding risk daily; transition to pharmacologic when safe",
    "For patients on dual antiplatelet therapy, consult hematology before adding anticoagulation",
]


# ---------------------------------------------------------------------------
# Core scoring function
# ---------------------------------------------------------------------------

def calculate_score(factors: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate the Caprini VTE Risk Score from a dictionary of risk factors.

    Parameters
    ----------
    factors : dict
        Keys are risk factor identifiers (see RISK_FACTORS). Values should be
        truthy (1, True, "yes", "y") to indicate presence, or falsy (0, False,
        "no", "", None) to indicate absence.

        Age is handled automatically: pass ``age`` as a numeric value and the
        appropriate age bracket will be selected. If you pass age bracket keys
        directly (``age_41_60``, ``age_61_74``, ``age_75_plus``), those are
        used instead.

    Returns
    -------
    dict with keys:
        score           — total Caprini score (int)
        risk_tier       — "Very Low Risk" / "Low Risk" / "Moderate Risk" /
                          "High Risk" / "Highest Risk"
        vte_rate        — estimated VTE rate without prophylaxis (float)
        prophylaxis     — list of prophylaxis recommendation strings
        active_factors  — dict of {factor_key: points} for all present factors
        extended_prophylaxis — list of applicable extended prophylaxis notes
        bleeding_considerations — list of bleeding risk notes
    """
    active: Dict[str, int] = {}

    # --- Age handling ---
    age_val = factors.get("age")
    if age_val is not None:
        try:
            age_num = float(age_val)
        except (TypeError, ValueError):
            age_num = None
        if age_num is not None:
            if age_num >= 75:
                active["age_75_plus"] = FACTOR_POINTS["age_75_plus"]
            elif age_num >= 61:
                active["age_61_74"] = FACTOR_POINTS["age_61_74"]
            elif age_num >= 41:
                active["age_41_60"] = FACTOR_POINTS["age_41_60"]

    # --- All other factors ---
    for key, points in FACTOR_POINTS.items():
        if key in AGE_KEYS:
            # Already handled above (unless user passed the key directly)
            if key not in active:
                val = factors.get(key)
                if _is_positive(val):
                    active[key] = points
            continue
        val = factors.get(key)
        if _is_positive(val):
            active[key] = points

    # --- Compute total ---
    total = sum(active.values())

    # --- Determine tier ---
    tier_label = "Highest Risk"
    tier_vte = 0.054
    for max_score, label, vte_rate, _desc in TIERS:
        if total <= max_score:
            tier_label = label
            tier_vte = vte_rate
            break

    # --- Extended prophylaxis ---
    extended = []
    has_cancer_surgery = _is_positive(factors.get("malignancy")) and (
        _is_positive(factors.get("major_open_surgery_gt_45min"))
        or _is_positive(factors.get("laparoscopic_surgery_gt_45min"))
    )
    has_lea = _is_positive(factors.get("elective_lea"))
    has_hip_fracture = _is_positive(factors.get("hip_pelvis_leg_fracture_lt_1mo"))
    has_severe_trauma = _is_positive(factors.get("multiple_trauma_lt_1mo"))

    if has_cancer_surgery:
        extended.append(EXTENDED_PROPHYLAXIS_INDICATIONS[0])
        extended.append(EXTENDED_PROPHYLAXIS_INDICATIONS[3])
    if has_lea:
        extended.append(EXTENDED_PROPHYLAXIS_INDICATIONS[1])
    if has_hip_fracture:
        extended.append(EXTENDED_PROPHYLAXIS_INDICATIONS[2])
    if has_severe_trauma:
        extended.append(EXTENDED_PROPHYLAXIS_INDICATIONS[4])

    return {
        "score": total,
        "risk_tier": tier_label,
        "vte_rate": tier_vte,
        "prophylaxis": PROPHYLAXIS_RECOMMENDATIONS[tier_label],
        "active_factors": dict(sorted(active.items(), key=lambda kv: -kv[1])),
        "extended_prophylaxis": extended,
        "bleeding_considerations": BLEEDING_RISK_CONSIDERATIONS,
    }


def _is_positive(val: Any) -> bool:
    """Return True if a factor value is considered 'present'."""
    if val is None:
        return False
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val >= 1
    s = str(val).strip().lower()
    return s in ("1", "true", "yes", "y", "present")


def get_all_factors() -> List[Dict[str, Any]]:
    """Return the full list of risk factors with their keys, labels, and points."""
    return [
        {"key": key, "label": label, "points": pts}
        for key, label, pts in RISK_FACTORS
    ]


def format_report(result: Dict[str, Any], patient_id: Optional[str] = None) -> str:
    """Format a Caprini result dict into a human-readable clinical report."""
    lines = []
    lines.append("=" * 64)
    lines.append("  CAPRINI VTE RISK ASSESSMENT REPORT")
    lines.append("=" * 64)
    if patient_id:
        lines.append(f"  Patient ID: {patient_id}")
    lines.append(f"  Total Score: {result['score']}")
    lines.append(f"  Risk Tier:   {result['risk_tier']}")
    lines.append(f"  Est. VTE Rate (no prophylaxis): {result['vte_rate']:.1%}")
    lines.append("-" * 64)

    lines.append("  Active Risk Factors:")
    if result["active_factors"]:
        for key, pts in result["active_factors"].items():
            label = key
            for k, l, _ in RISK_FACTORS:
                if k == key:
                    label = l
                    break
            lines.append(f"    [{pts} pt{'s' if pts != 1 else ' '}] {label}")
    else:
        lines.append("    (none)")

    lines.append("-" * 64)
    lines.append("  Prophylaxis Recommendations:")
    for rec in result["prophylaxis"]:
        lines.append(f"    • {rec}")

    if result["extended_prophylaxis"]:
        lines.append("-" * 64)
        lines.append("  Extended Prophylaxis Guidance:")
        for note in result["extended_prophylaxis"]:
            lines.append(f"    • {note}")

    lines.append("-" * 64)
    lines.append("  Bleeding Risk Considerations:")
    for note in result["bleeding_considerations"]:
        lines.append(f"    • {note}")

    lines.append("=" * 64)
    lines.append("  DISCLAIMER: This tool is for clinical decision SUPPORT only.")
    lines.append("  It does NOT replace clinical judgment. Always consider the")
    lines.append("  individual patient's complete clinical picture.")
    lines.append("=" * 64)
    return "\n".join(lines)
