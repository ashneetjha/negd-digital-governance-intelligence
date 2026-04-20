"""
Standalone Compare Pipeline — run month-to-month comparison from the CLI.

Usage:
  python compare_pipeline.py --state "Delhi" --month-a "2025-01" --month-b "2025-02"
"""
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.comparison_service import run_comparison, compare_cross_state
from app.utils.logger import get_logger

logger = get_logger("compare_pipeline")


def main():
    parser = argparse.ArgumentParser(description="NeGD Comparison Pipeline CLI")
    parser.add_argument("--state",   required=True, help="State name")
    parser.add_argument("--month-a", required=True, help="Earlier month (YYYY-MM)")
    parser.add_argument("--month-b", required=True, help="Later month (YYYY-MM)")
    parser.add_argument("--topic", help="Specific topic to compare (optional)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--state-b", help="Second state for cross-state comparison (optional)")
    parser.add_argument("--month-c", help="Month for state-b in cross-state comparison (defaults to month-a)")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"State:   {args.state}")
    print(f"Month A: {args.month_a}")
    print(f"Month B: {args.month_b}")
    if args.state_b:
        print(f"State B: {args.state_b}")
    if args.topic:
        print(f"Topic:   {args.topic}")
    print(f"{'='*60}\n")

    # Cross-state mode
    if args.state_b:
        month_b_for_state_b = args.month_c or args.month_a
        result = compare_cross_state(
            state_a=args.state,
            month_a=args.month_a,
            state_b=args.state_b,
            month_b=month_b_for_state_b,
            topic=args.topic,
        )
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return
        print("CROSS-STATE SUMMARY")
        print("-" * 60)
        print(result.get("summary", "—"))
        for key, label in [
            ("state_a_strengths", f"{args.state} STRENGTHS"),
            ("state_b_strengths", f"{args.state_b} STRENGTHS"),
            ("common_initiatives", "COMMON INITIATIVES"),
            ("recommendations", "RECOMMENDATIONS"),
        ]:
            items = result.get(key, [])
            if items:
                print(f"\n{label} ({len(items)})")
                print("-" * 60)
                for item in items:
                    print(f"  • {item}")
        return

    result = run_comparison(
        state=args.state,
        month_a=args.month_a,
        month_b=args.month_b,
        topic=args.topic,
    )

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    print("SUMMARY")
    print("-" * 60)
    print(result.get("summary", "—"))

    sections = [
        ("NEW INITIATIVES",        "new_initiatives"),
        ("REMOVED MENTIONS",       "removed_mentions"),
    ]
    for label, key in sections:
        items = result.get(key, [])
        print(f"\n{label} ({len(items)})")
        print("-" * 60)
        for item in items:
            print(f"  • {item}")

    quant = result.get("quantitative_changes", [])
    if quant:
        print(f"\nQUANTITATIVE CHANGES ({len(quant)})")
        print("-" * 60)
        for q in quant:
            print(f"  {q['metric']:<30}  {args.month_a}: {q['month_a']}  →  {args.month_b}: {q['month_b']}")

    comp = result.get("compliance_changes", [])
    if comp:
        print(f"\nCOMPLIANCE CHANGES ({len(comp)})")
        print("-" * 60)
        for c in comp:
            print(f"  {c['area']:<30}  {args.month_a}: {c['status_month_a']}  →  {args.month_b}: {c['status_month_b']}")

    citations = result.get("citations", [])
    if citations:
        print(f"\nCITATIONS ({len(citations)})")
        print("-" * 60)
        for i, c in enumerate(citations, 1):
            print(f"  {i}. {c['state']} | {c['month']} | {c.get('section', '—')}")


if __name__ == "__main__":
    main()
