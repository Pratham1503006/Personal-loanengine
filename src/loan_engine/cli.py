"""Command-line interface.

Examples
--------
Run the synthetic profiles and write results::

    python -m loan_engine.cli --profiles data/test_profiles.json \
        --output data/test_results.json --write-outputs

Assess a single inline profile::

    python -m loan_engine.cli --profile '{"applicant_age_years": 32, ...}'
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import data_loader as dl
from . import reporting
from . import validation as vd


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="loan_engine", description="India personal-loan eligibility engine")
    p.add_argument("--profiles", type=str, help="Path to a JSON file with synthetic profiles.")
    p.add_argument("--profile", type=str, help="A single inline JSON applicant profile.")
    p.add_argument("--output", type=str, help="Where to write the JSON results.")
    p.add_argument("--preference", type=str, default="balanced", help="Recommendation preference.")
    p.add_argument("--write-outputs", action="store_true", help="Regenerate all files in outputs/.")
    p.add_argument("--data-dir", type=str, default=None, help="Override the data directory.")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    data_dir = Path(args.data_dir) if args.data_dir else None

    lenders = dl.load_lenders(data_dir)
    rules = dl.load_rules(data_dir)
    sources = dl.load_sources(data_dir)

    profiles = []
    if args.profiles:
        profiles = dl.load_test_profiles(Path(args.profiles))
    if args.profile:
        parsed, result = vd.parse_and_validate(json.loads(args.profile))
        if parsed is None:
            print("Invalid profile:", "; ".join(result.errors), file=sys.stderr)
            return 2
        profiles.append(parsed)
    if not profiles:
        profiles = dl.load_test_profiles()

    results = [
        reporting.assess_profile(p, lenders, rules, sources, preference=args.preference)
        for p in profiles
    ]

    if args.output:
        out = Path(args.output)
        if len(results) == 1:
            reporting.save_result_json(results[0], out)
        else:
            out.parent.mkdir(parents=True, exist_ok=True)
            with open(out, "w", encoding="utf-8") as fh:
                json.dump(results, fh, indent=2, default=str)
        print(f"Wrote {len(results)} result(s) to {out}")

    if args.write_outputs:
        write_all_outputs(results, lenders, rules, sources)

    summary = {
        "profiles": len(results),
        "applicant_outcomes": {},
        "lender_decisions": {},
    }
    for r in results:
        summary["applicant_outcomes"][r["applicant_outcome"]] = (
            summary["applicant_outcomes"].get(r["applicant_outcome"], 0) + 1
        )
        for lo in r["lender_outcomes"]:
            summary["lender_decisions"][lo["decision"]] = (
                summary["lender_decisions"].get(lo["decision"], 0) + 1
            )
    print(json.dumps(summary, indent=2))
    return 0


def write_all_outputs(results, lenders, rules, sources) -> None:
    root = dl.REPO_ROOT / "outputs"
    root.mkdir(parents=True, exist_ok=True)

    sp = reporting.sample_predictions(results)
    sp.to_csv(root / "sample_predictions.csv", index=False)

    fa = reporting.rule_failure_analysis(results)
    fa.to_csv(root / "rule_failure_analysis.csv", index=False)

    cov = reporting.research_coverage(lenders, rules, sources)
    cov.to_csv(root / "research_coverage.csv", index=False)

    print(f"Wrote {root / 'sample_predictions.csv'}")
    print(f"Wrote {root / 'rule_failure_analysis.csv'}")
    print(f"Wrote {root / 'research_coverage.csv'}")


if __name__ == "__main__":
    raise SystemExit(main())
