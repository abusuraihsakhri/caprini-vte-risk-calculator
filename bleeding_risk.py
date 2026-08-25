#!/usr/bin/env python3
"""
Bleeding Risk Stratification for Caprini VTE Risk Calculator.
Stratifies patients by surgical bleeding risk to guide VTE prophylaxis decisions.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class BleedingRiskFactors:
    """Patient bleeding risk factors."""
    age: float
    sex: str
    platelet_count: float
    inr: float
    aptt_sec: float
    liver_disease: bool = False
    renal_disease: bool = False
    antiplatelet_therapy: bool = False
    anticoagulant_therapy: bool = False
    prior_bleeding: bool = False
    surgery_type: str = "general"


def calculate_bleeding_risk(factors: BleedingRiskFactors) -> Dict[str, Any]:
    """Calculate surgical bleeding risk score."""
    score = 0
    risk_factors = []

    if factors.platelet_count < 50:
        score += 3
        risk_factors.append(f"Severe thrombocytopenia ({factors.platelet_count:.0f})")
    elif factors.platelet_count < 100:
        score += 1
        risk_factors.append(f"Moderate thrombocytopenia ({factors.platelet_count:.0f})")

    if factors.inr > 1.5:
        score += 2
        risk_factors.append(f"Elevated INR ({factors.inr:.1f})")

    if factors.aptt_sec > 40:
        score += 1
        risk_factors.append(f"Elevated aPTT ({factors.aptt_sec:.0f}s)")

    if factors.liver_disease:
        score += 2
        risk_factors.append("Liver disease")
    if factors.renal_disease:
        score += 1
        risk_factors.append("Renal disease")
    if factors.antiplatelet_therapy:
        score += 1
        risk_factors.append("Antiplatelet therapy")
    if factors.anticoagulant_therapy:
        score += 2
        risk_factors.append("Anticoagulant therapy")
    if factors.prior_bleeding:
        score += 2
        risk_factors.append("Prior surgical bleeding")

    if factors.surgery_type in ("neurosurgery", "spinal", "ophthalmologic", "urologic"):
        score += 2
        risk_factors.append(f"High-bleeding-risk surgery ({factors.surgery_type})")
    elif factors.surgery_type in ("orthopedic", "abdominal", "cardiac"):
        score += 1
        risk_factors.append(f"Moderate-bleeding-risk surgery ({factors.surgery_type})")

    if factors.age > 75:
        score += 1
        risk_factors.append(f"Age >75 ({factors.age:.0f})")

    if score >= 6:
        bleeding_risk = "VERY_HIGH"
        prophylaxis_modifier = "Consider mechanical prophylaxis only. Delay pharmacologic if possible."
    elif score >= 4:
        bleeding_risk = "HIGH"
        prophylaxis_modifier = "Shortened pharmacologic prophylaxis duration. Close monitoring."
    elif score >= 2:
        bleeding_risk = "MODERATE"
        prophylaxis_modifier = "Standard prophylaxis with increased bleeding surveillance."
    else:
        bleeding_risk = "LOW"
        prophylaxis_modifier = "Standard VTE prophylaxis appropriate."

    return {
        "bleeding_risk_score": score,
        "bleeding_risk": bleeding_risk,
        "risk_factors": risk_factors,
        "prophylaxis_modifier": prophylaxis_modifier,
        "platelet_count": factors.platelet_count,
        "inr": factors.inr,
    }


class BleedingRiskAgent:
    """Sub-agent for bleeding risk stratification."""

    def __init__(self):
        self.agent_name = "BleedingRiskAgent"

    def evaluate(self, factors: BleedingRiskFactors, caprini_score: float = 0.0) -> Dict[str, Any]:
        """Evaluate bleeding risk."""
        result = calculate_bleeding_risk(factors)
        alerts = []

        if result["bleeding_risk"] in ("VERY_HIGH", "HIGH"):
            alerts.append({
                "type": "HIGH_BLEEDING_RISK", "severity": "WARNING",
                "message": f"High bleeding risk (score: {result['bleeding_risk_score']}). "
                           f"May modify VTE prophylaxis approach.",
                "recommendation": result["prophylaxis_modifier"]
            })

        if caprini_score >= 5 and result["bleeding_risk_score"] >= 4:
            alerts.append({
                "type": "HIGH_VTE_HIGH_BLEEDING", "severity": "CRITICAL",
                "message": "Conflict: High VTE risk (Caprini) but high bleeding risk.",
                "recommendation": "Individualized assessment. Consider IVC filter if anticoagulation contraindicated."
            })

        return {"bleeding_result": result, "alerts": alerts}
