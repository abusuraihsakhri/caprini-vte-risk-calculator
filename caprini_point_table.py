#!/usr/bin/env python3
"""
Caprini 2005 VTE risk assessment model with the complete factor-point table.

Each risk factor carries its published weight (1, 2, 3, or 5 points); the
total maps to VTE-risk tiers and ACCP-aligned prophylaxis intensity:

    1 pt : age 41-60, minor surgery, BMI>25, swollen legs, varicose veins,
           pregnancy/postpartum, OCP/HRT, sepsis <1mo, pneumonia <1mo,
           COPD/abnormal PFTs, acute MI <1mo, CHF <1mo, bed rest,
           IBD, recurrent miscarriage
    2 pts: age 61-74, arthroscopic surgery, major/laparoscopic surgery >45min,
           malignancy present or previous, confined to bed >72h,
           immobilizing cast <1mo, central venous line
    3 pts: age >=75, personal history DVT/PE, family history of thrombosis,
           factor V Leiden, prothrombin 20210A, lupus anticoagulant,
           anticardiolipin antibodies, elevated homocysteine,
           HIT/HITTS, other congenital/acquired thrombophilia
    5 pts: stroke >1 month, elective major lower-extremity arthroplasty,
           hip/pelvis/leg fracture <1mo, acute spinal cord injury with
           paralysis <1mo, multiple trauma <1mo

Tiers (VTE incidence without prophylaxis):
    0        very low   ~0.5%
    1-2      low        ~1.5%
    3-4      moderate   ~3%
    >=5      high       ~6%
"""

from dataclasses import dataclass
from typing import Any, Dict, List


CAPRINI_2005: Dict[str, int] = {
    # ---- 1 point ----------------------------------------------------------
    "age_41_60": 1,
    "minor_surgery_planned": 1,
    "bmi_over_25": 1,
    "swollen_legs": 1,
    "varicose_veins": 1,
    "pregnancy_or_postpartum": 1,
    "recurrent_miscarriage_history": 1,
    "oral_contraceptives_or_hrt": 1,
    "sepsis_within_1_month": 1,
    "serious_lung_disease_pneumonia": 1,
    "copd_abnormal_pulmonary_function": 1,
    "acute_mi_within_1_month": 1,
    "chf_within_1_month": 1,
    "medical_patient_at_bed_rest": 1,
    "inflammatory_bowel_disease": 1,
    # ---- 2 points ---------------------------------------------------------
    "age_61_74": 2,
    "arthroscopic_surgery": 2,
    "major_open_surgery_over_45min": 2,
    "laparoscopic_surgery_over_45min": 2,
    "malignancy_present_or_previous": 2,
    "confined_to_bed_over_72h": 2,
    "immobilizing_plaster_cast": 2,
    "central_venous_line": 2,
    # ---- 3 points ---------------------------------------------------------
    "age_75_plus": 3,
    "personal_history_dvt_pe": 3,
    "family_history_thrombosis": 3,
    "factor_v_leiden_mutation": 3,
    "prothrombin_20210a_mutation": 3,
    "lupus_anticoagulant": 3,
    "anticardiolipin_antibodies": 3,
    "elevated_homocysteine": 3,
    "hit_or_hitts": 3,
    "other_thrombophilia": 3,
    # ---- 5 points ---------------------------------------------------------
    "stroke_over_1_month": 5,
    "elective_major_lower_extremity_arthroplasty": 5,
    "hip_pelvis_leg_fracture_within_1_month": 5,
    "acute_spinal_cord_injury_paralysis": 5,
    "multiple_trauma_within_1_month": 5,
}

AGE_FIELDS = {"age_41_60", "age_61_74", "age_75_plus"}

PROPHYLAXIS_BY_TIER = {
    "very_low": ["early ambulation only"],
    "low": ["graduated compression stockings",
            "intermittent pneumatic compression until ambulating"],
    "moderate": ["LMWH or low-dose unfractionated heparin",
                 "+ mechanical prophylaxis (IPC/GCS)"],
    "high": ["pharmacologic prophylaxis (LMWH/LDUH) + mechanical",
             "reassess daily; consider extended-duration prophylaxis",
             "consider IVC filter only when anticoagulation contraindicated"],
}

TIER_VTE_RATES = {
    "very_low": 0.005, "low": 0.015, "moderate": 0.03, "high": 0.06,
}


@dataclass
class CapriniFactors:
    """Set boolean flags for every applicable factor; age handled separately."""
    age_years: float = 40
    flags: List[str] = None

    def __post_init__(self):
        if self.flags is None:
            self.flags = []


def score_caprini(f: CapriniFactors) -> Dict[str, Any]:
    active: Dict[str, int] = {}
    for name in f.flags:
        if name not in CAPRINI_2005:
            raise KeyError(f"unknown Caprini factor: {name}")
        active[name] = CAPRINI_2005[name]
    age_field = ("age_75_plus" if f.age_years >= 75 else
                 "age_61_74" if f.age_years >= 61 else
                 "age_41_60" if f.age_years >= 41 else None)
    if age_field:
        active[age_field] = CAPRINI_2005[age_field]

    total = sum(active.values())
    if total == 0:
        tier = "very_low"
    elif total <= 2:
        tier = "low"
    elif total <= 4:
        tier = "moderate"
    else:
        tier = "high"

    return {
        "caprini_score": total,
        "risk_tier": tier,
        "estimated_vte_rate_no_prophylaxis": TIER_VTE_RATES[tier],
        "prophylaxis_recommendation": PROPHYLAXIS_BY_TIER[tier],
        "active_factors": dict(sorted(active.items(), key=lambda kv: -kv[1])),
        "five_point_factors_present": [k for k in active if active[k] == 5],
    }


if __name__ == "__main__":
    cases = [
        ("young minor surgery",
         CapriniFactors(35, ["minor_surgery_planned"])),
        ("moderate cancer case",
         CapriniFactors(66, ["malignancy_present_or_previous",
                             "central_venous_line", "bmi_over_25"])),
        ("high-risk arthroplasty",
         CapriniFactors(78, ["elective_major_lower_extremity_arthroplasty",
                             "family_history_thrombosis", "swollen_legs"])),
        ("trauma maximum",
         CapriniFactors(52, ["multiple_trauma_within_1_month",
                             "hip_pelvis_leg_fracture_within_1_month",
                             "acute_spinal_cord_injury_paralysis"])),
    ]
    print("Caprini 2005 scoring")
    print("-" * 64)
    for name, factors in cases:
        r = score_caprini(factors)
        print(f"{name:24s} score={r['caprini_score']:<3} "
              f"tier={r['risk_tier']:<9s} "
              f"VTE~{r['estimated_vte_rate_no_prophylaxis']:.1%}")
        print(f"   plan: {' + '.join(r['prophylaxis_recommendation'])}")
