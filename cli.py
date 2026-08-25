#!/usr/bin/env python3
"""
CLI for the Caprini VTE Risk Score Calculator.

Usage:
    python cli.py score --age 65 --malignancy --major-open-surgery-gt-45min
    python cli.py score --json '{"age": 65, "malignancy": true, "major_open_surgery_gt_45min": true}'
    python cli.py factors
    python cli.py batch -i input.csv -o results.csv

Stdlib only.
"""

import argparse
import csv
import json
import sys

from caprini import (
    calculate_score,
    format_report,
    get_all_factors,
    FACTOR_POINTS,
    RISK_FACTORS,
    AGE_KEYS,
)


def _add_factor_args(parser: argparse.ArgumentParser) -> None:
    """Add a CLI flag for every Caprini risk factor."""
    parser.add_argument("--age", type=float, default=None,
                        help="Patient age (auto-selects age bracket)")
    for key, label, pts in RISK_FACTORS:
        flag = "--" + key.replace("_", "-")
        parser.add_argument(flag, action="store_true", default=False,
                            help=f"[{pts}pt] {label}")


def _args_to_factors(args: argparse.Namespace) -> dict:
    """Convert parsed argparse namespace into a factors dict."""
    factors = {}
    if args.age is not None:
        factors["age"] = args.age
    for key, _, _ in RISK_FACTORS:
        if getattr(args, key, False):
            factors[key] = True
    return factors


def cmd_score(args: argparse.Namespace) -> int:
    """Handle the 'score' subcommand."""
    if args.json:
        try:
            factors = json.loads(args.json)
        except json.JSONDecodeError as e:
            print(f"Error: invalid JSON: {e}", file=sys.stderr)
            return 1
    else:
        factors = _args_to_factors(args)

    result = calculate_score(factors)
    report = format_report(result, patient_id=args.patient_id)
    print(report)

    if args.json_output:
        print("\n--- JSON Output ---")
        print(json.dumps(result, indent=2))

    return 0


def cmd_factors(args: argparse.Namespace) -> int:
    """Handle the 'factors' subcommand — list all risk factors."""
    factors = get_all_factors()
    print("Caprini VTE Risk Factors")
    print("=" * 56)
    current_pts = None
    for f in factors:
        if f["points"] != current_pts:
            current_pts = f["points"]
            print(f"\n--- {current_pts} point{'s' if current_pts != 1 else ''} ---")
        print(f"  {f['key']:42s}  {f['label']}")
    print()
    return 0


def cmd_batch(args: argparse.Namespace) -> int:
    """Handle the 'batch' subcommand — process a CSV file."""
    try:
        with open(args.input, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fieldnames = list(reader.fieldnames or [])
            rows = list(reader)
    except FileNotFoundError:
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        return 1

    out_fields = fieldnames + ["caprini_score", "risk_tier", "vte_rate",
                                "active_factors", "prophylaxis_summary"]
    out_rows = []
    for row in rows:
        # Convert CSV values to factors dict
        factors = {}
        # Try to find an age column
        for age_col in ("age", "Age", "AGE"):
            if age_col in row and row[age_col]:
                try:
                    factors["age"] = float(row[age_col])
                except ValueError:
                    pass
                break

        # Map other columns: check if column name matches a factor key
        for key, _, _ in RISK_FACTORS:
            if key in AGE_KEYS:
                continue
            val = row.get(key, row.get(key.replace("_", "-"), ""))
            if str(val).strip().lower() in ("1", "true", "yes", "y"):
                factors[key] = True

        result = calculate_score(factors)
        out_row = dict(row)
        out_row["caprini_score"] = result["score"]
        out_row["risk_tier"] = result["risk_tier"]
        out_row["vte_rate"] = f"{result['vte_rate']:.1%}"
        out_row["active_factors"] = "; ".join(
            f"{k}({v})" for k, v in result["active_factors"].items()
        )
        out_row["prophylaxis_summary"] = " | ".join(result["prophylaxis"])
        out_rows.append(out_row)

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Processed {len(out_rows)} records -> {args.output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="caprini",
        description="Caprini VTE Risk Score Calculator — clinical decision support tool",
    )
    sub = parser.add_subparsers(dest="command")

    # --- score ---
    p_score = sub.add_parser("score", help="Calculate Caprini score for a single patient")
    _add_factor_args(p_score)
    p_score.add_argument("--json", default=None,
                         help="Pass all factors as a JSON string (overrides flags)")
    p_score.add_argument("--patient-id", default=None, help="Optional patient identifier")
    p_score.add_argument("--json-output", action="store_true",
                         help="Also print raw JSON result")

    # --- factors ---
    sub.add_parser("factors", help="List all Caprini risk factors")

    # --- batch ---
    p_batch = sub.add_parser("batch", help="Batch-process a CSV file of patients")
    p_batch.add_argument("-i", "--input", required=True, help="Input CSV path")
    p_batch.add_argument("-o", "--output", default="results.csv", help="Output CSV path")

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "score":
        return cmd_score(args)
    elif args.command == "factors":
        return cmd_factors(args)
    elif args.command == "batch":
        return cmd_batch(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
