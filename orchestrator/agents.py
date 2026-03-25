import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ImplementerResult:
    changed_files: list[str]; change_summary: str; why_this_change: str; notes: list[str]

@dataclass
class EvalResult: score: float; details: dict

@dataclass
class TestResult: passed: bool; total: int; details: str

@dataclass
class ControllerResult:
    decision: str; decision_code: str; score_after: float; score_before: float; score_delta: float

def run_implementer(config, hypothesis):
    config.tmp_path.mkdir(parents=True, exist_ok=True)
    result = ImplementerResult(["src/search/normalize.py"], "placeholder: normalization", "improve matching", ["placeholder"])
    (config.tmp_path / "implementer_result.json").write_text(
        json.dumps({"changed_files": result.changed_files, "change_summary": result.change_summary,
                    "why_this_change": result.why_this_change, "notes": result.notes}, ensure_ascii=False, indent=2), encoding="utf-8")
    return result

def run_tests(config):
    try:
        r = subprocess.run(["pytest", str(config.tests_path), "-v"], capture_output=True, text=True, cwd=Path.cwd())
    except FileNotFoundError:
        r = subprocess.run(["python3", "-m", "pytest", str(config.tests_path), "-v"], capture_output=True, text=True, cwd=Path.cwd())
    passed = r.returncode == 0
    total = sum(1 for line in r.stdout.split("\n") if "PASSED" in line or "passed" in line)
    result = TestResult(passed, total, r.stdout)
    config.tmp_path.mkdir(parents=True, exist_ok=True)
    (config.tmp_path / "tests_result.json").write_text(json.dumps({"passed": passed, "total": total, "details": r.stdout}, ensure_ascii=False, indent=2), encoding="utf-8")
    return result

def run_eval(config):
    r = subprocess.run(["python3", str(config.frozen_eval_path)], capture_output=True, text=True, cwd=Path.cwd())
    if r.returncode != 0: raise RuntimeError(f"Eval failed: {r.stderr}")
    data = json.loads(r.stdout)
    config.tmp_path.mkdir(parents=True, exist_ok=True)
    (config.tmp_path / "eval_result.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return EvalResult(data["score"], data)

def run_controller(config, score_before, score_after, tests_passed):
    decision = "reject"; code = "NO_IMPROVEMENT"
    if score_after > score_before and tests_passed: decision, code = "accept", "ACCEPT"
    elif not tests_passed: code = "TEST_FAIL"
    elif score_after < score_before: code = "SCORE_REGRESSION"
    result = ControllerResult(decision, code, score_after, score_before, round(score_after - score_before, 6))
    config.tmp_path.mkdir(parents=True, exist_ok=True)
    (config.tmp_path / "controller_result.json").write_text(
        json.dumps({"decision": decision, "decision_code": code, "score_after": score_after,
                    "score_before": score_before, "score_delta": result.score_delta}, ensure_ascii=False, indent=2), encoding="utf-8")
    return result

def rollback_change(config):
    if not config.use_git: return
    subprocess.run(["git", "restore", "."], capture_output=True, text=True, cwd=Path.cwd())
    subprocess.run(["git", "clean", "-fd"], capture_output=True, text=True, cwd=Path.cwd())
    print("[rollback] Rolled back")
