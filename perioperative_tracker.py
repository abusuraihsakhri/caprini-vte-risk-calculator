#!/usr/bin/env python3
"""
Perioperative Caprini trajectory tracker.

Stores sequential Caprini assessments at protocol timepoints (preop, POD 1/3/5),
attributes each score change to newly-added risk factors, and fires escalation
alerts when:
  - the patient crosses into the high-risk tier (score >= 5)
  - any new 5-point factor appears after surgery (trauma/fracture events)
  - a single interval adds >= 3 points
  - high-tier patients lack documented pharmacologic prophylaxis

Stdlib only.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from caprini_point_table import CapriniFactors, PROPHYLAXIS_BY_TIER, score_caprini


@dataclass
class Snapshot:
    timepoint: str                      # preop | pod1 | pod3 | pod5 | discharge
    age_years: float
    new_flags_since_last: List[str] = field(default_factory=list)
    pharmacologic_prophylaxis_ordered: bool = False


def _apply(snapshots_so_far: List[str], snap: Snapshot) -> List[str]:
    return snapshots_so_far + list(snap.new_flags_since_last)


def track_perioperative(snaps: List[Snapshot]) -> Dict[str, Any]:
    timeline: List[Dict[str, Any]] = []
    alerts: List[str] = []
    accumulated_flags: List[str] = []

    for i, snap in enumerate(snaps):
        accumulated_flags = _apply(accumulated_flags, snap)
        result = score_caprini(CapriniFactors(snap.age_years, list(accumulated_flags)))
        prev = timeline[-1] if timeline else None
        delta = None if prev is None else result["caprini_score"] - prev["score"]
        entry = {
            "timepoint": snap.timepoint,
            "score": result["caprini_score"],
            "tier": result["risk_tier"],
            "delta": delta,
            "new_factors": list(snap.new_flags_since_last),
        }
        if prev and result["risk_tier"] != prev["tier"]:
            alerts.append(f"{snap.timepoint}: tier {prev['tier']} -> "
                          f"{result['risk_tier']} (update prophylaxis orders)")
        if i > 0 and delta is not None and delta >= 3:
            alerts.append(f"{snap.timepoint}: score jumped +{delta}; review for "
                          "occult complication (DVT, PE, infection)")
        new_five_point = [f for f in result.get("five_point_factors_present", [])
                          if f in snap.new_flags_since_last]
        for f in new_five_point:
            alerts.append(f"{snap.timepoint}: NEW 5-point factor '{f}' postoperatively")
        if result["risk_tier"] == "high" and not snap.pharmacologic_prophylaxis_ordered:
            alerts.append(f"{snap.timepoint}: HIGH Caprini ({result['caprini_score']}) "
                          "without pharmacologic prophylaxis order")
        timeline.append(entry)

    final = timeline[-1] if timeline else None
    return {
        "timeline": timeline,
        "alerts": alerts or ["no escalation events across the perioperative window"],
        "final_score": final["score"] if final else None,
        "final_plan": PROPHYLAXIS_BY_TIER[final["tier"]] if final else [],
    }


if __name__ == "__main__":
    snaps = [
        Snapshot("preop", 68, [], False),
        Snapshot("pod1", 68, ["major_open_surgery_over_45min"], True),
        Snapshot("pod3", 68, ["central_venous_line"], True),
        Snapshot("pod5", 68, ["swollen_legs", "confined_to_bed_over_72h"], False),
    ]
    report = track_perioperative(snaps)
    print("Perioperative Caprini trajectory")
    print("-" * 56)
    for e in report["timeline"]:
        d = "" if e["delta"] is None else f"{e['delta']:+d}"
        extras = f" (+{', '.join(e['new_factors'])})" if e["new_factors"] else ""
        print(f"{e['timepoint']:8s} score={e['score']:<3} {e['tier']:<9s} delta={d:>3}{extras}")
    print("\nAlerts:")
    for a in report["alerts"]:
        print(f"  ! {a}")
    print("\nFinal plan:", "; ".join(report["final_plan"]))
