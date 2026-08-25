# Caprini VTE Risk Score Calculator

A Python implementation of the **Caprini Risk Assessment Model for Venous Thromboembolism (VTE)** in surgical patients.

This is a validated, point-based scoring system used to stratify surgical and hospitalized patients by their risk of developing VTE, and to guide appropriate prophylaxis decisions.

## What This Tool Does

1. **Scores patients** using the 40-factor Caprini model (0–~50 point range)
2. **Stratifies risk** into five tiers: Very Low, Low, Moderate, High, Highest
3. **Recommends prophylaxis** aligned with ACCP guidelines for each tier
4. **Flags extended prophylaxis** needs for cancer surgery, arthroplasty, and trauma
5. **Provides bleeding risk guidance** to balance VTE prevention against hemorrhage

## Risk Factor Summary

| Points | Factors |
|--------|---------|
| **1** | Age 41-60, minor surgery (<45 min), BMI >25, swollen legs, varicose veins, pregnancy/postpartum, recurrent miscarriage, OCP/HRT, sepsis <1mo, lung disease <1mo, abnormal PFTs, acute MI, CHF <1mo, IBD, bed rest |
| **2** | Age 61-74, arthroscopic surgery (>45 min), major open surgery (>45 min), laparoscopic surgery (>45 min), malignancy, bed rest >72h, immobilizing cast, central venous access |
| **3** | Age ≥75, history of VTE, family history of VTE, Factor V Leiden, Prothrombin 20210A, lupus anticoagulant, anticardiolipin antibodies, elevated homocysteine, HIT, other thrombophilia |
| **5** | Stroke <1mo, multiple trauma <1mo, elective major LEA, hip/pelvis/leg fracture <1mo, acute spinal cord injury <1mo |

## Risk Tiers

| Score | Tier | VTE Rate (no prophylaxis) | Recommendation |
|-------|------|---------------------------|----------------|
| 0–1 | Very Low | ~0.0% | Early ambulation only |
| 2 | Low | ~0.7% | Sequential compression devices (SCDs) |
| 3–4 | Moderate | ~1.8% | SCDs ± pharmacologic prophylaxis |
| 5–6 | High | ~3.6% | Pharmacologic prophylaxis recommended |
| ≥7 | Highest | ~5.4%+ | Pharmacologic + extended duration |

## Quick Start

### Python API

```python
from caprini import calculate_score, format_report

result = calculate_score({
    "age": 68,
    "malignancy": True,
    "major_open_surgery_gt_45min": True,
    "central_venous_access": True,
    "bmi_gt_25": True,
})

print(format_report(result))
# Score: 8, Tier: Highest Risk, VTE rate: 5.4%+
```

### CLI

```bash
# Score a single patient with flags
python cli.py score --age 68 --malignancy --major-open-surgery-gt-45min

# Score from JSON
python cli.py score --json '{"age": 68, "malignancy": true, "major_open_surgery_gt_45min": true}'

# List all risk factors
python cli.py factors

# Batch process a CSV
python cli.py batch -i patients.csv -o results.csv
```

### CSV Batch Format

The batch command expects a CSV with an optional `age` column and columns matching factor keys:

```csv
patient_id,age,malignancy,major_open_surgery_gt_45min,history_of_vte
P001,68,1,1,0
P002,45,0,0,1
```

## Running Tests

```bash
python -m pytest test_caprini.py -v
```

Or without pytest (stdlib unittest):

```bash
python -m unittest test_caprini -v
```

## Project Structure

```
caprini.py              — Core scoring engine (calculate_score, format_report)
cli.py                  — Command-line interface
test_caprini.py         — Test suite
bleeding_risk.py        — Bleeding risk stratification module
caprini_point_table.py  — Reference point table (older module)
perioperative_tracker.py — Serial Caprini tracking across perioperative period
pharmacogenomic_prophylaxis.py — PGx-adjusted prophylaxis guidance
```

## Limitations

- This tool is for **clinical decision support only**. It does not replace clinical judgment.
- The Caprini model was developed and validated primarily in surgical populations. Its performance in purely medical patients is less well-established.
- VTE rate estimates are population-level averages and may not reflect individual patient risk.
- Always consider the complete clinical picture including bleeding risk, patient preferences, and institutional protocols.

## References

- Caprini JA. Thrombosis risk assessment as a guide to quality patient care. *Dis Mon*. 2005;51(2-3):70-78.
- Caprini JA. Individual risk assessment is the best strategy for thromboembolic prophylaxis. *Dis Mon*. 2010;56(8):552-559.
- Gould MK, et al. Prevention of VTE in nonorthopedic surgical patients: Antithrombotic Therapy and Prevention of Thrombosis, 9th ed: ACCP Evidence-Based Clinical Practice Guidelines. *Chest*. 2012;141(2 Suppl):e227S-e277S.

## License

MIT
