# CAPRINI Vte Risk Calculator

> **Domain:** Clinical Decision Support & Biomedical Computing  
> **Reference Guidelines & Standards:** `Standard Clinical Formulations & ISO/IEC Quality Frameworks`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

Bleeding Risk Stratification for Caprini VTE Risk Calculator.
Stratifies patients by surgical bleeding risk to guide VTE prophylaxis decisions.

Caprini VTE Risk Score Calculator.

Implements the Caprini Risk Assessment Model for Venous Thromboembolism (VTE)
in surgical patients. This is a validated, point-based scoring system published
by Joseph A. Caprini (2005, revised 2009/2013) and widely adopted in surgical
practice for VTE risk stratification and prophylaxis guidance.

Reference:
  Caprini JA. Thrombosis risk assessment as a guide to quality patient care.
  Dis Mon. 2005;51(2-3):70-78.

Stdlib only — no third-party dependencies.

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Core Algorithmic & Evaluation Engines

- **`BleedingRiskFactors`**: Patient bleeding risk factors.
- **`BleedingRiskAgent`**: Sub-agent for bleeding risk stratification.
- **`CapriniFactors`**: Set boolean flags for every applicable factor; age handled separately.
- **`Snapshot`** — dedicated module for snapshot evaluation and state verification.
- **`PharmacogenomicProfile`**: Patient pharmacogenomic profile.
- **`PharmacogenomicAgent`**: Sub-agent for pharmacogenomic prophylaxis.

---

## 📐 Mathematical Formulation & Logic

```text
  """Calculate surgical bleeding risk score."""
  score = 0
  bleeding_risk = "VERY_HIGH"
  bleeding_risk = "HIGH"
  bleeding_risk = "MODERATE"
```

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py --age <value> --malignancy <value> --major-open-surgery-gt-45min <value> --json <value>
```

### Parameter Reference
- `--age`: Specifies input measurement or parameter value.
- `--malignancy`: Specifies input measurement or parameter value.
- `--major-open-surgery-gt-45min`: Specifies input measurement or parameter value.
- `--json`: Specifies input measurement or parameter value.
- `---`: Specifies input measurement or parameter value.
- `--patient-id`: Specifies input measurement or parameter value.
- `--json-output`: Specifies input measurement or parameter value.
- `--input`: Specifies input measurement or parameter value.
- `--output`: Specifies input measurement or parameter value.

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `patient_id` | Parameter / observation metric | Required |
| `age` | Parameter / observation metric | Required |
| `sex` | Parameter / observation metric | Required |
| `prior_vte` | Parameter / observation metric | Required |
| `cancer` | Parameter / observation metric | Required |
| `immobility` | Parameter / observation metric | Required |
| `surgery` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t caprini-vte-risk-calculator .
docker run -p 8000:8000 caprini-vte-risk-calculator
```
