import csv
import subprocess
import sys
from pathlib import Path

import pytest

from caprini import RISK_FACTORS, calculate_score, get_all_factors
from perioperative_tracker import Snapshot, track_perioperative


def test_factor_counts():
    counts = {points: sum(1 for _, _, value in RISK_FACTORS if value == points) for points in (1, 2, 3, 5)}
    assert counts == {1: 15, 2: 8, 3: 10, 5: 5}
    assert len(RISK_FACTORS) == 38


@pytest.mark.parametrize(
    ("age", "score"),
    [(40, 0), (41, 1), (60, 1), (61, 2), (74, 2), (75, 3), (100, 3)],
)
def test_age_boundaries(age, score):
    assert calculate_score({"age": age})["score"] == score


def test_numeric_age_prevents_age_double_counting():
    result = calculate_score({"age": 70, "age_41_60": True, "age_75_plus": True})
    assert result["score"] == 2
    assert result["active_factors"] == {"age_61_74": 2}


def test_multiple_explicit_age_brackets_rejected_without_numeric_age():
    with pytest.raises(ValueError, match="mutually exclusive"):
        calculate_score({"age_41_60": True, "age_61_74": True})


@pytest.mark.parametrize("age", [-1, 131, "old"])
def test_invalid_age_rejected(age):
    with pytest.raises(ValueError):
        calculate_score({"age": age})


@pytest.mark.parametrize(
    ("factors", "score", "tier", "rate"),
    [
        ({}, 0, "Very Low Risk", 0.005),
        ({"age": 50}, 1, "Low Risk", 0.015),
        ({"age": 70}, 2, "Low Risk", 0.015),
        ({"age": 80}, 3, "Moderate Risk", 0.030),
        ({"age": 80, "bmi_gt_25": True}, 4, "Moderate Risk", 0.030),
        ({"stroke_lt_1mo": True}, 5, "High Risk", 0.060),
        ({"age": 80, "history_of_vte": True}, 6, "High Risk", 0.060),
        ({"age": 80, "history_of_vte": True, "bmi_gt_25": True}, 7, "High Risk", 0.060),
        ({"stroke_lt_1mo": True, "history_of_vte": True}, 8, "High Risk", 0.060),
        ({"stroke_lt_1mo": True, "multiple_trauma_lt_1mo": True}, 10, "High Risk", 0.060),
    ],
)
def test_chest_risk_strata(factors, score, tier, rate):
    result = calculate_score(factors)
    assert result["score"] == score
    assert result["risk_tier"] == tier
    assert result["vte_rate"] == rate


def test_high_risk_guidance_does_not_recommend_ivc_filter():
    result = calculate_score({"stroke_lt_1mo": True})
    combined = " ".join(result["prophylaxis"] + result["extended_prophylaxis"]).lower()
    assert "ivc filter" not in combined
    assert any("not recommended" in item.lower() and "inferior vena cava" in item.lower() for item in result["bleeding_considerations"])


def test_cancer_surgery_extended_note_is_conditional():
    result = calculate_score({"malignancy": True, "major_open_surgery_gt_45min": True, "bmi_gt_25": True})
    assert result["score"] == 5
    assert result["risk_tier"] == "High Risk"
    assert len(result["extended_prophylaxis"]) == 1
    assert "if this patient is undergoing abdominal or pelvic cancer surgery" in result["extended_prophylaxis"][0].lower()


def test_specialty_population_note_for_arthroplasty():
    result = calculate_score({"elective_lea": True})
    assert result["score"] == 5
    assert result["scope_notes"]
    assert "population-specific" in result["scope_notes"][0]


def test_unknown_keys_are_ignored():
    assert calculate_score({"age": 50, "not_a_factor": True})["score"] == 1


def test_get_all_factors_structure():
    factors = get_all_factors()
    assert len(factors) == 38
    assert set(factors[0]) == {"key", "label", "points"}


def test_perioperative_tracker_uses_canonical_scoring():
    result = track_perioperative([
        Snapshot("preop", 68, []),
        Snapshot("postop", 68, ["major_open_surgery_gt_45min", "central_venous_access"]),
    ])
    assert result["timeline"][0]["score"] == 2
    assert result["timeline"][1]["score"] == 6
    assert result["final_risk_tier"] == "High Risk"
    assert result["alerts"]


def test_cli_score_smoke():
    completed = subprocess.run(
        [sys.executable, "cli.py", "score", "--age", "68", "--malignancy", "--major-open-surgery-gt-45min"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert "Total score: 6" in completed.stdout
    assert "High Risk" in completed.stdout


def test_cli_batch_smoke(tmp_path: Path):
    input_csv = tmp_path / "input.csv"
    output_csv = tmp_path / "output.csv"
    input_csv.write_text("patient_id,age,malignancy\nP1,68,1\nP2,30,0\n", encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, "cli.py", "batch", "-i", str(input_csv), "-o", str(output_csv)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    with output_csv.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["caprini_score"] == "4"
    assert rows[0]["risk_tier"] == "Moderate Risk"
    assert rows[1]["caprini_score"] == "0"
    assert rows[1]["risk_tier"] == "Very Low Risk"
