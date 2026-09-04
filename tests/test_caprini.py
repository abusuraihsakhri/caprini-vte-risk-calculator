#!/usr/bin/env python3
"""
Comprehensive tests for the Caprini VTE Risk Score Calculator.

Covers:
  - Score 0 (very low risk, no factors)
  - Score ≥7 (highest risk)
  - All individual risk factors (1, 2, 3, and 5 point factors)
  - Age bracket auto-selection
  - Clinical scenarios (orthopedic, cancer, trauma, medical)
  - Prophylaxis recommendations per tier
  - Extended prophylaxis guidance
  - Edge cases and input handling
  - CLI commands
  - Report formatting

Stdlib only — uses unittest so no pytest dependency is required.
"""

import csv
import json
import os
import sys
import tempfile
import unittest

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from caprini import (
    calculate_score,
    format_report,
    get_all_factors,
    FACTOR_POINTS,
    RISK_FACTORS,
    PROPHYLAXIS_RECOMMENDATIONS,
    EXTENDED_PROPHYLAXIS_INDICATIONS,
    BLEEDING_RISK_CONSIDERATIONS,
    _is_positive,
)


class TestIsPositive(unittest.TestCase):
    """Test the _is_positive helper."""

    def test_truthy_values(self):
        for v in [1, True, "1", "true", "True", "yes", "Yes", "y", "Y", "present", 2, 1.0]:
            self.assertTrue(_is_positive(v), f"Expected True for {v!r}")

    def test_falsy_values(self):
        for v in [0, False, "0", "false", "no", "", None, "nope", 0.0]:
            self.assertFalse(_is_positive(v), f"Expected False for {v!r}")


class TestScoreZero(unittest.TestCase):
    """Score 0: no risk factors at all."""

    def test_empty_factors(self):
        result = calculate_score({})
        self.assertEqual(result["score"], 0)
        self.assertEqual(result["risk_tier"], "Very Low Risk")
        self.assertAlmostEqual(result["vte_rate"], 0.0)
        self.assertEqual(result["active_factors"], {})

    def test_young_healthy_no_factors(self):
        result = calculate_score({"age": 25})
        self.assertEqual(result["score"], 0)
        self.assertEqual(result["risk_tier"], "Very Low Risk")

    def test_all_factors_false(self):
        factors = {key: False for key, _, _ in RISK_FACTORS}
        factors["age"] = 30
        result = calculate_score(factors)
        self.assertEqual(result["score"], 0)

    def test_very_low_prophylaxis(self):
        result = calculate_score({})
        self.assertIn("Early ambulation", result["prophylaxis"][0])


class TestScoreHighestRisk(unittest.TestCase):
    """Score ≥7: highest risk tier."""

    def test_multiple_five_point_factors(self):
        """Multiple 5-point factors should easily exceed 7."""
        result = calculate_score({
            "age": 80,  # age_75_plus = 3
            "stroke_lt_1mo": True,  # 5
            "multiple_trauma_lt_1mo": True,  # 5
        })
        # 3 + 5 + 5 = 13
        self.assertEqual(result["score"], 13)
        self.assertEqual(result["risk_tier"], "Highest Risk")
        self.assertGreaterEqual(result["vte_rate"], 0.054)

    def test_accumulated_factors_reach_highest(self):
        """Many small factors accumulating to ≥7."""
        result = calculate_score({
            "age": 50,  # age_41_60 = 1
            "bmi_gt_25": True,  # 1
            "varicose_veins": True,  # 1
            "malignancy": True,  # 2
            "major_open_surgery_gt_45min": True,  # 2
            "central_venous_access": True,  # 2
        })
        # 1 + 1 + 1 + 2 + 2 + 2 = 9
        self.assertEqual(result["score"], 9)
        self.assertEqual(result["risk_tier"], "Highest Risk")

    def test_highest_risk_prophylaxis(self):
        result = calculate_score({
            "age": 80,
            "stroke_lt_1mo": True,
        })
        recs = result["prophylaxis"]
        self.assertTrue(any("Pharmacologic" in r for r in recs))
        self.assertTrue(any("Extended" in r or "extended" in r for r in recs))


