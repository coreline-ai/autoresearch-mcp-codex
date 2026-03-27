"""
Tests for orchestrator modules: state, agents, logging, runner.
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


# ---------------------------------------------------------------------------
# state.py tests
# ---------------------------------------------------------------------------

class TestPhaseEnum:
    def test_phase_has_16_states(self):
        from orchestrator.state import Phase
        assert len(Phase) == 16

    def test_phase_values_are_strings(self):
        from orchestrator.state import Phase
        for p in Phase:
            assert isinstance(p.value, str)

    def test_key_phases_exist(self):
        from orchestrator.state import Phase
        expected = [
            "init", "read_context", "explore", "plan", "implement",
            "run_tests", "run_eval", "critique", "decide", "accept",
            "reject", "rollback", "archive", "finalize", "error", "done",
        ]
        for val in expected:
            assert Phase(val).value == val


class TestDecisionCode:
    def test_decision_code_has_11_codes(self):
        from orchestrator.state import DecisionCode
        assert len(DecisionCode) == 11

    def test_accept_code(self):
        from orchestrator.state import DecisionCode
        assert DecisionCode.ACCEPT.value == "ACCEPT"

    def test_all_codes_uppercase(self):
        from orchestrator.state import DecisionCode
        for dc in DecisionCode:
            assert dc.value == dc.value.upper()


class TestIterationState:
    def test_to_dict_roundtrip(self):
        from orchestrator.state import IterationState, Phase
        state = IterationState(
            iteration=1,
            mode="single-agent",
            phase=Phase.IMPLEMENT,
            selected_hypothesis="H-001",
            baseline_score=0.5,
            last_updated="2026-01-01T00:00:00Z",
        )
        d = state.to_dict()
        restored = IterationState.from_dict(d)
        assert restored.iteration == 1
        assert restored.phase == Phase.IMPLEMENT
        assert restored.baseline_score == 0.5

    def test_from_dict_unknown_phase_kept_as_string(self):
        from orchestrator.state import IterationState
        d = {
            "iteration": 1, "mode": "single-agent", "phase": "unknown_phase",
            "selected_hypothesis": None, "baseline_score": 0.0, "last_updated": "",
        }
        state = IterationState.from_dict(d)
        assert state.phase == "unknown_phase"

    def test_new_fields_default_none(self):
        from orchestrator.state import IterationState, Phase
        state = IterationState(iteration=1, mode="test", phase=Phase.INIT)
        assert state.candidate_score is None
        assert state.tests_pass is None
        assert state.constraints_ok is None
        assert state.decision is None


# ---------------------------------------------------------------------------
# agents.py data model tests
# ---------------------------------------------------------------------------

class TestDataModels:
    def test_implementer_result_defaults(self):
        from orchestrator.agents import ImplementerResult
        r = ImplementerResult(
            changed_files=["a.py"],
            change_summary="test",
            why_this_change="reason",
        )
        assert r.scope_respected is True
        assert r.forbidden_paths_touched == []
        assert r.estimated_risk == "low"
        assert r.verification_commands_run == []

    def test_eval_result_defaults(self):
        from orchestrator.agents import EvalResult
        r = EvalResult(score=0.75)
        assert r.tests_pass is True
        assert r.constraints_ok is True
        assert r.regressions == []

    def test_tests_result_defaults(self):
        from orchestrator.agents import TestsResult
        r = TestsResult(passed=True)
        assert r.summary == ""
        assert r.failed_tests == []
        assert r.duration_sec == 0.0

    def test_critic_result_defaults(self):
        from orchestrator.agents import CriticResult
        r = CriticResult()
        assert r.severity == "low"
        assert r.recommendation == "accept"
        assert r.objections == []

    def test_controller_result_fields(self):
        from orchestrator.agents import ControllerResult
        r = ControllerResult(
            decision="accept", decision_code="ACCEPT",
            score_after=0.8, score_before=0.5, score_delta=0.3,
        )
        assert r.reason == ""
        assert r.critic_severity == "low"


# ---------------------------------------------------------------------------
# Decision engine tests (9-level priority chain)
# ---------------------------------------------------------------------------

class TestDecisionEngine:
    """Test run_controller with various input combinations."""

    def _make_config(self, tmp_path):
        from orchestrator.config import OrchestratorConfig
        return OrchestratorConfig(tmp_path=tmp_path)

    def _make_eval(self, score=0.8, constraints_ok=True, regressions=None):
        from orchestrator.agents import EvalResult
        return EvalResult(
            score=score,
            constraints_ok=constraints_ok,
            regressions=regressions or [],
        )

    def _make_tests(self, passed=True, failed=None):
        from orchestrator.agents import TestsResult
        return TestsResult(passed=passed, failed_tests=failed or [])

    def _make_impl(self, scope_ok=True, forbidden=None):
        from orchestrator.agents import ImplementerResult
        return ImplementerResult(
            changed_files=["a.py"],
            change_summary="test change",
            why_this_change="test",
            scope_respected=scope_ok,
            forbidden_paths_touched=forbidden or [],
        )

    def _make_critic(self, severity="low", recommendation="accept"):
        from orchestrator.agents import CriticResult
        return CriticResult(severity=severity, recommendation=recommendation)

    def test_level0_no_code_change_rejects(self, tmp_path):
        """Empty changed_files or placeholder → reject."""
        from orchestrator.agents import run_controller, ImplementerResult
        config = self._make_config(tmp_path)
        empty_impl = ImplementerResult([], "SKIPPED", "n/a", is_placeholder=True)
        ctrl = run_controller(
            config, score_before=0.5,
            eval_result=self._make_eval(0.8),
            test_result=self._make_tests(),
            impl_result=empty_impl,
        )
        assert ctrl.decision == "reject"
        assert ctrl.decision_code == "NO_CODE_CHANGE"

    def test_level1_test_fail_rejects(self, tmp_path):
        from orchestrator.agents import run_controller
        config = self._make_config(tmp_path)
        ctrl = run_controller(
            config, score_before=0.5,
            eval_result=self._make_eval(0.8),
            test_result=self._make_tests(passed=False, failed=["test_a"]),
            impl_result=self._make_impl(),
        )
        assert ctrl.decision == "reject"
        assert ctrl.decision_code == "TEST_FAIL"

    def test_level2_constraint_fail_rejects(self, tmp_path):
        from orchestrator.agents import run_controller
        config = self._make_config(tmp_path)
        ctrl = run_controller(
            config, score_before=0.5,
            eval_result=self._make_eval(0.8, constraints_ok=False),
            test_result=self._make_tests(),
            impl_result=self._make_impl(),
        )
        assert ctrl.decision == "reject"
        assert ctrl.decision_code == "CONSTRAINT_FAIL"

    def test_level3_forbidden_file_rejects(self, tmp_path):
        from orchestrator.agents import run_controller
        config = self._make_config(tmp_path)
        ctrl = run_controller(
            config, score_before=0.5,
            eval_result=self._make_eval(0.8),
            test_result=self._make_tests(),
            impl_result=self._make_impl(forbidden=["eval/frozen_eval.py"]),
        )
        assert ctrl.decision == "reject"
        assert ctrl.decision_code == "FORBIDDEN_FILE"

    def test_level4_scope_violation_rejects(self, tmp_path):
        from orchestrator.agents import run_controller
        config = self._make_config(tmp_path)
        ctrl = run_controller(
            config, score_before=0.5,
            eval_result=self._make_eval(0.8),
            test_result=self._make_tests(),
            impl_result=self._make_impl(scope_ok=False),
        )
        assert ctrl.decision == "reject"
        assert ctrl.decision_code == "SCOPE_VIOLATION"

    def test_level5_critic_high_rejects(self, tmp_path):
        from orchestrator.agents import run_controller
        config = self._make_config(tmp_path)
        ctrl = run_controller(
            config, score_before=0.5,
            eval_result=self._make_eval(0.8),
            test_result=self._make_tests(),
            impl_result=self._make_impl(),
            critic_result=self._make_critic(severity="high", recommendation="reject"),
        )
        assert ctrl.decision == "reject"
        assert ctrl.decision_code == "CRITIC_BLOCK"

    def test_level5_critic_high_hold(self, tmp_path):
        from orchestrator.agents import run_controller
        config = self._make_config(tmp_path)
        ctrl = run_controller(
            config, score_before=0.5,
            eval_result=self._make_eval(0.8),
            test_result=self._make_tests(),
            impl_result=self._make_impl(),
            critic_result=self._make_critic(severity="high", recommendation="hold"),
        )
        assert ctrl.decision == "hold"
        assert ctrl.decision_code == "CRITIC_BLOCK"

    def test_level6_score_regression_rejects(self, tmp_path):
        from orchestrator.agents import run_controller
        config = self._make_config(tmp_path)
        ctrl = run_controller(
            config, score_before=0.8,
            eval_result=self._make_eval(0.5),
            test_result=self._make_tests(),
            impl_result=self._make_impl(),
        )
        assert ctrl.decision == "reject"
        assert ctrl.decision_code == "SCORE_REGRESSION"

    def test_level7_no_improvement_rejects(self, tmp_path):
        from orchestrator.agents import run_controller
        config = self._make_config(tmp_path)
        ctrl = run_controller(
            config, score_before=0.5,
            eval_result=self._make_eval(0.5),
            test_result=self._make_tests(),
            impl_result=self._make_impl(),
        )
        assert ctrl.decision == "reject"
        assert ctrl.decision_code == "NO_IMPROVEMENT"

    def test_level8_accept(self, tmp_path):
        from orchestrator.agents import run_controller
        config = self._make_config(tmp_path)
        ctrl = run_controller(
            config, score_before=0.5,
            eval_result=self._make_eval(0.8),
            test_result=self._make_tests(),
            impl_result=self._make_impl(),
        )
        assert ctrl.decision == "accept"
        assert ctrl.decision_code == "ACCEPT"
        assert ctrl.score_delta == pytest.approx(0.3)

    def test_priority_test_fail_beats_score_improvement(self, tmp_path):
        """Even if score improved, test failure should reject."""
        from orchestrator.agents import run_controller
        config = self._make_config(tmp_path)
        ctrl = run_controller(
            config, score_before=0.5,
            eval_result=self._make_eval(0.9),
            test_result=self._make_tests(passed=False),
            impl_result=self._make_impl(),
        )
        assert ctrl.decision == "reject"
        assert ctrl.decision_code == "TEST_FAIL"


# ---------------------------------------------------------------------------
# Critic tests
# ---------------------------------------------------------------------------

class TestCritic:
    def _make_config(self, tmp_path):
        from orchestrator.config import OrchestratorConfig
        return OrchestratorConfig(tmp_path=tmp_path)

    def test_clean_change_low_severity(self, tmp_path):
        from orchestrator.agents import (
            run_critic, ImplementerResult, TestsResult, EvalResult,
        )
        config = self._make_config(tmp_path)
        result = run_critic(
            config,
            plan=None,
            impl_result=ImplementerResult(["a.py"], "good change", "reason"),
            test_result=TestsResult(passed=True),
            eval_result=EvalResult(score=0.8),
            baseline_score=0.5,
        )
        assert result.severity == "low"
        assert result.recommendation == "accept"

    def test_forbidden_path_high_severity(self, tmp_path):
        from orchestrator.agents import (
            run_critic, ImplementerResult, TestsResult, EvalResult,
        )
        config = self._make_config(tmp_path)
        result = run_critic(
            config,
            plan=None,
            impl_result=ImplementerResult(
                ["a.py"], "bad change", "reason",
                forbidden_paths_touched=["eval/frozen_eval.py"],
            ),
            test_result=TestsResult(passed=True),
            eval_result=EvalResult(score=0.8),
            baseline_score=0.5,
        )
        assert result.severity == "high"
        assert result.recommendation == "reject"

    def test_narrow_win_medium_severity(self, tmp_path):
        from orchestrator.agents import (
            run_critic, ImplementerResult, TestsResult, EvalResult,
        )
        config = self._make_config(tmp_path)
        result = run_critic(
            config,
            plan=None,
            impl_result=ImplementerResult(["a.py"], "small change", "reason"),
            test_result=TestsResult(passed=True),
            eval_result=EvalResult(score=0.55),
            baseline_score=0.5,
        )
        assert result.severity == "medium"
        assert "narrow win" in result.objections[0].lower() or "small" in result.objections[0].lower()


# ---------------------------------------------------------------------------
# Explorer tests
# ---------------------------------------------------------------------------

class TestExplorer:
    def _make_config(self, tmp_path):
        from orchestrator.config import OrchestratorConfig
        return OrchestratorConfig(tmp_path=tmp_path)

    def test_parse_hypotheses_md(self, tmp_path):
        from orchestrator.agents import run_explorer
        config = self._make_config(tmp_path)
        context = {
            "hypotheses": (
                "# HYPOTHESES\n\n"
                "### H-001: Normalize punctuation\n"
                "- expected_effect: improve recall\n"
                "- risk: low\n"
                "- priority: high\n"
                "- status: selected\n\n"
                "### H-002: Lowercase all\n"
                "- expected_effect: consistency\n"
                "- risk: low\n"
                "- priority: medium\n"
                "- status: proposed\n"
            ),
            "product_goal": "", "task": "", "memory": "", "results": "",
        }
        result = run_explorer(config, context)
        assert len(result.hypotheses) == 2
        assert result.hypotheses[0]["id"] == "H-001"
        assert result.hypotheses[1]["id"] == "H-002"

    def test_select_hypothesis_prefers_selected(self, tmp_path):
        from orchestrator.agents import run_explorer, select_hypothesis
        config = self._make_config(tmp_path)
        context = {
            "hypotheses": (
                "### H-001: A\n- status: proposed\n- priority: low\n\n"
                "### H-002: B\n- status: selected\n- priority: medium\n"
            ),
            "product_goal": "", "task": "", "memory": "", "results": "",
        }
        explorer = run_explorer(config, context)
        selected = select_hypothesis(explorer)
        assert selected == "H-002"

    def test_select_skips_rejected(self, tmp_path):
        from orchestrator.agents import run_explorer, select_hypothesis
        config = self._make_config(tmp_path)
        context = {
            "hypotheses": (
                "- H-001\n  - status: rejected\n  - priority: high\n\n"
                "- H-002\n  - status: proposed\n  - priority: medium\n"
            ),
            "product_goal": "", "task": "", "memory": "", "results": "",
        }
        explorer = run_explorer(config, context)
        selected = select_hypothesis(explorer)
        assert selected == "H-002"

    def test_select_skips_accepted(self, tmp_path):
        from orchestrator.agents import run_explorer, select_hypothesis
        config = self._make_config(tmp_path)
        context = {
            "hypotheses": (
                "- H-001\n  - status: accepted\n  - priority: high\n\n"
                "- H-002\n  - status: rejected\n  - priority: high\n\n"
                "- H-003\n  - status: proposed\n  - priority: low\n"
            ),
            "product_goal": "", "task": "", "memory": "", "results": "",
        }
        explorer = run_explorer(config, context)
        selected = select_hypothesis(explorer)
        assert selected == "H-003"

    def test_select_returns_none_when_all_exhausted(self, tmp_path):
        from orchestrator.agents import run_explorer, select_hypothesis
        config = self._make_config(tmp_path)
        context = {
            "hypotheses": (
                "- H-001\n  - status: accepted\n\n"
                "- H-002\n  - status: rejected\n"
            ),
            "product_goal": "", "task": "", "memory": "", "results": "",
        }
        explorer = run_explorer(config, context)
        selected = select_hypothesis(explorer)
        assert selected is None

    def test_update_hypothesis_status(self, tmp_path):
        from orchestrator.agents import update_hypothesis_status
        from orchestrator.config import OrchestratorConfig

        hyp_path = tmp_path / "agent" / "HYPOTHESES.md"
        hyp_path.parent.mkdir(parents=True, exist_ok=True)
        hyp_path.write_text(
            "# HYPOTHESES\n\n"
            "- H-001\n  - title: test\n  - status: selected\n\n"
            "- H-002\n  - title: test2\n  - status: proposed\n",
            encoding="utf-8",
        )

        import os
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            config = OrchestratorConfig()
            update_hypothesis_status(config, "H-001", "rejected")
            content = hyp_path.read_text(encoding="utf-8")
            assert "status: rejected" in content
            # H-002 should be unchanged
            lines = content.split("\n")
            h002_lines = content.split("H-002")[1]
            assert "status: proposed" in h002_lines
        finally:
            os.chdir(original_cwd)

    def test_parse_format_a_hypotheses(self, tmp_path):
        """Test parsing the actual HYPOTHESES.md format (dash-based)."""
        from orchestrator.agents import run_explorer
        config = self._make_config(tmp_path)
        context = {
            "hypotheses": (
                "# HYPOTHESES\n\n"
                "- H-001\n"
                "  - title: normalize punctuation\n"
                "  - expected_effect: recall improvement\n"
                "  - risk: low\n"
                "  - priority: high\n"
                "  - status: selected\n\n"
                "- H-002\n"
                "  - title: lowercase normalization\n"
                "  - priority: high\n"
                "  - status: proposed\n\n"
                "- H-003\n"
                "  - title: synonym expansion\n"
                "  - priority: medium\n"
                "  - status: parked\n"
            ),
            "product_goal": "", "task": "", "memory": "", "results": "",
        }
        result = run_explorer(config, context)
        assert len(result.hypotheses) == 3
        assert result.hypotheses[0]["id"] == "H-001"
        assert result.hypotheses[0]["title"] == "normalize punctuation"
        assert result.hypotheses[0]["status"] == "selected"
        assert result.hypotheses[2]["status"] == "parked"


# ---------------------------------------------------------------------------
# Constraints tests
# ---------------------------------------------------------------------------

class TestConstraints:
    def test_all_pass(self):
        from eval.constraints import check_constraints
        result = check_constraints(
            eval_output={"score": 0.8, "latency_ms": 100, "regressions": []},
            baseline_latency_ms=100,
        )
        assert result["constraints_ok"] is True
        assert result["violations"] == []

    def test_latency_budget_exceeded(self):
        from eval.constraints import check_constraints
        result = check_constraints(
            eval_output={"score": 0.8, "latency_ms": 200, "regressions": []},
            baseline_latency_ms=100,
        )
        assert result["constraints_ok"] is False
        assert any("Latency budget" in v for v in result["violations"])

    def test_regressions_fail(self):
        from eval.constraints import check_constraints
        result = check_constraints(
            eval_output={"score": 0.8, "latency_ms": 100, "regressions": ["fixture Q-001 regressed"]},
            baseline_latency_ms=100,
        )
        assert result["constraints_ok"] is False

    def test_score_out_of_range(self):
        from eval.constraints import check_constraints
        result = check_constraints(
            eval_output={"score": 1.5, "latency_ms": 100, "regressions": []},
            baseline_latency_ms=100,
        )
        assert result["constraints_ok"] is False


# ---------------------------------------------------------------------------
# Logging tests
# ---------------------------------------------------------------------------

class TestLogging:
    def test_log_result_creates_tsv(self, tmp_path):
        from orchestrator.config import OrchestratorConfig
        from orchestrator.logging import log_result

        config = OrchestratorConfig(results_path=tmp_path / "RESULTS.tsv")
        log_result(
            config, iteration=1, hypothesis_id="H-001", status="accept",
            code="ACCEPT", score_before=0.5, score_after=0.8,
            tests_pass=True, summary="test change", reason="",
            constraints_ok=True, critic_severity="low",
            critic_recommendation="accept", changed_files_count=1,
        )
        content = (tmp_path / "RESULTS.tsv").read_text(encoding="utf-8")
        lines = content.strip().split("\n")
        assert len(lines) == 2  # header + 1 row
        assert "H-001" in lines[1]
        assert "ACCEPT" in lines[1]

    def test_log_decision_creates_md(self, tmp_path):
        from orchestrator.config import OrchestratorConfig
        from orchestrator.logging import log_decision

        config = OrchestratorConfig(decisions_path=tmp_path / "DECISIONS.md")
        log_decision(
            config, iteration=1, decision="accept", code="ACCEPT",
            score_before=0.5, score_after=0.8, tests_pass=True,
            summary="test", reason="",
            constraints_ok=True, critic_severity="low",
            critic_recommendation="accept",
        )
        content = (tmp_path / "DECISIONS.md").read_text(encoding="utf-8")
        assert "## Iteration 1" in content
        assert "critic_severity: low" in content

    def test_update_memory_adds_accepted(self, tmp_path):
        from orchestrator.config import OrchestratorConfig
        from orchestrator.logging import update_memory

        config = OrchestratorConfig(memory_path=tmp_path / "MEMORY.md")
        update_memory(config, "ACCEPT", "normalize punctuation", "")
        content = (tmp_path / "MEMORY.md").read_text(encoding="utf-8")
        assert "normalize punctuation" in content
        assert "Accepted Patterns" in content

    def test_update_memory_adds_rejected(self, tmp_path):
        from orchestrator.config import OrchestratorConfig
        from orchestrator.logging import update_memory

        config = OrchestratorConfig(memory_path=tmp_path / "MEMORY.md")
        update_memory(config, "TEST_FAIL", "bad change", "tests broke")
        content = (tmp_path / "MEMORY.md").read_text(encoding="utf-8")
        assert "bad change" in content
        assert "Rejected Patterns" in content

    def test_update_memory_trims_to_max(self, tmp_path):
        from orchestrator.config import OrchestratorConfig
        from orchestrator.logging import update_memory, MAX_MEMORY_ITEMS

        config = OrchestratorConfig(memory_path=tmp_path / "MEMORY.md")
        for i in range(MAX_MEMORY_ITEMS + 3):
            update_memory(config, "ACCEPT", f"change {i}", "")
        content = (tmp_path / "MEMORY.md").read_text(encoding="utf-8")
        items = [l for l in content.split("\n") if l.startswith("- ") and "change" in l]
        assert len(items) == MAX_MEMORY_ITEMS


# ---------------------------------------------------------------------------
# Integration tests: IterationRunner with mocked agents
# ---------------------------------------------------------------------------

class TestIterationRunnerIntegration:
    """Test full iteration pipeline with mocked subprocess calls."""

    def _setup_agent_files(self, tmp_path):
        """Create minimal agent state files for a test run."""
        agent = tmp_path / "agent"
        agent.mkdir()
        (agent / "PRODUCT_GOAL.md").write_text("# Goal\nImprove search relevance\n")
        (agent / "TASK.md").write_text("# Task\nNormalize queries\n")
        (agent / "RULES.md").write_text("# Rules\n- frozen eval immutable\n")
        (agent / "MEMORY.md").write_text("# MEMORY\n\n## Accepted Patterns\n\n## Rejected Patterns\n\n## Known Risks\n\n## Strategy Notes\n")
        (agent / "HYPOTHESES.md").write_text("### H-001: Normalize punctuation\n- status: selected\n- priority: high\n")
        (agent / "PLAN.md").write_text("# Plan\n## Change Scope\n- src/query_processor.py\n")
        (agent / "ITERATION_STATE.json").write_text('{"iteration":0,"mode":"single-agent","phase":"done","selected_hypothesis":null,"baseline_score":0.5,"last_updated":""}')

        eval_dir = tmp_path / "eval"
        eval_dir.mkdir()
        (eval_dir / "baseline.json").write_text('{"score": 0.5, "iteration": 0}')

        return agent

    def _make_config(self, tmp_path):
        from orchestrator.config import OrchestratorConfig
        return OrchestratorConfig(
            baseline_path=tmp_path / "eval" / "baseline.json",
            frozen_eval_path=Path("eval/frozen_eval.py"),
            tests_path=Path("tests"),
            results_path=tmp_path / "agent" / "RESULTS.tsv",
            decisions_path=tmp_path / "agent" / "DECISIONS.md",
            memory_path=tmp_path / "agent" / "MEMORY.md",
            state_path=tmp_path / "agent" / "ITERATION_STATE.json",
            tmp_path=tmp_path / "tmp",
            reports_path=tmp_path / "reports",
            use_git=False,
        )

    def test_full_iteration_accept(self, tmp_path, monkeypatch):
        """Test full iteration where score improves → accept."""
        self._setup_agent_files(tmp_path)
        config = self._make_config(tmp_path)

        # Mock state file path to use tmp
        config.state_path = tmp_path / "agent" / "ITERATION_STATE.json"

        # Mock agent functions
        from orchestrator import agents
        from orchestrator.agents import (
            ImplementerResult, TestsResult, EvalResult, CriticResult,
            ExplorerResult, PlannerResult,
        )

        mock_impl = ImplementerResult(["src/query_processor.py"], "improved normalize", "better matching")
        mock_tests = TestsResult(passed=True, total=7, duration_sec=0.1)
        mock_eval = EvalResult(score=0.8, constraints_ok=True)
        mock_critic = CriticResult(severity="low", recommendation="accept")
        mock_explorer = ExplorerResult(hypotheses=[{"id": "H-001", "status": "selected"}])
        mock_plan = PlannerResult(selected_hypothesis="H-001", change_scope=["src/query_processor.py"])

        monkeypatch.setattr(agents, "run_implementer", lambda *a, **kw: mock_impl)
        monkeypatch.setattr(agents, "run_tests", lambda *a, **kw: mock_tests)
        monkeypatch.setattr(agents, "run_eval", lambda *a, **kw: mock_eval)
        monkeypatch.setattr(agents, "run_critic", lambda *a, **kw: mock_critic)
        monkeypatch.setattr(agents, "run_explorer", lambda *a, **kw: mock_explorer)
        monkeypatch.setattr(agents, "run_planner", lambda *a, **kw: mock_plan)
        monkeypatch.setattr(agents, "rollback_change", lambda *a, **kw: None)

        from orchestrator.runner import IterationRunner
        runner = IterationRunner(config)
        ctrl = runner.run(iteration=1, baseline_score=0.5)

        assert ctrl.decision == "accept"
        assert ctrl.decision_code == "ACCEPT"
        assert ctrl.score_delta == pytest.approx(0.3)

        # Verify logging happened
        assert (tmp_path / "agent" / "RESULTS.tsv").exists()
        tsv = (tmp_path / "agent" / "RESULTS.tsv").read_text()
        assert "accept" in tsv
        assert "ACCEPT" in tsv

    def test_full_iteration_reject_on_test_fail(self, tmp_path, monkeypatch):
        """Test full iteration where tests fail → reject."""
        self._setup_agent_files(tmp_path)
        config = self._make_config(tmp_path)

        config.state_path = tmp_path / "agent" / "ITERATION_STATE.json"

        from orchestrator.agents import (
            ImplementerResult, TestsResult, EvalResult, CriticResult,
            ExplorerResult, PlannerResult,
        )
        import orchestrator.runner as runner_mod

        monkeypatch.setattr(runner_mod, "run_implementer", lambda *a, **kw: ImplementerResult(["a.py"], "change", "reason"))
        monkeypatch.setattr(runner_mod, "run_tests", lambda *a, **kw: TestsResult(passed=False, failed_tests=["test_a"]))
        monkeypatch.setattr(runner_mod, "run_eval", lambda *a, **kw: EvalResult(score=0.9))
        monkeypatch.setattr(runner_mod, "run_critic", lambda *a, **kw: CriticResult())
        monkeypatch.setattr(runner_mod, "run_explorer", lambda *a, **kw: ExplorerResult([{"id": "H-001", "status": "selected"}]))
        monkeypatch.setattr(runner_mod, "run_planner", lambda *a, **kw: PlannerResult(selected_hypothesis="H-001"))
        monkeypatch.setattr(runner_mod, "rollback_change", lambda *a, **kw: None)

        from orchestrator.runner import IterationRunner
        ctrl = IterationRunner(config).run(iteration=1, baseline_score=0.5)

        assert ctrl.decision == "reject"
        assert ctrl.decision_code == "TEST_FAIL"

    def test_full_iteration_error_recovery(self, tmp_path, monkeypatch):
        """Test that pipeline errors are caught and result in reject."""
        self._setup_agent_files(tmp_path)
        config = self._make_config(tmp_path)

        config.state_path = tmp_path / "agent" / "ITERATION_STATE.json"

        from orchestrator.agents import ExplorerResult, PlannerResult
        import orchestrator.runner as runner_mod

        monkeypatch.setattr(runner_mod, "run_explorer", lambda *a, **kw: ExplorerResult([{"id": "H-001", "status": "selected"}]))
        monkeypatch.setattr(runner_mod, "run_planner", lambda *a, **kw: PlannerResult(selected_hypothesis="H-001"))

        def raise_error(*a, **kw):
            raise RuntimeError("CLI crashed")

        monkeypatch.setattr(runner_mod, "run_implementer", raise_error)
        monkeypatch.setattr(runner_mod, "rollback_change", lambda *a, **kw: None)

        from orchestrator.runner import IterationRunner
        ctrl = IterationRunner(config).run(iteration=1, baseline_score=0.5)

        assert ctrl.decision == "reject"
        assert ctrl.decision_code == "EVAL_CRASH"
        assert "Pipeline error" in ctrl.reason


# ---------------------------------------------------------------------------
# LoopOrchestrator integration test
# ---------------------------------------------------------------------------

class TestLoopOrchestratorIntegration:
    def test_loop_stops_on_stagnation(self, tmp_path, monkeypatch):
        """Test that loop stops after max_no_improvement_streak."""
        from orchestrator.config import OrchestratorConfig
        from orchestrator.agents import ControllerResult

        config = OrchestratorConfig(
            max_iterations=10,
            max_no_improvement_streak=2,
            baseline_path=tmp_path / "baseline.json",
            tmp_path=tmp_path / "tmp",
            reports_path=tmp_path / "reports",
            allow_dirty=True,
        )
        (tmp_path / "baseline.json").write_text('{"score": 0.5}')

        call_count = 0

        def mock_run(iteration, baseline_score, hypothesis="H-001"):
            nonlocal call_count
            call_count += 1
            # Always return reject (no improvement)
            return ControllerResult(
                decision="reject", decision_code="NO_IMPROVEMENT",
                score_after=0.5, score_before=0.5, score_delta=0.0,
            )

        from orchestrator.loop import LoopOrchestrator
        orch = LoopOrchestrator(config)
        monkeypatch.setattr(orch.runner, "run", mock_run)

        result = orch.run()
        assert result["status"] == "completed"
        assert call_count == 2  # stops after 2 consecutive no-improvement

    def test_loop_stops_on_target_score(self, tmp_path, monkeypatch):
        """Test that loop stops when target score is reached."""
        from orchestrator.config import OrchestratorConfig
        from orchestrator.agents import ControllerResult

        config = OrchestratorConfig(
            max_iterations=10,
            target_score=0.9,
            baseline_path=tmp_path / "baseline.json",
            tmp_path=tmp_path / "tmp",
            reports_path=tmp_path / "reports",
            allow_dirty=True,
        )
        (tmp_path / "baseline.json").write_text('{"score": 0.5}')

        iteration_scores = [0.7, 0.9]
        call_count = 0

        def mock_run(iteration, baseline_score, hypothesis="H-001"):
            nonlocal call_count
            score = iteration_scores[call_count]
            call_count += 1
            # Update baseline file
            (tmp_path / "baseline.json").write_text(json.dumps({"score": score}))
            return ControllerResult(
                decision="accept", decision_code="ACCEPT",
                score_after=score, score_before=baseline_score,
                score_delta=round(score - baseline_score, 6),
            )

        from orchestrator.loop import LoopOrchestrator
        orch = LoopOrchestrator(config)
        monkeypatch.setattr(orch.runner, "run", mock_run)

        result = orch.run()
        assert result["status"] == "completed"
        assert result["final_score"] == 0.9
        assert call_count == 2


# ---------------------------------------------------------------------------
# Rollback test
# ---------------------------------------------------------------------------

class TestRollback:
    def test_rollback_skips_without_git(self, tmp_path):
        from orchestrator.config import OrchestratorConfig
        from orchestrator.agents import rollback_change

        config = OrchestratorConfig(use_git=False)
        # Should not raise — just returns
        rollback_change(config)


# ---------------------------------------------------------------------------
# TSV escaping test
# ---------------------------------------------------------------------------

class TestTSVEscaping:
    def test_tab_in_summary_replaced(self, tmp_path):
        from orchestrator.config import OrchestratorConfig
        from orchestrator.logging import log_result

        config = OrchestratorConfig(results_path=tmp_path / "RESULTS.tsv")
        log_result(
            config, iteration=1, hypothesis_id="H-001", status="accept",
            code="ACCEPT", score_before=0.5, score_after=0.8,
            tests_pass=True, summary="change\twith\ttabs", reason="reason\there",
        )
        content = (tmp_path / "RESULTS.tsv").read_text()
        data_line = content.strip().split("\n")[1]
        # Should have exactly 15 tab-separated columns (no extra tabs from summary)
        assert len(data_line.split("\t")) == 15

    def test_results_tsv_roundtrip(self, tmp_path):
        """Write a row, read it back, verify all 15 columns parse correctly."""
        from orchestrator.config import OrchestratorConfig
        from orchestrator.logging import log_result, RESULTS_HEADER

        config = OrchestratorConfig(results_path=tmp_path / "RESULTS.tsv")
        log_result(
            config, iteration=3, hypothesis_id="H-002", status="reject",
            code="SCORE_REGRESSION", score_before=0.8, score_after=0.6,
            tests_pass=True, summary="added synonym expansion", reason="score dropped",
            constraints_ok=True, critic_severity="medium",
            critic_recommendation="reject", changed_files_count=2,
        )
        content = (tmp_path / "RESULTS.tsv").read_text(encoding="utf-8")
        lines = content.strip().split("\n")
        headers = lines[0].split("\t")
        values = lines[1].split("\t")
        row = dict(zip(headers, values))

        assert len(headers) == 15
        assert len(values) == 15
        assert headers == RESULTS_HEADER
        assert row["iteration"] == "3"
        assert row["hypothesis_id"] == "H-002"
        assert row["status"] == "reject"
        assert row["decision_code"] == "SCORE_REGRESSION"
        assert float(row["score_before"]) == 0.8
        assert float(row["score_after"]) == 0.6
        assert float(row["score_delta"]) == pytest.approx(-0.2)
        assert row["tests_pass"] == "true"
        assert row["constraints_ok"] == "true"
        assert row["critic_severity"] == "medium"
        assert row["changed_files_count"] == "2"
        assert row["change_summary"] == "added synonym expansion"
        assert row["rollback_reason"] == "score dropped"


# ---------------------------------------------------------------------------
# LLM provider tests
# ---------------------------------------------------------------------------

class TestLLMProvider:
    def test_find_llm_cmd_returns_list_or_none(self):
        from orchestrator.agents import _find_llm_cmd
        result = _find_llm_cmd("claude")
        assert result is None or isinstance(result, list)

    def test_find_llm_cmd_unknown_provider(self):
        from orchestrator.agents import _find_llm_cmd
        assert _find_llm_cmd("unknown_provider") is None

    def test_check_llm_auth_returns_dict(self):
        from orchestrator.agents import check_llm_auth
        result = check_llm_auth("claude")
        assert "authenticated" in result
        assert "provider" in result
        assert "message" in result

    def test_check_llm_auth_unknown_provider(self):
        from orchestrator.agents import check_llm_auth
        result = check_llm_auth("nonexistent")
        assert result["authenticated"] is False


# ---------------------------------------------------------------------------
# Iteration numbering test
# ---------------------------------------------------------------------------

class TestIterationNumbering:
    def test_get_last_iteration_empty(self, tmp_path):
        from orchestrator.config import OrchestratorConfig
        from orchestrator.loop import _get_last_iteration

        config = OrchestratorConfig(results_path=tmp_path / "RESULTS.tsv")
        assert _get_last_iteration(config) == 0

    def test_get_last_iteration_with_data(self, tmp_path):
        from orchestrator.config import OrchestratorConfig
        from orchestrator.loop import _get_last_iteration

        tsv = tmp_path / "RESULTS.tsv"
        tsv.write_text(
            "iteration\tother\n"
            "1\tdata\n"
            "2\tdata\n"
            "5\tdata\n",
            encoding="utf-8",
        )
        config = OrchestratorConfig(results_path=tsv)
        assert _get_last_iteration(config) == 5

    def test_get_last_iteration_header_only(self, tmp_path):
        from orchestrator.config import OrchestratorConfig
        from orchestrator.loop import _get_last_iteration

        tsv = tmp_path / "RESULTS.tsv"
        tsv.write_text("iteration\tother\n", encoding="utf-8")
        config = OrchestratorConfig(results_path=tsv)
        assert _get_last_iteration(config) == 0
