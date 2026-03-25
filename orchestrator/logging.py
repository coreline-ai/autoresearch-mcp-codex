import json
from datetime import datetime, timezone
from pathlib import Path

def log_result(config, iteration, hypothesis_id, status, code, score_before, score_after, tests_pass, summary, reason):
    p = config.results_path
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text("\t".join(["iteration", "timestamp", "hypothesis_id", "status", "decision_code", "score_before", "score_after", "score_delta", "tests_pass", "constraints_ok", "critic_severity", "critic_recommendation", "changed_files_count", "change_summary", "rollback_reason"]) + "\n", encoding="utf-8")
    ts = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    with p.open("a", encoding="utf-8") as f:
        f.write("\t".join([str(iteration), ts, hypothesis_id, status, code, str(score_before), str(score_after),
                           str(round(score_after - score_before, 6)), str(tests_pass).lower(), "true", "low", status, "1",
                           summary.replace("\t", " "), reason.replace("\t", " ")]) + "\n")

def log_decision(config, i, d, code, sb, sa, tp, summary, reason):
    p = config.decisions_path
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists(): p.write_text("# DECISIONS\n\n", encoding="utf-8")
    with p.open("a", encoding="utf-8") as f:
        f.write(f"\n## Iteration {i}\n- decision: {d}\n- decision_code: {code}\n- score_before: {sb}\n- score_after: {sa}\n- tests_pass: {tp}\n- change_summary: {summary}\n- rollback_reason: {reason}\n")

def update_memory(config, code, summary, reason):
    p = config.memory_path
    p.parent.mkdir(parents=True, exist_ok=True)
    sections = {"Accepted Patterns": [], "Rejected Patterns": [], "Known Risks": [], "Strategy Notes": []}
    if p.exists():
        content = p.read_text(encoding="utf-8"); cur = None
        for line in content.split("\n"):
            if line.startswith("## "):
                s = line[3:].strip()
                if s in sections: cur = s
            elif cur and line.startswith("- "): sections[cur].append(line[2:].strip())
    if code == "ACCEPT": sections["Accepted Patterns"].append(f"- {summary}")
    elif code in ["SCORE_REGRESSION", "TEST_FAIL", "CONSTRAINT_FAIL"]:
        sections["Rejected Patterns"].append(f"- {summary}: {reason}")
    with p.open("w", encoding="utf-8") as f:
        f.write("# MEMORY\n\n## Accepted Patterns\n")
        for item in sections["Accepted Patterns"]: f.write(f"{item}\n")
        f.write("\n## Rejected Patterns\n")
        for item in sections["Rejected Patterns"]: f.write(f"{item}\n")
        f.write("\n## Known Risks\n")
        for item in sections["Known Risks"]: f.write(f"{item}\n")
        f.write("\n## Strategy Notes\n")
        for item in sections["Strategy Notes"]: f.write(f"{item}\n")