class TestIndividualOnePointFactors(unittest.TestCase):
    """Test each 1-point factor individually."""

    def _check_single_factor(self, key, expected_pts=1):
        result = calculate_score({key: True})
        self.assertEqual(result["score"], expected_pts, f"Factor {key} should be {expected_pts}pt")
        self.assertIn(key, result["active_factors"])
        self.assertEqual(result["active_factors"][key], expected_pts)

    def test_age_41_60(self):
        result = calculate_score({"age": 50})
        self.assertEqual(result["score"], 1)
        self.assertIn("age_41_60", result["active_factors"])

    def test_minor_surgery(self):
        self._check_single_factor("minor_surgery_lt_45min")

    def test_bmi_gt_25(self):
        self._check_single_factor("bmi_gt_25")

    def test_swollen_legs(self):
        self._check_single_factor("swollen_legs")

    def test_varicose_veins(self):
        self._check_single_factor("varicose_veins")

    def test_pregnancy_or_postpartum(self):
        self._check_single_factor("pregnancy_or_postpartum")

    def test_recurrent_miscarriage(self):
        self._check_single_factor("recurrent_miscarriage")

    def test_oral_contraceptives_or_hrt(self):
        self._check_single_factor("oral_contraceptives_or_hrt")

    def test_sepsis_lt_1mo(self):
        self._check_single_factor("sepsis_lt_1mo")

    def test_serious_lung_disease(self):
        self._check_single_factor("serious_lung_disease_lt_1mo")

    def test_abnormal_pulmonary_function(self):
        self._check_single_factor("abnormal_pulmonary_function")

    def test_acute_mi(self):
        self._check_single_factor("acute_mi")

    def test_chf_lt_1mo(self):
        self._check_single_factor("chf_lt_1mo")

    def test_inflammatory_bowel_disease(self):
        self._check_single_factor("inflammatory_bowel_disease")

    def test_medical_patient_bed_rest(self):
        self._check_single_factor("medical_patient_bed_rest")


class TestIndividualTwoPointFactors(unittest.TestCase):
    """Test each 2-point factor individually."""

    def _check_single_factor(self, key, expected_pts=2):
        result = calculate_score({key: True})
        self.assertEqual(result["score"], expected_pts, f"Factor {key} should be {expected_pts}pt")
        self.assertIn(key, result["active_factors"])

    def test_age_61_74(self):
        result = calculate_score({"age": 70})
        self.assertEqual(result["score"], 2)
        self.assertIn("age_61_74", result["active_factors"])

    def test_arthroscopic_surgery(self):
        self._check_single_factor("arthroscopic_surgery_gt_45min")

    def test_major_open_surgery(self):
        self._check_single_factor("major_open_surgery_gt_45min")

    def test_laparoscopic_surgery(self):
        self._check_single_factor("laparoscopic_surgery_gt_45min")

    def test_malignancy(self):
        self._check_single_factor("malignancy")

    def test_bed_rest_gt_72h(self):
        self._check_single_factor("bed_rest_gt_72h")

    def test_immobilizing_plaster_cast(self):
        self._check_single_factor("immobilizing_plaster_cast")

    def test_central_venous_access(self):
        self._check_single_factor("central_venous_access")


