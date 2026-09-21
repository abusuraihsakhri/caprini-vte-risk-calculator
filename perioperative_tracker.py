#!/usr/bin/env python3
"""Track serial Caprini scores across perioperative timepoints."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from caprini import calculate_score


@dataclass
class Snapshot:
    timepoint: str
    age_years: float
    new_flags_since_last: List[str] = field(default_factory=list)


def track_perioperative(snapshots: List[Snapshot]) -> Dict[str, Any]:
    timeline: List[Dict[str, Any]] = []
    alerts: List[str] = []
    accumulated: List[str] = []

    for snapshot in snapshots:
        accumulated.extend(snapshot.new_flags_since_last)
        factors = {"age": snapshot.age_years, **{key: True for key in accumulated}}
        result = calculate_score(factors)
        previous = timeline[-1] if timeline else None
        delta = None if previous is None else result["score"] - previous["score"]
        entry = {
            "timepoint": snapshot.timepoint,
            "score": result["score"],
            "risk_tier": result["risk_tier"],
            "delta": delta,
            "new_factors": list(snapshot.new_flags_since_last),
        }
        if previous and result["risk_tier"] != previous["risk_tier"]:
            alerts.append(
                f"{snapshot.timepoint}: risk stratum changed from {previous['risk_tier']} to {result['risk_tier']}"
            )
        if delta is not None and delta >= 3:
            alerts.append(f"{snapshot.timepoint}: Caprini score increased by {delta} points")
        timeline.append(entry)

    return {
        "timeline": timeline,
        "alerts": alerts,
        "final_score": timeline[-1]["score"] if timeline else None,
        "final_risk_tier": timeline[-1]["risk_tier"] if timeline else None,
    }
