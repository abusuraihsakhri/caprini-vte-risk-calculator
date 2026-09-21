# Caprini VTE Risk Calculator

### [Open the Live Application →](https://abusuraihsakhri.github.io/caprini-vte-risk-calculator/)

A small, dependency-free implementation of the Caprini venous thromboembolism (VTE) risk score, with a browser interface and command-line tools.

The risk-factor weights follow the Caprini table reproduced in the 2012 American College of Chest Physicians (CHEST/AT9) guideline for nonorthopedic surgical patients. The displayed VTE strata and prophylaxis summary are scoped to **general and abdominal-pelvic surgery** in that guideline; orthopedic, trauma, spinal-cord-injury, and other populations require their relevant specialty guidance.

## Features

- 38 Caprini risk factors with automatic age scoring.
- CHEST/AT9 strata: score 0 very low, 1–2 low, 3–4 moderate, and ≥5 high risk.
- Conditional prophylaxis summary without hard-coded drug doses.
- Batch CSV processing and human-readable CLI reports.
- Static browser calculator that runs entirely on-device; no patient data is sent to a server.
- Light and dark themes, keyboard-accessible controls, and a compact responsive layout.
- Python standard library only at runtime.

## Browser application

The `web/` directory is a static GitHub Pages application. It uses a small JavaScript scoring module rather than Pyodide so the calculator loads quickly and has no Python/WASM runtime dependency. CI runs browser scoring smoke tests to reduce drift from the Python implementation.

## CLI

```bash
python cli.py score --age 68 --malignancy --major-open-surgery-gt-45min
python cli.py score --json '{"age": 68, "malignancy": true}' --json-output
python cli.py factors
python cli.py batch -i sample.csv -o results.csv
```

## Python API

```python
from caprini import calculate_score

result = calculate_score({
    "age": 68,
    "malignancy": True,
    "major_open_surgery_gt_45min": True,
})

print(result["score"])
print(result["risk_tier"])
```

## Testing

```bash
python -m pip install pytest
python -m pytest -q
node web/test.mjs
```

GitHub Actions tests Python 3.10–3.13 and the browser scoring module.

## Clinical scope

This repository is a clinical decision-support and educational implementation. It does not diagnose VTE, assess all bleeding contraindications, or replace institutional policy or clinician judgment. The CHEST 2012 prophylaxis mapping used here is population-specific and should not be generalized to every surgical or medical population.

Primary references:

- Caprini JA. *Thrombosis risk assessment as a guide to quality patient care.* Dis Mon. 2005;51(2-3):70-78.
- Gould MK, Garcia DA, Wren SM, et al. *Prevention of VTE in Nonorthopedic Surgical Patients: Antithrombotic Therapy and Prevention of Thrombosis, 9th ed.* Chest. 2012;141(2 Suppl):e227S-e277S.
- Cronin M, Dengler N, Krauss ES, et al. *Completion of the Updated Caprini Risk Assessment Model (2013 Version).* Clin Appl Thromb Hemost. 2019;25:1076029619838052.

## Privacy

The browser version performs all calculations locally and does not transmit form values. The CLI and Python API perform local computation only.

## License

MIT. See `LICENSE`.