class TestIndividualThreePointFactors(unittest.TestCase):
    """Test each 3-point factor individually."""

    def _check_single_factor(self, key, expected_pts=3):
        result = calculate_score({key: True})
        self.assertEqual(result["score"], expected_pts, f"Factor {key} should be {expected_pts}pt")
        self.assertIn(key, result["active_factors"])

    def test_age_75_plus(self):
        result = calculate_score({"age": 78})
        self.assertEqual(result["score"], 3)
        self.assertIn("age_75_plus", result["active_factors"])

    def test_history_of_vte(self):
        self._check_single_factor("history_of_vte")

    def test_family_history_of_vte(self):
        self._check_single_factor("family_history_of_vte")

    def test_factor_v_leiden(self):
        self._check_single_factor("factor_v_leiden")

    def test_prothrombin_20210a(self):
        self._check_single_factor("prothrombin_20210a")

    def test_lupus_anticoagulant(self):
        self._check_single_factor("lupus_anticoagulant")

    def test_anticardiolipin_antibodies(self):
        self._check_single_factor("anticardiolipin_antibodies")

    def test_elevated_homocysteine(self):
        self._check_single_factor("elevated_homocysteine")

    def test_hit(self):
        self._check_single_factor("hit")

    def test_other_thrombophilia(self):
        self._check_single_factor("other_thrombophilia")


class TestIndividualFivePointFactors(unittest.TestCase):
    """Test each 5-point factor individually."""

    def _check_single_factor(self, key, expected_pts=5):
        result = calculate_score({key: True})
        self.assertEqual(result["score"], expected_pts, f"Factor {key} should be {expected_pts}pt")
        self.assertIn(key, result["active_factors"])

    def test_stroke_lt_1mo(self):
        self._check_single_factor("stroke_lt_1mo")

    def test_multiple_trauma_lt_1mo(self):
        self._check_single_factor("multiple_trauma_lt_1mo")

    def test_elective_lea(self):
        self._check_single_factor("elective_lea")

    def test_hip_pelvis_leg_fracture(self):
        self._check_single_factor("hip_pelvis_leg_fracture_lt_1mo")

    def test_acute_spinal_cord_injury(self):
        self._check_single_factor("acute_spinal_cord_injury_lt_1mo")


class TestAgeBrackets(unittest.TestCase):
    """Test age bracket auto-selection logic."""

    def test_age_under_41_no_points(self):
        for age in [18, 25, 30, 40]:
            result = calculate_score({"age": age})
            self.assertEqual(result["score"], 0, f"Age {age} should score 0")

    def test_age_41_to_60(self):
        for age in [41, 50, 55, 60]:
            result = calculate_score({"age": age})
            self.assertEqual(result["score"], 1, f"Age {age} should score 1")
            self.assertIn("age_41_60", result["active_factors"])

    def test_age_61_to_74(self):
        for age in [61, 65, 70, 74]:
            result = calculate_score({"age": age})
            self.assertEqual(result["score"], 2, f"Age {age} should score 2")
            self.assertIn("age_61_74", result["active_factors"])

    def test_age_75_plus(self):
        for age in [75, 80, 90, 100]:
            result = calculate_score({"age": age})
            self.assertEqual(result["score"], 3, f"Age {age} should score 3")
            self.assertIn("age_75_plus", result["active_factors"])

    def test_age_boundary_40(self):
        result = calculate_score({"age": 40})
        self.assertEqual(result["score"], 0)

    def test_age_boundary_41(self):
        result = calculate_score({"age": 41})
        self.assertEqual(result["score"], 1)

    def test_age_boundary_60(self):
        result = calculate_score({"age": 60})
        self.assertEqual(result["score"], 1)

    def test_age_boundary_61(self):
        result = calculate_score({"age": 61})
        self.assertEqual(result["score"], 2)

    def test_age_boundary_74(self):
        result = calculate_score({"age": 74})
        self.assertEqual(result["score"], 2)

    def test_age_boundary_75(self):
        result = calculate_score({"age": 75})
        self.assertEqual(result["score"], 3)

    def test_age_string_input(self):
        """Age passed as string should still work."""
        result = calculate_score({"age": "68"})
        self.assertEqual(result["score"], 2)

    def test_direct_age_key_overrides(self):
        """Passing age_75_plus directly should work even without age."""
        result = calculate_score({"age_75_plus": True})
        self.assertEqual(result["score"], 3)


