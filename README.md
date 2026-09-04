# Caprini VTE Risk Assessment & Thromboprophylaxis Engine

A clinically validated, pure Python risk assessment engine implementing the **Caprini Risk Assessment Model (RAM) for Venous Thromboembolism (VTE)** (Caprini JA. *Dis Mon* 2005; revised 2009/2013) and American College of Chest Physicians (**ACCP/CHEST 2012**) perioperative thromboprophylaxis clinical practice guidelines.

---

## Caprini Risk Assessment Model (RAM) Architecture

The Caprini score stratifies surgical and medical inpatients into evidence-based VTE risk tiers to guide mechanical and pharmacological thromboprophylaxis.

### Point Valuation Schema

| Point Value | Risk Factors |
|:---|:---|
| **1 Point Each** | Age 41–60 yrs, Minor surgery, BMI $> 25\text{ kg/m}^2$, Swollen legs, Varicose veins, Pregnancy / postpartum ($<1\text{ mo}$), History of unexplained abortion ($\ge 3$), Oral contraceptives / HRT, Sepsis ($<1\text{ mo}$), Serious lung disease / pneumonia ($<1\text{ mo}$), Abnormal pulmonary function, Acute MI ($<1\text{ mo}$), CHF ($<1\text{ mo}$), History of inflammatory bowel disease, Medical patient on bed rest |
| **2 Points Each** | Age 61–74 yrs, Major open surgery ($>45\text{ min}$), Laparoscopic surgery ($>45\text{ min}$), Malignancy (present or previous), Confined to bed ($>72\text{ hours}$), Immobilizing plaster cast, Central venous access |
| **3 Points Each** | Age $\ge 75\text{ yrs}$, History of VTE (DVT/PE), Family history of VTE, Factor V Leiden, Prothrombin 20210A, Elevated serum homocysteine, Positive lupus anticoagulant, Elevated anticardiolipin antibodies, Other congenital/acquired thrombophilia |
| **5 Points Each** | Elective major lower extremity arthroplasty (total hip/knee), Hip / pelvis / leg fracture ($<1\text{ mo}$), Stroke ($<1\text{ mo}$), Multiple trauma ($<1\text{ mo}$), Acute spinal cord injury ($<1\text{ mo}$) |

---

### Risk Categories & CHEST 2012 Recommendations

| Caprini Score | Risk Tier | 30-Day VTE Risk (No Prophylaxis) | Recommended Prophylaxis |
|:---|:---|:---|:---|
| **0** | **Lowest Risk** | $\sim 0.5\%$ | Early, frequent ambulation alone |
| **1 – 2** | **Low Risk** | $\sim 1.5\%$ | Mechanical prophylaxis: Intermittent Pneumatic Compression (IPC) devices |
| **3 – 4** | **Moderate Risk** | $\sim 3.0\%$ | Pharmacological (LMWH or low-dose UFH) OR Mechanical (IPC); dual if high bleeding risk |
| **5 – 8** | **High Risk** | $\sim 6.0\%$ | Pharmacological (LMWH or low-dose UFH) AND Mechanical (IPC/GCS) dual prophylaxis |
| $\ge 9$ | **Highest Risk** | $\sim 11.0\%$ | Pharmacological (LMWH or low-dose UFH) AND Mechanical (IPC) extended duration (e.g. 28–35 days for major abdominal/pelvic cancer or orthopedic surgery) |

---

## Features

- **Standardized Caprini RAM Scoring:** Evaluates comprehensive clinical, surgical, and hypercoagulable risk factors.
- **Bleeding Risk Harmonization:** Balances thrombosis prevention against surgical bleeding risk.
- **Batch CSV Processing:** High-throughput batch triage for hospital pre-admission and surgical scheduling workflows.
- **Zero Runtime Dependencies:** Pure Python implementation relying strictly on the Python Standard Library.

---

## Installation & Requirements

- Python 3.10+ (tested on 3.10, 3.11, 3.12)
- Zero external runtime dependencies.

```bash
git clone https://github.com/abusuraihsakhri/caprini-vte-risk-calculator.git
cd caprini-vte-risk-calculator
```

---

## CLI Usage

### 1. Calculate Score for a Surgical Patient
```bash
python cli.py calc --age 68 --major-open-surgery-gt-45min --malignancy --central-venous-access
```

### 2. High-Risk Orthopedic Arthroplasty Case
```bash
python cli.py calc --age 76 --elective-major-lower-extremity-arthroplasty --prior-vte
```

### 3. Batch Process Patient Cohorts from CSV
```bash
python cli.py batch -i sample.csv -o results.csv
```

---

## Python API Quickstart

```python
from caprini import calculate_caprini_score, CapriniFactors

factors = CapriniFactors(
    age=65,
    major_open_surgery_gt_45min=True,
    malignancy=True,
    central_venous_access=True
)

result = calculate_caprini_score(factors)
print(f"Caprini Score: {result.score}")
print(f"Risk Category: {result.risk_level.value}")
print(f"Recommended Prophylaxis: {result.recommended_prophylaxis}")
```

---

## Testing & Verification

Run the test suite:

```bash
python -m pytest -p no:zarr
```

