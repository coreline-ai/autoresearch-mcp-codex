"""Single iteration runner with full agent pipeline.

Workflow (doc spec):
  INIT -> READ_CONTEXT -> EXPLORE -> PLAN -> IMPLEMENT -> RUN_TESTS
  -> RUN_EVAL -> CRITIQUE -> DECIDE -> ACCEPT/REJECT -> ARCHIVE -> DONE
"""

from __future__ import annotations

import traceback

from .agents import (
    ControllerResult,
    EvalResult,
    TestsResult,
    ImplementerResult,
    CriticResult,
    load_agent_context,
    run_explorer,
    select_hypothesis,
    run_planner,
    run_implementer,
    run_tests,
    run_eval,
    run_critic,
    run_controller,
    rollback_change,
    check_change_budget,
    _detect_git_changes,
    update_hypothesis_status,
)
from .config import OrchestratorConfig, save_baseline
from .logging import log_result, log_decision, update_memory
from .state import Phase, DecisionCode, init_state, update_phase, update_state_fields


class IterationRunner:
    def __init__(self, config: OrchestratorConfig | None = None):
        self.config = config or OrchestratorConfig()
        # Track consecutive NO_CODE_CHANGE per hypothesis to avoid infinite retry
        self._no_change_counts: dict[str, int] = {}

    def _update_phase(self, phase: Phase) -> None:
        update_phase(phase, self.config.state_path)

    def run(self, iteration: int, baseline_score: float, hypothesis: str = "H-001") -> ControllerResult:
        print(f"\n[iteration {iteration}] Starting...")
        sp = self.config.state_path

        # Phase: INIT
        init_state(iteration, self.config.mode, hypothesis, baseline_score, sp)

        # Defaults for error recovery — intentionally pessimistic.
        # If a phase crashes, these defaults ensure logs reflect
        # "not verified" rather than false positives.
        selected = hypothesis
        impl = ImplementerResult([], "", "", is_placeholder=True)
        test_result = TestsResult(passed=False)
        eval_result = EvalResult(score=0.0, constraints_ok=False)
        critic_result = CriticResult(severity="unknown", recommendation="reject")

        try:
            # Phase: READ_CONTEXT
            self._update_phase(Phase.READ_CONTEXT)
            context = load_agent_context(self.config)
            print(f"[iteration {iteration}] Context loaded ({len(context)} files)")

            # Phase: EXPLORE
            self._update_phase(Phase.EXPLORE)
            explorer_result = run_explorer(self.config, context)
            selected = select_hypothesis(explorer_result)
            if selected is None:
                print(f"[iteration {iteration}] All hypotheses exhausted --no actionable hypothesis remaining")
                raise StopIteration("All hypotheses exhausted")
            update_state_fields(sp, selected_hypothesis=selected)
            print(f"[iteration {iteration}] Explorer: {len(explorer_result.hypotheses)} hypotheses, selected={selected}")

            # Phase: PLAN
            self._update_phase(Phase.PLAN)
            plan = run_planner(self.config, context, selected)
            print(f"[iteration {iteration}] Plan: scope={plan.change_scope}")

            # Phase: IMPLEMENT
            self._update_phase(Phase.IMPLEMENT)
            impl = run_implementer(self.config, selected, plan)
            print(f"[iteration {iteration}] Implementer: {impl.changed_files} (placeholder={impl.is_placeholder})")

            # Post-implement validation: actual git changes, budget, scope
            if self.config.use_git and not impl.is_placeholder:
                actual = _detect_git_changes()
                if actual != impl.changed_files:
                    impl.changed_files = actual
                    impl.notes.append(f"changed_files updated from git diff: {actual}")
                # Budget check
                within, budget_info = check_change_budget()
                if not within:
                    impl.scope_respected = False
                    impl.notes.append(
                        f"Change budget exceeded: {budget_info['changed_files']} files, "
                        f"{budget_info['diff_lines']} lines"
                    )
                # Scope check: verify changed files are within plan scope
                if plan.change_scope:
                    for f in impl.changed_files:
                        if not any(f.startswith(s) or f == s for s in plan.change_scope):
                            impl.scope_respected = False
                            impl.notes.append(f"Out-of-scope change: {f}")

            # Phase: RUN_TESTS
            self._update_phase(Phase.RUN_TESTS)
            test_result = run_tests(self.config)
            update_state_fields(sp, tests_pass=test_result.passed)
            print(f"[iteration {iteration}] Tests: passed={test_result.passed} ({test_result.total} tests, {test_result.duration_sec}s)")

            # Phase: RUN_EVAL
            self._update_phase(Phase.RUN_EVAL)
            eval_result = run_eval(self.config)
            update_state_fields(sp, candidate_score=eval_result.score, constraints_ok=eval_result.constraints_ok)
            print(f"[iteration {iteration}] Eval: score={eval_result.score}")

            # Phase: CRITIQUE
            self._update_phase(Phase.CRITIQUE)
            critic_result = run_critic(self.config, plan, impl, test_result, eval_result, baseline_score)
            print(f"[iteration {iteration}] Critic: severity={critic_result.severity}, rec={critic_result.recommendation}")

            # Phase: DECIDE
            self._update_phase(Phase.DECIDE)
            ctrl = run_controller(
                self.config,
                score_before=baseline_score,
                eval_result=eval_result,
                test_result=test_result,
                impl_result=impl,
                critic_result=critic_result,
            )

        except Exception as e:
            print(f"[iteration {iteration}] ERROR in pipeline: {e}")
            traceback.print_exc()
            self._update_phase(Phase.ERROR)
            ctrl = ControllerResult(
                decision="reject",
                decision_code=DecisionCode.EVAL_CRASH.value,
                score_after=eval_result.score,
                score_before=baseline_score,
                score_delta=round(eval_result.score - baseline_score, 6),
                reason=f"Pipeline error: {e}",
                next_action="rollback_and_continue",
            )

        update_state_fields(sp, decision=ctrl.decision)
        print(f"[iteration {iteration}] Decision: {ctrl.decision} ({ctrl.decision_code}) -- {ctrl.reason}")

        # Phase: ACCEPT / REJECT / ROLLBACK
        if ctrl.decision == "accept":
            self._update_phase(Phase.ACCEPT)
            save_baseline(self.config, eval_result.score, iteration)
        else:
            self._update_phase(Phase.REJECT)
            if ctrl.decision == "hold":
                print(f"[iteration {iteration}] HOLD -- requires manual review")
            self._update_phase(Phase.ROLLBACK)
            rollback_ok = rollback_change(self.config)
            if not rollback_ok:
                print(f"[iteration {iteration}] WARNING: rollback failed, state may be inconsistent")
                self._update_phase(Phase.ERROR)

        # Phase: ARCHIVE
        self._update_phase(Phase.ARCHIVE)
        rollback_reason = "" if ctrl.decision == "accept" else ctrl.reason
        log_result(
            config=self.config,
            iteration=iteration,
            hypothesis_id=selected,
            status=ctrl.decision,
            code=ctrl.decision_code,
            score_before=baseline_score,
            score_after=eval_result.score,
            tests_pass=test_result.passed,
            constraints_ok=eval_result.constraints_ok,
            critic_severity=ctrl.critic_severity,
            critic_recommendation=ctrl.critic_recommendation,
            changed_files_count=len(impl.changed_files),
            summary=impl.change_summary,
            reason=rollback_reason,
        )
        log_decision(
            config=self.config,
            iteration=iteration,
            decision=ctrl.decision,
            code=ctrl.decision_code,
            score_before=baseline_score,
            score_after=eval_result.score,
            tests_pass=test_result.passed,
            constraints_ok=eval_result.constraints_ok,
            critic_severity=ctrl.critic_severity,
            critic_recommendation=ctrl.critic_recommendation,
            changed_files_count=len(impl.changed_files),
            summary=impl.change_summary,
            reason=rollback_reason,
        )
        update_memory(self.config, ctrl.decision_code, impl.change_summary, rollback_reason)

        # Update hypothesis status based on decision
        if ctrl.decision == "accept":
            update_hypothesis_status(self.config, selected, "accepted")
        elif ctrl.decision_code == "NO_CODE_CHANGE":
            # First NO_CODE_CHANGE: keep hypothesis for retry (CLI might appear later).
            # Second consecutive: mark as "tried" so explorer moves to next hypothesis.
            self._no_change_counts[selected] = self._no_change_counts.get(selected, 0) + 1
            if self._no_change_counts[selected] >= 2:
                update_hypothesis_status(self.config, selected, "tried")
                print(f"[iteration {iteration}] {selected} marked 'tried' after {self._no_change_counts[selected]}x NO_CODE_CHANGE")
        else:
            update_hypothesis_status(self.config, selected, "rejected")

        # Phase: DONE
        self._update_phase(Phase.DONE)
        print(f"[iteration {iteration}] Completed: {ctrl.decision} (score: {baseline_score} -> {eval_result.score})")
        return ctrl