class TestRiskTiers(unittest.TestCase):
    """Test tier assignment for all score ranges."""

    def test_tier_very_low_score_0(self):
        r = calculate_score({})
        self.assertEqual(r["risk_tier"], "Very Low Risk")

    def test_tier_very_low_score_1(self):
        r = calculate_score({"age": 50})
        self.assertEqual(r["risk_tier"], "Very Low Risk")

    def test_tier_low_score_2(self):
        r = calculate_score({"age": 70})
        self.assertEqual(r["risk_tier"], "Low Risk")

    def test_tier_moderate_score_3(self):
        r = calculate_score({"age": 80})
        self.assertEqual(r["risk_tier"], "Moderate Risk")

    def test_tier_moderate_score_4(self):
        r = calculate_score({"age": 80, "bmi_gt_25": True})
        self.assertEqual(r["risk_tier"], "Moderate Risk")

    def test_tier_high_score_5(self):
        r = calculate_score({"stroke_lt_1mo": True})
        self.assertEqual(r["risk_tier"], "High Risk")

    def test_tier_high_score_6(self):
        r = calculate_score({"stroke_lt_1mo": True, "bmi_gt_25": True})
        self.assertEqual(r["risk_tier"], "High Risk")

    def test_tier_highest_score_7(self):
        r = calculate_score({"stroke_lt_1mo": True, "multiple_trauma_lt_1mo": True})
        # 5 + 5 = 10, but let's test a score of exactly 7
        r = calculate_score({
            "age": 80,  # 3
            "stroke_lt_1mo": True,  # 5
            "bmi_gt_25": True,  # 1
            "varicose_veins": True,  # 1
        })
        # 3 + 5 + 1 + 1 = 10 — too high. Let me try:
        r = calculate_score({
            "age": 80,  # 3
            "stroke_lt_1mo": True,  # 5
        })
        # 3 + 5 = 8
        self.assertEqual(r["risk_tier"], "Highest Risk")

    def test_tier_highest_score_exactly_7(self):
        """Score of exactly 7 should be Highest Risk."""
        r = calculate_score({
            "age": 75,  # 3
            "history_of_vte": True,  # 3
            "bmi_gt_25": True,  # 1
        })
        # 3 + 3 + 1 = 7
        self.assertEqual(r["score"], 7)
        self.assertEqual(r["risk_tier"], "Highest Risk")


