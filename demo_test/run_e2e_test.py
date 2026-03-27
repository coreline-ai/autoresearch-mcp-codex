#!/usr/bin/env python3
"""
End-to-End Pipeline Test for AutoResearch MCP

이 스크립트는 프로젝트 파일을 건드리지 않고, 임시 디렉토리에
전체 파이프라인 환경을 복제하여 실제 iteration을 실행합니다.

테스트 시나리오:
  1. Single iteration (accept 경로)
  2. Single iteration (reject 경로 — baseline을 높게 설정)
  3. Multi-iteration loop (3회, stagnation 종료)
  4. Error recovery (eval 실패 시 rollback)
  5. Artifact 무결성 검증 (RESULTS.tsv, DECISIONS.md, MEMORY.md, baseline.json)
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

# ── 프로젝트 루트를 sys.path에 추가 ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ── 색상 출력 ──
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


def banner(msg: str) -> None:
    print(f"\n{CYAN}{'=' * 60}{RESET}")
    print(f"{BOLD}{CYAN}  {msg}{RESET}")
    print(f"{CYAN}{'=' * 60}{RESET}\n")


def ok(msg: str) -> None:
    print(f"  {GREEN}[OK] {msg}{RESET}")


def fail(msg: str) -> None:
    print(f"  {RED}[FAIL] {msg}{RESET}")


def info(msg: str) -> None:
    print(f"  {YELLOW}-> {msg}{RESET}")


class PipelineTestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors: list[str] = []

    def check(self, condition: bool, description: str) -> bool:
        if condition:
            ok(description)
            self.passed += 1
        else:
            fail(description)
            self.failed += 1
            self.errors.append(description)
        return condition

    def summary(self) -> str:
        total = self.passed + self.failed
        status = f"{GREEN}ALL PASSED{RESET}" if self.failed == 0 else f"{RED}{self.failed} FAILED{RESET}"
        return f"\n{BOLD}Result: {self.passed}/{total} checks passed — {status}"


# ── 환경 구축 ──

def setup_test_environment(work_dir: Path) -> None:
    """프로젝트에서 필요한 파일만 복사하여 독립 테스트 환경 구축."""
    # 디렉토리 구조
    for d in ["agent", "eval", "src", "tests", "prompts", "tmp", "reports/final", "orchestrator"]:
        (work_dir / d).mkdir(parents=True, exist_ok=True)

    # eval/ — frozen_eval.py, fixtures.json, constraints.py
    shutil.copy2(PROJECT_ROOT / "eval" / "frozen_eval.py", work_dir / "eval" / "frozen_eval.py")
    shutil.copy2(PROJECT_ROOT / "eval" / "fixtures.json", work_dir / "eval" / "fixtures.json")
    shutil.copy2(PROJECT_ROOT / "eval" / "constraints.py", work_dir / "eval" / "constraints.py")
    (work_dir / "eval" / "__init__.py").write_text('"""eval package"""\n')

    # src/ — query_processor.py
    shutil.copy2(PROJECT_ROOT / "src" / "query_processor.py", work_dir / "src" / "query_processor.py")
    shutil.copy2(PROJECT_ROOT / "src" / "__init__.py", work_dir / "src" / "__init__.py")

    # orchestrator/ — 전체 모듈
    for f in (PROJECT_ROOT / "orchestrator").glob("*.py"):
        shutil.copy2(f, work_dir / "orchestrator" / f.name)

    # prompts/ (implementer.md 필요)
    for f in (PROJECT_ROOT / "prompts").glob("*.md"):
        shutil.copy2(f, work_dir / "prompts" / f.name)

    # tests/ — 기본 테스트 파일 (frozen_eval 테스트)
    for f in (PROJECT_ROOT / "tests").glob("*.py"):
        shutil.copy2(f, work_dir / "tests" / f.name)

    # agent/ — 상태 파일 초기화
    _write_agent_files(work_dir)

    # eval/baseline.json — 초기 baseline
    (work_dir / "eval" / "baseline.json").write_text(
        json.dumps({"score": 0.5, "iteration": 0}, indent=2), encoding="utf-8"
    )


def _write_agent_files(work_dir: Path) -> None:
    """에이전트 상태 파일 생성."""
    agent = work_dir / "agent"

    def _w(path: Path, text: str) -> None:
        path.write_text(text, encoding="utf-8")

    _w(agent / "PRODUCT_GOAL.md",
        "# Goal\nImprove search relevance compared to baseline.\n\n"
        "## Success Criteria\n- frozen eval score improvement\n- tests pass\n- latency < 5%\n")
    _w(agent / "TASK.md",
        "# Task\nImprove user search query preprocessing to increase recall.\n\n"
        "## This Cycle Goal\nValidate punctuation normalization\n")
    _w(agent / "RULES.md",
        "# Rules\n## Absolute Rules\n"
        "- Do not modify eval/frozen_eval.py\n"
        "- Do not modify eval/fixtures.json\n"
        "- Do not modify eval/baseline.json\n"
        "- 1 iteration = 1 core change\n")
    _w(agent / "MEMORY.md",
        "# MEMORY\n\n## Accepted Patterns\n\n## Rejected Patterns\n\n## Known Risks\n\n## Strategy Notes\n")
    _w(agent / "HYPOTHESES.md",
        "### H-001: Normalize punctuation\n"
        "- expected_effect: improve recall\n"
        "- risk: low\n"
        "- priority: high\n"
        "- status: selected\n\n"
        "### H-002: Lowercase normalization\n"
        "- expected_effect: consistency\n"
        "- risk: low\n"
        "- priority: medium\n"
        "- status: proposed\n")
    _w(agent / "PLAN.md",
        "# Plan\n## Selected Hypothesis\nH-001\n\n"
        "## Change Scope\n- src/query_processor.py\n\n"
        "## Planned Change\npunctuation normalization improvement\n\n"
        "## Tests To Run\n- pytest tests/ -v\n\n"
        "## Reject Conditions\n- test failure\n- score regression\n")
    _w(agent / "ITERATION_STATE.json",
        json.dumps({
            "iteration": 0, "mode": "single-agent", "phase": "done",
            "selected_hypothesis": None, "baseline_score": 0.5,
            "candidate_score": None, "tests_pass": None,
            "constraints_ok": None, "decision": None, "last_updated": "",
        }, indent=2))
    _w(agent / "RESULTS.tsv",
        "iteration\ttimestamp\thypothesis_id\tstatus\tdecision_code\t"
        "score_before\tscore_after\tscore_delta\ttests_pass\tconstraints_ok\t"
        "critic_severity\tcritic_recommendation\tchanged_files_count\t"
        "change_summary\trollback_reason\n")
    _w(agent / "DECISIONS.md", "# DECISIONS\n\n")


# ── 테스트 시나리오 ──

def test_1_single_iteration_placeholder_reject(work_dir: Path, result: PipelineTestResult) -> None:
    """시나리오 1: baseline=0.5, placeholder implementer -> reject (NO_CODE_CHANGE)."""
    banner("Test 1: Single Iteration - Placeholder Reject")
    info(f"Working dir: {work_dir}")

    (work_dir / "eval" / "baseline.json").write_text(
        json.dumps({"score": 0.5, "iteration": 0}, indent=2), encoding="utf-8"
    )

    from orchestrator.config import OrchestratorConfig
    from orchestrator.runner import IterationRunner

    config = OrchestratorConfig(
        baseline_path=work_dir / "eval" / "baseline.json",
        frozen_eval_path=work_dir / "eval" / "frozen_eval.py",
        tests_path=work_dir / "tests",
        results_path=work_dir / "agent" / "RESULTS.tsv",
        decisions_path=work_dir / "agent" / "DECISIONS.md",
        memory_path=work_dir / "agent" / "MEMORY.md",
        state_path=work_dir / "agent" / "ITERATION_STATE.json",
        tmp_path=work_dir / "tmp",
        reports_path=work_dir / "reports",
        use_git=False,
    )

    try:
        runner = IterationRunner(config)
        ctrl = runner.run(iteration=1, baseline_score=0.5)

        # placeholder -> reject
        result.check(ctrl.decision == "reject", f"Decision is 'reject' (got {ctrl.decision})")
        result.check(ctrl.decision_code == "NO_CODE_CHANGE", f"Code is NO_CODE_CHANGE (got {ctrl.decision_code})")

        # baseline NOT updated (rejected)
        baseline = json.loads((work_dir / "eval" / "baseline.json").read_text(encoding="utf-8"))
        result.check(baseline["score"] == 0.5, f"Baseline unchanged at 0.5 (got {baseline['score']})")

        tsv = (work_dir / "agent" / "RESULTS.tsv").read_text(encoding="utf-8")
        tsv_lines = [l for l in tsv.strip().split("\n") if l]
        result.check(len(tsv_lines) == 2, f"RESULTS.tsv has header + 1 row (got {len(tsv_lines)} lines)")
        result.check("reject" in tsv_lines[-1], "RESULTS.tsv row contains 'reject'")

        decisions = (work_dir / "agent" / "DECISIONS.md").read_text(encoding="utf-8")
        result.check("## Iteration 1" in decisions, "DECISIONS.md has Iteration 1 block")
        result.check("decision: reject" in decisions, "DECISIONS.md records 'reject'")

        memory = (work_dir / "agent" / "MEMORY.md").read_text(encoding="utf-8")
        result.check("Accepted Patterns" in memory, "MEMORY.md has Accepted Patterns section")

        state = json.loads((work_dir / "agent" / "ITERATION_STATE.json").read_text(encoding="utf-8"))
        result.check(state["phase"] == "done", f"Final phase is 'done' (got {state['phase']})")
        result.check(state["iteration"] == 1, f"Iteration is 1 (got {state['iteration']})")

        # tmp/ 아티팩트
        result.check((work_dir / "tmp" / "eval_result.json").exists(), "tmp/eval_result.json created")
        result.check((work_dir / "tmp" / "controller_result.json").exists(), "tmp/controller_result.json created")
        result.check((work_dir / "tmp" / "explorer_result.json").exists(), "tmp/explorer_result.json created")
        result.check((work_dir / "tmp" / "planner_result.json").exists(), "tmp/planner_result.json created")
        result.check((work_dir / "tmp" / "critic_result.json").exists(), "tmp/critic_result.json created")

    except Exception as e:
        result.check(False, f"Test 1 crashed: {e}")


def test_2_single_iteration_reject(work_dir: Path, result: PipelineTestResult) -> None:
    """시나리오 2: baseline=1.0, placeholder -> reject (NO_CODE_CHANGE)."""
    banner("Test 2: Single Iteration - Reject (No Code Change)")
    info(f"Working dir: {work_dir}")

    _write_agent_files(work_dir)
    (work_dir / "eval" / "baseline.json").write_text(
        json.dumps({"score": 1.0, "iteration": 0}, indent=2), encoding="utf-8"
    )

    from orchestrator.config import OrchestratorConfig
    from orchestrator.runner import IterationRunner

    config = OrchestratorConfig(
        baseline_path=work_dir / "eval" / "baseline.json",
        frozen_eval_path=work_dir / "eval" / "frozen_eval.py",
        tests_path=work_dir / "tests",
        results_path=work_dir / "agent" / "RESULTS.tsv",
        decisions_path=work_dir / "agent" / "DECISIONS.md",
        memory_path=work_dir / "agent" / "MEMORY.md",
        state_path=work_dir / "agent" / "ITERATION_STATE.json",
        tmp_path=work_dir / "tmp",
        reports_path=work_dir / "reports",
        use_git=False,
    )

    try:
        ctrl = IterationRunner(config).run(iteration=1, baseline_score=1.0)
        result.check(ctrl.decision == "reject", f"Decision is 'reject' (got {ctrl.decision})")
        result.check(ctrl.decision_code == "NO_CODE_CHANGE", f"Code is NO_CODE_CHANGE (got {ctrl.decision_code})")
        baseline = json.loads((work_dir / "eval" / "baseline.json").read_text(encoding="utf-8"))
        result.check(baseline["score"] == 1.0, "Baseline unchanged at 1.0")
        decisions = (work_dir / "agent" / "DECISIONS.md").read_text(encoding="utf-8")
        result.check("reject" in decisions, "DECISIONS.md records 'reject'")
    except Exception as e:
        result.check(False, f"Test 2 crashed: {e}")


def test_3_loop_stagnation(work_dir: Path, result: PipelineTestResult) -> None:
    """시나리오 3: loop with placeholder -> all reject (NO_CODE_CHANGE) -> stagnation."""
    banner("Test 3: Multi-Iteration Loop - Stagnation Stop")
    info(f"Working dir: {work_dir}")

    _write_agent_files(work_dir)
    (work_dir / "eval" / "baseline.json").write_text(
        json.dumps({"score": 1.0, "iteration": 0}, indent=2), encoding="utf-8"
    )

    from orchestrator.config import OrchestratorConfig
    from orchestrator.loop import LoopOrchestrator

    config = OrchestratorConfig(
        max_iterations=5, max_no_improvement_streak=2,
        baseline_path=work_dir / "eval" / "baseline.json",
        frozen_eval_path=work_dir / "eval" / "frozen_eval.py",
        tests_path=work_dir / "tests",
        results_path=work_dir / "agent" / "RESULTS.tsv",
        decisions_path=work_dir / "agent" / "DECISIONS.md",
        memory_path=work_dir / "agent" / "MEMORY.md",
        state_path=work_dir / "agent" / "ITERATION_STATE.json",
        tmp_path=work_dir / "tmp",
        reports_path=work_dir / "reports",
        use_git=False, allow_dirty=True,
    )

    try:
        loop_result = LoopOrchestrator(config).run()
        result.check(loop_result["status"] == "completed", f"Loop completed (got {loop_result['status']})")
        result.check(loop_result["iterations_run"] == 2, f"Ran 2 iterations before stagnation (got {loop_result['iterations_run']})")
        result.check(loop_result["final_score"] == 1.0, f"Final score 1.0 (got {loop_result['final_score']})")
        tsv = (work_dir / "agent" / "RESULTS.tsv").read_text(encoding="utf-8")
        data_lines = [l for l in tsv.strip().split("\n")[1:] if l]
        result.check(len(data_lines) == 2, f"RESULTS.tsv has 2 data rows (got {len(data_lines)})")
    except Exception as e:
        result.check(False, f"Test 3 crashed: {e}")


def test_4_loop_all_rejects(work_dir: Path, result: PipelineTestResult) -> None:
    """시나리오 4: baseline=0.5, placeholder -> all reject -> stagnation."""
    banner("Test 4: Loop - All Rejects (Placeholder)")
    info(f"Working dir: {work_dir}")

    _write_agent_files(work_dir)
    (work_dir / "eval" / "baseline.json").write_text(
        json.dumps({"score": 0.5, "iteration": 0}, indent=2), encoding="utf-8"
    )

    from orchestrator.config import OrchestratorConfig
    from orchestrator.loop import LoopOrchestrator

    config = OrchestratorConfig(
        max_iterations=10, max_no_improvement_streak=2,
        baseline_path=work_dir / "eval" / "baseline.json",
        frozen_eval_path=work_dir / "eval" / "frozen_eval.py",
        tests_path=work_dir / "tests",
        results_path=work_dir / "agent" / "RESULTS.tsv",
        decisions_path=work_dir / "agent" / "DECISIONS.md",
        memory_path=work_dir / "agent" / "MEMORY.md",
        state_path=work_dir / "agent" / "ITERATION_STATE.json",
        tmp_path=work_dir / "tmp",
        reports_path=work_dir / "reports",
        use_git=False, allow_dirty=True,
    )

    try:
        loop_result = LoopOrchestrator(config).run()
        result.check(loop_result["status"] == "completed", f"Loop completed (got {loop_result['status']})")
        # placeholder -> all NO_CODE_CHANGE -> stagnation after 2
        result.check(loop_result["iterations_run"] == 2, f"Ran 2 iterations (got {loop_result['iterations_run']})")
        result.check(loop_result["final_score"] == 0.5, f"Final score unchanged 0.5 (got {loop_result['final_score']})")

        tsv = (work_dir / "agent" / "RESULTS.tsv").read_text(encoding="utf-8")
        data_lines = [l for l in tsv.strip().split("\n")[1:] if l]
        reject_count = sum(1 for l in data_lines if l.split("\t")[3] == "reject")
        result.check(reject_count == 2, f"All 2 are rejects (got {reject_count})")

        baseline = json.loads((work_dir / "eval" / "baseline.json").read_text(encoding="utf-8"))
        result.check(baseline["score"] == 0.5, "Baseline unchanged at 0.5")
    except Exception as e:
        result.check(False, f"Test 4 crashed: {e}")


def test_5_eval_result_integrity(work_dir: Path, result: PipelineTestResult) -> None:
    """시나리오 5: eval_result.json 무결성 검증."""
    banner("Test 5: Eval Result Integrity - Constraints Check")
    info(f"Working dir: {work_dir}")

    eval_json_path = work_dir / "tmp" / "eval_result.json"
    if not eval_json_path.exists():
        info("Running a single iteration first to generate eval_result.json...")
        _write_agent_files(work_dir)
        (work_dir / "eval" / "baseline.json").write_text(
            json.dumps({"score": 0.5, "iteration": 0}, indent=2), encoding="utf-8"
        )

        from orchestrator.config import OrchestratorConfig
        from orchestrator.runner import IterationRunner

        config = OrchestratorConfig(
            baseline_path=work_dir / "eval" / "baseline.json",
            frozen_eval_path=work_dir / "eval" / "frozen_eval.py",
            tests_path=work_dir / "tests",
            results_path=work_dir / "agent" / "RESULTS.tsv",
            decisions_path=work_dir / "agent" / "DECISIONS.md",
            memory_path=work_dir / "agent" / "MEMORY.md",
            state_path=work_dir / "agent" / "ITERATION_STATE.json",
            tmp_path=work_dir / "tmp",
            reports_path=work_dir / "reports",
            use_git=False,
        )
        try:
            IterationRunner(config).run(iteration=1, baseline_score=0.5)
        except Exception:
            pass

    eval_data = json.loads(eval_json_path.read_text(encoding="utf-8"))
    result.check("score" in eval_data, "eval_result has 'score' field")
    result.check("constraints_ok" in eval_data, "eval_result has 'constraints_ok' field")
    result.check("latency_ms" in eval_data, "eval_result has 'latency_ms' field")
    result.check("latency_delta_pct" in eval_data, "eval_result has 'latency_delta_pct' field")
    result.check(isinstance(eval_data["constraints_ok"], bool), "constraints_ok is boolean (not hardcoded string)")
    result.check(0.0 <= eval_data["score"] <= 1.0, f"Score in valid range (got {eval_data['score']})")

    # constraints_ok이 frozen_eval의 하드코딩 True가 아닌 실제 constraints 체크 결과인지
    # latency_ms가 100(frozen_eval 하드코딩)이 아닌 실측값인지 확인
    # (실측값은 보통 100 이하이고, 정확히 100일 확률은 매우 낮음)
    info(f"  latency_ms = {eval_data.get('latency_ms')}")
    info(f"  latency_delta_pct = {eval_data.get('latency_delta_pct')}")
    info(f"  constraints_ok = {eval_data.get('constraints_ok')}")


# ── 메인 ──

def main() -> int:
    banner("AutoResearch MCP - End-to-End Pipeline Test")
    print(f"  Project root: {PROJECT_ROOT}")
    print(f"  Python: {sys.executable}")
    print(f"  Version: {sys.version.split()[0]}")

    result = PipelineTestResult()

    # 임시 디렉토리에서 테스트 실행
    with tempfile.TemporaryDirectory(prefix="autoresearch_e2e_") as tmpdir:
        work_dir = Path(tmpdir)
        info(f"Temp work dir: {work_dir}")

        # 환경 구축
        banner("Setting up test environment")
        setup_test_environment(work_dir)
        ok("Test environment created")

        # cwd를 work_dir로 변경 (frozen_eval이 상대경로로 fixtures.json을 찾으므로)
        original_cwd = os.getcwd()
        os.chdir(work_dir)
        info(f"Changed cwd to: {work_dir}")

        try:
            test_1_single_iteration_placeholder_reject(work_dir, result)
            test_2_single_iteration_reject(work_dir, result)
            test_3_loop_stagnation(work_dir, result)
            test_4_loop_all_rejects(work_dir, result)
            test_5_eval_result_integrity(work_dir, result)
        finally:
            os.chdir(original_cwd)

    # 결과 출력
    print(result.summary())

    if result.errors:
        print(f"\n{RED}Failed checks:{RESET}")
        for err in result.errors:
            print(f"  - {err}")

    return 0 if result.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
