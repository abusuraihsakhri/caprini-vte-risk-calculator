#!/usr/bin/env python3
"""Command-line interface for the Caprini VTE risk calculator."""

from __future__ import annotations

import argparse
import csv
import json
import sys

from caprini import AGE_KEYS, RISK_FACTORS, calculate_score, format_report, get_all_factors

TRUE_VALUES = {"1", "true", "yes", "y", "present"}

COLUMN_ALIASES = {
    "minor_surgery": "minor_surgery_lt_45min",
    "minor_surgery_planned": "minor_surgery_lt_45min",
    "arthroscopy": "arthroscopic_surgery",
    "arthroscopic_surgery_gt_45min": "arthroscopic_surgery",
    "major_surgery": "major_open_surgery_gt_45min",
    "major_open_surgery": "major_open_surgery_gt_45min",
    "major_surgery_gt_45min": "major_open_surgery_gt_45min",
    "laparoscopic": "laparoscopic_surgery_gt_45min",
    "laparoscopic_surgery": "laparoscopic_surgery_gt_45min",
    "elective_arthroplasty": "elective_lea",
    "arthroplasty": "elective_lea",
    "cancer": "malignancy",
    "malignancy_present": "malignancy",
    "bed_rest": "bed_rest_gt_72h",
    "immobility": "bed_rest_gt_72h",
    "central_line": "central_venous_access",
    "prior_vte": "history_of_vte",
    "dvt_pe_history": "history_of_vte",
    "family_vte": "family_history_of_vte",
    "stroke": "stroke_lt_1mo",
    "spinal_cord_injury": "acute_spinal_cord_injury_lt_1mo",
    "trauma": "multiple_trauma_lt_1mo",
    "sepsis": "sepsis_lt_1mo",
    "antiphospholipid": "lupus_anticoagulant",
}


def _is_true(value: object) -> bool:
    return str(value).strip().lower() in TRUE_VALUES


def _add_factor_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--age", type=float, default=None, help="Patient age in years")
    for key, label, points in RISK_FACTORS:
        parser.add_argument(
            "--" + key.replace("_", "-"),
            action="store_true",
            default=False,
            help=f"[{points} pt] {label}",
        )


def _args_to_factors(args: argparse.Namespace) -> dict:
    factors = {}
    if args.age is not None:
        factors["age"] = args.age
    for key, _, _ in RISK_FACTORS:
        if getattr(args, key, False):
            factors[key] = True
    return factors


def cmd_score(args: argparse.Namespace) -> int:
    try:
        factors = json.loads(args.json) if args.json else _args_to_factors(args)
        if not isinstance(factors, dict):
            raise ValueError("JSON input must be an object")
        result = calculate_score(factors)
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(format_report(result, patient_id=args.patient_id))
    if args.json_output:
        print("\n--- JSON Output ---")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def cmd_factors(_: argparse.Namespace) -> int:
    print("Caprini VTE risk factors")
    print("=" * 64)
    current_points = None
    for factor in get_all_factors():
        if factor["points"] != current_points:
            current_points = factor["points"]
            print(f"\n{current_points}-point factors")
        print(f"  {factor['key']:42s} {factor['label']}")
    return 0


def _row_to_factors(row: dict) -> dict:
    normalized = {
        str(key).strip().lower().replace("-", "_"): value
        for key, value in row.items()
        if key is not None
    }
    factors = {}

    for age_column in ("age", "age_years"):
        value = normalized.get(age_column)
        if value not in (None, ""):
            try:
                factors["age"] = float(value)
            except (TypeError, ValueError):
                pass
            break

    for bmi_column in ("bmi", "body_mass_index"):
        value = normalized.get(bmi_column)
        if value not in (None, ""):
            try:
                if float(value) > 25:
                    factors["bmi_gt_25"] = True
            except (TypeError, ValueError):
                pass
            break

    for key, _, _ in RISK_FACTORS:
        if key in AGE_KEYS:
            continue
        if _is_true(normalized.get(key, "")):
            factors[key] = True

    for alias, target in COLUMN_ALIASES.items():
        if _is_true(normalized.get(alias, "")):
            factors[target] = True

    return factors


def cmd_batch(args: argparse.Namespace) -> int:
    try:
        with open(args.input, newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                print("Error: input CSV has no header", file=sys.stderr)
                return 2
            fieldnames = list(reader.fieldnames)
            rows = list(reader)
    except FileNotFoundError:
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        return 2

    added_fields = ["caprini_score", "risk_tier", "vte_rate", "active_factors", "prophylaxis_summary"]
    out_fields = fieldnames + [field for field in added_fields if field not in fieldnames]
    out_rows = []

    for line_number, row in enumerate(rows, start=2):
        try:
            result = calculate_score(_row_to_factors(row))
        except ValueError as exc:
            print(f"Error on CSV line {line_number}: {exc}", file=sys.stderr)
            return 2
        output = dict(row)
        output["caprini_score"] = result["score"]
        output["risk_tier"] = result["risk_tier"]
        output["vte_rate"] = f"{result['vte_rate']:.1%}"
        output["active_factors"] = "; ".join(
            f"{key}({points})" for key, points in result["active_factors"].items()
        )
        output["prophylaxis_summary"] = " | ".join(result["prophylaxis"])
        out_rows.append(output)

    with open(args.output, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Processed {len(out_rows)} records -> {args.output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="caprini",
        description="Caprini VTE risk score calculator (CHEST 2012 general/abdominal-pelvic surgery mapping)",
    )
    subparsers = parser.add_subparsers(dest="command")

    score = subparsers.add_parser("score", help="Calculate one Caprini score")
    _add_factor_args(score)
    score.add_argument("--json", default=None, help="JSON object of factors; overrides flags")
    score.add_argument("--patient-id", default=None, help="Optional local report identifier")
    score.add_argument("--json-output", action="store_true", help="Print machine-readable result")

    subparsers.add_parser("factors", help="List factor keys and point values")

    batch = subparsers.add_parser("batch", help="Batch-process a CSV file")
    batch.add_argument("-i", "--input", required=True, help="Input CSV path")
    batch.add_argument("-o", "--output", default="results.csv", help="Output CSV path")
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "score":
        return cmd_score(args)
    if args.command == "factors":
        return cmd_factors(args)
    if args.command == "batch":
        return cmd_batch(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