class TestClinicalScenarios(unittest.TestCase):
    """Test realistic clinical scenarios."""

    def test_orthopedic_hip_replacement(self):
        """78-year-old with elective hip arthroplasty, BMI 28, varicose veins."""
        result = calculate_score({
            "age": 78,  # 3
            "elective_lea": True,  # 5
            "bmi_gt_25": True,  # 1
            "varicose_veins": True,  # 1
        })
        # 3 + 5 + 1 + 1 = 10
        self.assertEqual(result["score"], 10)
        self.assertEqual(result["risk_tier"], "Highest Risk")
        # Should have extended prophylaxis for LEA
        self.assertTrue(any("arthroplasty" in e.lower() for e in result["extended_prophylaxis"]))

    def test_cancer_surgery_patient(self):
        """66-year-old with colon cancer, major open surgery, central line, BMI 27."""
        result = calculate_score({
            "age": 66,  # 2
            "malignancy": True,  # 2
            "major_open_surgery_gt_45min": True,  # 2
            "central_venous_access": True,  # 2
            "bmi_gt_25": True,  # 1
        })
        # 2 + 2 + 2 + 2 + 1 = 9
        self.assertEqual(result["score"], 9)
        self.assertEqual(result["risk_tier"], "Highest Risk")
        # Should flag extended prophylaxis for cancer surgery
        self.assertTrue(len(result["extended_prophylaxis"]) > 0)
        self.assertTrue(any("cancer" in e.lower() for e in result["extended_prophylaxis"]))

    def test_trauma_patient(self):
        """52-year-old with multiple trauma, hip fracture, spinal cord injury."""
        result = calculate_score({
            "age": 52,  # 1
            "multiple_trauma_lt_1mo": True,  # 5
            "hip_pelvis_leg_fracture_lt_1mo": True,  # 5
            "acute_spinal_cord_injury_lt_1mo": True,  # 5
        })
        # 1 + 5 + 5 + 5 = 16
        self.assertEqual(result["score"], 16)
        self.assertEqual(result["risk_tier"], "Highest Risk")
        self.assertTrue(any("trauma" in e.lower() for e in result["extended_prophylaxis"]))

    def test_young_healthy_medical_patient(self):
        """30-year-old admitted for pneumonia, bed rest."""
        result = calculate_score({
            "age": 30,  # 0
            "serious_lung_disease_lt_1mo": True,  # 1
            "medical_patient_bed_rest": True,  # 1
        })
        # 0 + 1 + 1 = 2
        self.assertEqual(result["score"], 2)
        self.assertEqual(result["risk_tier"], "Low Risk")

    def test_middle_aged_with_thrombophilia(self):
        """48-year-old with Factor V Leiden and family history of VTE."""
        result = calculate_score({
            "age": 48,  # 1
            "factor_v_leiden": True,  # 3
            "family_history_of_vte": True,  # 3
        })
        # 1 + 3 + 3 = 7
        self.assertEqual(result["score"], 7)
        self.assertEqual(result["risk_tier"], "Highest Risk")

    def test_postpartum_with_complications(self):
        """35-year-old postpartum with DVT history."""
        result = calculate_score({
            "age": 35,  # 0
            "pregnancy_or_postpartum": True,  # 1
            "history_of_vte": True,  # 3
        })
        # 0 + 1 + 3 = 4
        self.assertEqual(result["score"], 4)
        self.assertEqual(result["risk_tier"], "Moderate Risk")

    def test_elderly_medical_patient(self):
        """82-year-old medical patient with CHF, bed rest, sepsis."""
        result = calculate_score({
            "age": 82,  # 3
            "chf_lt_1mo": True,  # 1
            "medical_patient_bed_rest": True,  # 1
            "sepsis_lt_1mo": True,  # 1
        })
        # 3 + 1 + 1 + 1 = 6
        self.assertEqual(result["score"], 6)
        self.assertEqual(result["risk_tier"], "High Risk")


class TestProphylaxisRecommendations(unittest.TestCase):
    """Test that each tier returns the correct prophylaxis recommendations."""

    def test_very_low_prophylaxis(self):
        r = calculate_score({})
        self.assertEqual(r["prophylaxis"], PROPHYLAXIS_RECOMMENDATIONS["Very Low Risk"])

    def test_low_prophylaxis(self):
        r = calculate_score({"age": 70})  # score = 2
        self.assertEqual(r["prophylaxis"], PROPHYLAXIS_RECOMMENDATIONS["Low Risk"])

    def test_moderate_prophylaxis(self):
        r = calculate_score({"age": 80})  # score = 3
        self.assertEqual(r["prophylaxis"], PROPHYLAXIS_RECOMMENDATIONS["Moderate Risk"])

    def test_high_prophylaxis(self):
        r = calculate_score({"stroke_lt_1mo": True})  # score = 5
        self.assertEqual(r["prophylaxis"], PROPHYLAXIS_RECOMMENDATIONS["High Risk"])

    def test_highest_prophylaxis(self):
        r = calculate_score({"stroke_lt_1mo": True, "multiple_trauma_lt_1mo": True})
        self.assertEqual(r["prophylaxis"], PROPHYLAXIS_RECOMMENDATIONS["Highest Risk"])

    def test_highest_mentions_extended(self):
        r = calculate_score({"stroke_lt_1mo": True, "multiple_trauma_lt_1mo": True})
        self.assertTrue(any("extended" in rec.lower() for r in r["prophylaxis"] for rec in [r]))


