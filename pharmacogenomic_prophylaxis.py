#!/usr/bin/env python3
"""
Pharmacogenomic Prophylaxis for Caprini VTE Risk Calculator.
Adjusts VTE prophylaxis based on pharmacogenomic profiles affecting drug metabolism.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass


PHARMACOGENOMIC_MARKERS = {
    "CYP2C9Poor": {"drug": "warfarin", "effect": "increased_bleeding",
                    "recommendation": "Reduce warfarin dose 50%. Consider DOACs."},
    "CYP2C9Intermediate": {"drug": "warfarin", "effect": "moderate_increase",
                           "recommendation": "Start warfarin at lower dose. INR monitoring."},
    "VKORC1_HighSensitivity": {"drug": "warfarin", "effect": "increased_sensitivity",
                                "recommendation": "Reduced warfarin initiation dose."},
    "DPYD_Deficient": {"drug": "fluorouracil", "effect": "severe_toxicity",
                        "recommendation": "Avoid 5-FU. Alternative chemotherapy."},
    "TPMT_Deficient": {"drug": "mercaptopurine", "effect": "myelosuppression",
                        "recommendation": "Reduce dose 75%. Monitor CBC closely."},
    "CYP3A4_Poor": {"drug": "rivaroxaban_apixaban", "effect": "increased_exposure",
                     "recommendation": "Consider dose reduction or avoid DOACs."},
    "CYP3A4_Rapid": {"drug": "rivaroxaban_apixaban", "effect": "decreased_exposure",
                      "recommendation": "Standard dose likely adequate."},
}


@dataclass
class PharmacogenomicProfile:
    """Patient pharmacogenomic profile."""
    cyp2c9_status: str = "Normal"
    vkorc1_status: str = "Normal"
    cyp3a4_status: str = "Normal"
    dpyd_status: str = "Normal"
    tpmt_status: str = "Normal"


def assess_pharmacogenomic_prophylaxis(profile: PharmacogenomicProfile,
                                        recommended_drug: str = "enoxaparin") -> Dict[str, Any]:
    """Assess pharmacogenomic impact on VTE prophylaxis."""
    adjustments = []
    drug_recommendations = []

    if profile.cyp2c9_status in ("Poor", "Intermediate") and recommended_drug == "warfarin":
        marker_key = f"CYP2C9{profile.cyp2c9_status}"
        marker = PHARMACOGENOMIC_MARKERS.get(marker_key, {})
        adjustments.append({
            "gene": "CYP2C9", "status": profile.cyp2c9_status,
            "impact": marker.get("effect", "unknown"),
            "recommendation": marker.get("recommendation", "Consult pharmacogenomics.")
        })

    if profile.vkorc1_status == "HighSensitivity" and recommended_drug == "warfarin":
        marker = PHARMACOGENOMIC_MARKERS.get("VKORC1_HighSensitivity", {})
        adjustments.append({
            "gene": "VKORC1", "status": profile.vkorc1_status,
            "impact": marker.get("effect", "unknown"),
            "recommendation": marker.get("recommendation", "Consult pharmacogenomics.")
        })

    if profile.cyp3a4_status in ("Poor", "Rapid") and recommended_drug in ("rivaroxaban", "apixaban"):
        marker_key = f"CYP3A4{profile.cyp3a4_status}"
        marker = PHARMACOGENOMIC_MARKERS.get(marker_key, {})
        adjustments.append({
            "gene": "CYP3A4", "status": profile.cyp3a4_status,
            "impact": marker.get("effect", "unknown"),
            "recommendation": marker.get("recommendation", "Consult pharmacogenomics.")
        })

    if profile.dpyd_status == "Deficient":
        marker = PHARMACOGENOMIC_MARKERS.get("DPYD_Deficient", {})
        adjustments.append({
            "gene": "DPYD", "status": profile.dpyd_status,
            "impact": marker.get("effect", "unknown"),
            "recommendation": marker.get("recommendation", "Consult pharmacogenomics.")
        })

    if adjustments:
        overall_adjustment = "PGx-guided dosing required"
    else:
        overall_adjustment = "No pharmacogenomic adjustments needed"

    if recommended_drug == "warfarin" and profile.cyp2c9_status in ("Poor", "Intermediate"):
        alternative = "DOAC preferred (rivaroxaban, apixaban) if CrCl adequate"
    else:
        alternative = "Standard prophylaxis appropriate"

    return {
        "adjustments": adjustments,
        "overall_adjustment": overall_adjustment,
        "recommended_drug": recommended_drug,
        "alternative_recommendation": alternative,
    }


class PharmacogenomicAgent:
    """Sub-agent for pharmacogenomic prophylaxis."""

    def __init__(self):
        self.agent_name = "PharmacogenomicAgent"

    def evaluate(self, profile: PharmacogenomicProfile,
                 recommended_drug: str = "enoxaparin") -> Dict[str, Any]:
        """Evaluate pharmacogenomic prophylaxis."""
        result = assess_pharmacogenomic_prophylaxis(profile, recommended_drug)
        alerts = []

        for adj in result["adjustments"]:
            if adj["impact"] in ("increased_bleeding", "severe_toxicity", "myelosuppression"):
                alerts.append({
                    "type": f"PGX_{adj['gene']}_ALERT", "severity": "WARNING",
                    "message": f"{adj['gene']} {adj['status']}: {adj['impact']}.",
                    "recommendation": adj["recommendation"]
                })

        if result["alternative_recommendation"] != "Standard prophylaxis appropriate":
            alerts.append({
                "type": "PGX_DRUG_ALTERNATIVE", "severity": "ADVISORY",
                "message": result["alternative_recommendation"],
                "recommendation": "Review pharmacogenomic profile before prescribing."
            })

        return {"pgx_result": result, "alerts": alerts}
