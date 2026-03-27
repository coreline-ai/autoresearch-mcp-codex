#!/usr/bin/env python3
"""
Generate final report after all iterations complete
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def load_results() -> list[dict]:
    """Load all results from RESULTS.tsv"""
    results_path = Path("agent/RESULTS.tsv")
    if not results_path.exists():
        return []

    results = []
    lines = results_path.read_text(encoding="utf-8").strip().split("\n")
    headers = lines[0].split("\t")

    for line in lines[1:]:
        values = line.split("\t")
        result = dict(zip(headers, values))
        results.append(result)

    return results


def generate_final_report(results: list[dict]) -> str:
    """Generate final report markdown"""
    if not results:
        return "# Final Report\n\nNo iterations completed."

    accepted = [r for r in results if r["status"] == "accept"]
    rejected = [r for r in results if r["status"] == "reject"]

    best_score = 0.0
    for r in results:
        try:
            score = float(r["score_after"])
            best_score = max(best_score, score)
        except ValueError:
            pass

    report = f"""# Final Report

**Generated:** {datetime.now(timezone.utc).isoformat()}

## Summary
- Total Iterations: {len(results)}
- Accepted Changes: {len(accepted)}
- Rejected Changes: {len(rejected)}
- Best Score: {best_score}

## Accepted Changes

"""
    for r in accepted:
        report += f"### Iteration {r['iteration']}\n"
        report += f"- Score: {r['score_before']} → {r['score_after']} (+{r['score_delta']})\n"
        report += f"- Change: {r['change_summary']}\n\n"

    report += "## Rejected Changes\n\n"
    for r in rejected:
        report += f"### Iteration {r['iteration']}\n"
        report += f"- Decision: {r['decision_code']}\n"
        report += f"- Change: {r['change_summary']}\n"
        report += f"- Reason: {r['rollback_reason']}\n\n"

    report += "## Recommendations\n\n"
    report += "- Continue with small preprocessing improvements\n"
    report += "- Monitor precision alongside recall\n"
    report += "- Consider more complex hypotheses after exhausting simple options\n"

    return report


def main() -> int:
    """Main entry point"""
    results = load_results()
    report = generate_final_report(results)

    final_path = Path("reports/final/final_report.md")
    final_path.parent.mkdir(parents=True, exist_ok=True)
    final_path.write_text(report, encoding="utf-8")

    print(f"Final report generated: {final_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