class TestExtendedProphylaxis(unittest.TestCase):
    """Test extended prophylaxis flagging."""

    def test_cancer_surgery_flags_extended(self):
        r = calculate_score({
            "malignancy": True,
            "major_open_surgery_gt_45min": True,
        })
        self.assertTrue(len(r["extended_prophylaxis"]) > 0)
        self.assertTrue(any("cancer" in e.lower() for e in r["extended_prophylaxis"]))

    def test_lea_flags_extended(self):
        r = calculate_score({"elective_lea": True})
        self.assertTrue(any("arthroplasty" in e.lower() for e in r["extended_prophylaxis"]))

    def test_hip_fracture_flags_extended(self):
        r = calculate_score({"hip_pelvis_leg_fracture_lt_1mo": True})
        self.assertTrue(any("hip" in e.lower() or "fracture" in e.lower()
                            for e in r["extended_prophylaxis"]))

    def test_trauma_flags_extended(self):
        r = calculate_score({"multiple_trauma_lt_1mo": True})
        self.assertTrue(any("trauma" in e.lower() for e in r["extended_prophylaxis"]))

    def test_no_extended_for_low_risk(self):
        r = calculate_score({"age": 50, "bmi_gt_25": True})
        self.assertEqual(len(r["extended_prophylaxis"]), 0)

    def test_laparoscopic_cancer_surgery_flags_extended(self):
        r = calculate_score({
            "malignancy": True,
            "laparoscopic_surgery_gt_45min": True,
        })
        self.assertTrue(any("cancer" in e.lower() for e in r["extended_prophylaxis"]))


class TestBleedingConsiderations(unittest.TestCase):
    """Test that bleeding risk considerations are always included."""

    def test_bleeding_considerations_present(self):
        r = calculate_score({})
        self.assertEqual(len(r["bleeding_considerations"]), len(BLEEDING_RISK_CONSIDERATIONS))
        self.assertTrue(any("bleeding" in b.lower() for b in r["bleeding_considerations"]))


class TestFormatReport(unittest.TestCase):
    """Test the report formatting function."""

    def test_report_contains_score(self):
        r = calculate_score({"age": 50})
        report = format_report(r)
        self.assertIn("Total Score: 1", report)

    def test_report_contains_tier(self):
        r = calculate_score({"age": 50})
        report = format_report(r)
        self.assertIn("Very Low Risk", report)

    def test_report_contains_patient_id(self):
        r = calculate_score({"age": 50})
        report = format_report(r, patient_id="P001")
        self.assertIn("P001", report)

    def test_report_contains_disclaimer(self):
        r = calculate_score({})
        report = format_report(r)
        self.assertIn("DISCLAIMER", report)
        self.assertIn("clinical judgment", report.lower())

    def test_report_lists_active_factors(self):
        r = calculate_score({"age": 50, "bmi_gt_25": True})
        report = format_report(r)
        self.assertIn("BMI", report)

    def test_report_no_factors_message(self):
        r = calculate_score({})
        report = format_report(r)
        self.assertIn("(none)", report)


class TestGetAllFactors(unittest.TestCase):
    """Test the get_all_factors utility."""

    def test_returns_all_factors(self):
        factors = get_all_factors()
        self.assertEqual(len(factors), len(RISK_FACTORS))

    def test_factor_structure(self):
        factors = get_all_factors()
        for f in factors:
            self.assertIn("key", f)
            self.assertIn("label", f)
            self.assertIn("points", f)
            self.assertIn(f["points"], [1, 2, 3, 5])


class TestTotalFactorCount(unittest.TestCase):
    """Verify we have the correct number of factors in each category."""

    def test_one_point_factors(self):
        count = sum(1 for _, _, pts in RISK_FACTORS if pts == 1)
        self.assertEqual(count, 15)

    def test_two_point_factors(self):
        count = sum(1 for _, _, pts in RISK_FACTORS if pts == 2)
        self.assertEqual(count, 8)

    def test_three_point_factors(self):
        count = sum(1 for _, _, pts in RISK_FACTORS if pts == 3)
        self.assertEqual(count, 10)

    def test_five_point_factors(self):
        count = sum(1 for _, _, pts in RISK_FACTORS if pts == 5)
        self.assertEqual(count, 5)

    def test_total_factors(self):
        self.assertEqual(len(RISK_FACTORS), 38)


class TestCLI(unittest.TestCase):
    """Test CLI commands."""

    def test_score_with_flags(self):
        from cli import main
        # Capture stdout
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            rc = main(["score", "--age", "68", "--malignancy",
                        "--major-open-surgery-gt-45min"])
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        self.assertEqual(rc, 0)
        self.assertIn("Total Score", output)
        # age 68=2 + malignancy=2 + major surgery=2 = 6 -> High Risk
        self.assertIn("High Risk", output)

    def test_score_with_json(self):
        from cli import main
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            rc = main(["score", "--json",
                        '{"age": 68, "malignancy": true, "major_open_surgery_gt_45min": true}'])
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        self.assertEqual(rc, 0)
        self.assertIn("Total Score", output)

    def test_factors_command(self):
        from cli import main
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            rc = main(["factors"])
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        self.assertEqual(rc, 0)
        self.assertIn("Caprini VTE Risk Factors", output)
        self.assertIn("age_41_60", output)

    def test_batch_command(self):
        from cli import main
        # Create a temp CSV
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False,
                                          newline="") as f:
            f.write("patient_id,age,malignancy,major_open_surgery_gt_45min\n")
            f.write("P001,68,1,1\n")
            f.write("P002,30,0,0\n")
            input_path = f.name

        output_path = input_path.replace(".csv", "_out.csv")
        try:
            import io
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            try:
                rc = main(["batch", "-i", input_path, "-o", output_path])
                output = sys.stdout.getvalue()
            finally:
                sys.stdout = old_stdout
            self.assertEqual(rc, 0)
            self.assertIn("Processed 2", output)

            # Verify output CSV
            with open(output_path, newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            self.assertEqual(len(rows), 2)
            self.assertEqual(int(rows[0]["caprini_score"]), 6)  # age 68=2 + malignancy=2 + surgery=2
            self.assertEqual(int(rows[1]["caprini_score"]), 0)
        finally:
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_no_command_returns_1(self):
        from cli import main
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            rc = main([])
        finally:
            sys.stdout = old_stdout
        self.assertEqual(rc, 1)


class TestInputVariations(unittest.TestCase):
    """Test various input formats and edge cases."""

    def test_string_true_values(self):
        r1 = calculate_score({"malignancy": "yes"})
        r2 = calculate_score({"malignancy": "true"})
        r3 = calculate_score({"malignancy": "1"})
        self.assertEqual(r1["score"], 2)
        self.assertEqual(r2["score"], 2)
        self.assertEqual(r3["score"], 2)

    def test_integer_1_value(self):
        r = calculate_score({"malignancy": 1})
        self.assertEqual(r["score"], 2)

    def test_none_value_ignored(self):
        r = calculate_score({"malignancy": None})
        self.assertEqual(r["score"], 0)

    def test_unknown_keys_ignored(self):
        r = calculate_score({"age": 50, "some_random_field": True, "another": "yes"})
        self.assertEqual(r["score"], 1)  # only age_41_60

    def test_score_accumulates_correctly(self):
        """Verify additive scoring across point categories."""
        r = calculate_score({
            "age": 50,          # 1
            "malignancy": True, # 2
            "history_of_vte": True,  # 3
            "stroke_lt_1mo": True,   # 5
        })
        self.assertEqual(r["score"], 11)

    def test_result_dict_keys(self):
        r = calculate_score({})
        expected_keys = {"score", "risk_tier", "vte_rate", "prophylaxis",
                         "active_factors", "extended_prophylaxis",
                         "bleeding_considerations"}
        self.assertEqual(set(r.keys()), expected_keys)


if __name__ == "__main__":
    unittest.main()
