"""Agent execution functions for AutoResearch Agent System.

Each function corresponds to one agent role defined in prompts/*.md.
Implements the full multi-agent pipeline: Explorer -> Planner -> Implementer ->
Tests -> Eval -> Critic -> Controller with 9-level decision engine.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from .state import DecisionCode, Decision


# ---------------------------------------------------------------------------
# Data models (doc 11 spec)
# ---------------------------------------------------------------------------

@dataclass
class ImplementerResult:
    """Output from the Implementer agent."""
    changed_files: list[str]
    change_summary: str
    why_this_change: str
    notes: list[str] = field(default_factory=list)
    verification_commands_run: list[str] = field(default_factory=list)
    scope_respected: bool = True
    forbidden_paths_touched: list[str] = field(default_factory=list)
    estimated_risk: str = "low"
    is_placeholder: bool = False


@dataclass
class EvalResult:
    """Output from frozen evaluation."""
    score: float
    tests_pass: bool = True
    constraints_ok: bool = True
    latency_ms: int | None = None
    latency_delta_pct: float | None = None
    regressions: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    details: dict = field(default_factory=dict)


@dataclass
class TestsResult:
    """Output from test execution."""
    passed: bool
    summary: str = ""
    failed_tests: list[str] = field(default_factory=list)
    duration_sec: float = 0.0
    stderr: str = ""
    total: int = 0


@dataclass
class CriticResult:
    """Output from the Critic agent."""
    severity: str = "low"          # low | medium | high
    objections: list[str] = field(default_factory=list)
    recommendation: str = "accept"  # accept | reject | accept_with_monitoring | hold
    reasoning: str = ""


@dataclass
class ExplorerResult:
    """Output from the Explorer agent."""
    hypotheses: list[dict] = field(default_factory=list)


@dataclass
class PlannerResult:
    """Output from the Planner agent."""
    selected_hypothesis: str = ""
    change_scope: list[str] = field(default_factory=list)
    planned_change: str = ""
    expected_effect: str = ""
    risks: list[str] = field(default_factory=list)
    tests_to_run: list[str] = field(default_factory=list)
    reject_conditions: list[str] = field(default_factory=list)


@dataclass
class ControllerResult:
    """Output from the Controller (decision engine)."""
    decision: str
    decision_code: str
    score_after: float
    score_before: float
    score_delta: float
    reason: str = ""
    next_action: str = ""
    critic_severity: str = "low"
    critic_recommendation: str = "accept"


# ---------------------------------------------------------------------------
# Agent context loader
# ---------------------------------------------------------------------------

def load_agent_context(config) -> dict[str, str]:
    """Read all agent state files into a context dict."""
    agent_dir = Path("agent")
    context = {}
    file_map = {
        "product_goal": "PRODUCT_GOAL.md",
        "task": "TASK.md",
        "rules": "RULES.md",
        "memory": "MEMORY.md",
        "hypotheses": "HYPOTHESES.md",
        "plan": "PLAN.md",
    }
    for key, filename in file_map.items():
        p = agent_dir / filename
        context[key] = p.read_text(encoding="utf-8") if p.exists() else ""
    # Load RESULTS.tsv
    if config.results_path.exists():
        context["results"] = config.results_path.read_text(encoding="utf-8")
    else:
        context["results"] = ""
    return context


# ---------------------------------------------------------------------------
# Explorer agent
# ---------------------------------------------------------------------------

def run_explorer(config, context: dict[str, str]) -> ExplorerResult:
    """Generate hypothesis candidates based on current state.

    Reads: PRODUCT_GOAL, TASK, MEMORY, RESULTS.tsv, HYPOTHESES
    Output: List of hypothesis dicts (id, title, expected_effect, risk, priority)

    Currently reads existing HYPOTHESES.md and returns parsed hypotheses.
    Integration with Codex CLI will replace this with dynamic generation.
    """
    config.tmp_path.mkdir(parents=True, exist_ok=True)
    hypotheses = []

    # Parse existing HYPOTHESES.md
    # Supports two formats:
    #   Format A (current): "- H-001\n  - title: ...\n  - status: ..."
    #   Format B (legacy):  "### H-001: Title\n- status: ..."
    hyp_text = context.get("hypotheses", "")
    current_hyp: dict[str, str] = {}
    import re
    for line in hyp_text.split("\n"):
        stripped = line.strip()

        # Format B: "### H-001: Title"
        if stripped.startswith("### "):
            if current_hyp and "id" in current_hyp:
                hypotheses.append(current_hyp)
            header = stripped[4:].strip()
            parts = header.split(":", 1)
            current_hyp = {
                "id": parts[0].strip(),
                "title": parts[1].strip() if len(parts) > 1 else header,
            }

        # Format A: top-level "- H-XXX" (not indented)
        elif re.match(r'^- (H-\d+)', stripped) and not line.startswith("  "):
            if current_hyp and "id" in current_hyp:
                hypotheses.append(current_hyp)
            m = re.match(r'^- (H-\d+)', stripped)
            current_hyp = {"id": m.group(1)}

        # Indented field: "  - key: value"
        elif stripped.startswith("- ") and current_hyp:
            key_val = stripped[2:].split(":", 1)
            if len(key_val) == 2:
                key = key_val[0].strip().lower().replace(" ", "_")
                val = key_val[1].strip()
                current_hyp[key] = val

    if current_hyp and "id" in current_hyp:
        hypotheses.append(current_hyp)

    result = ExplorerResult(hypotheses=hypotheses)
    (config.tmp_path / "explorer_result.json").write_text(
        json.dumps({"hypotheses": hypotheses}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return result


TERMINAL_STATUSES = {"accepted", "rejected", "tried", "exhausted"}


def select_hypothesis(explorer_result: ExplorerResult) -> str | None:
    """Select the next actionable hypothesis.

    Skips hypotheses that are already accepted, rejected, tried, or exhausted.
    Priority: status=selected > status=proposed (by priority) > first available.
    Returns None if all hypotheses are in terminal state.
    """
    hypotheses = explorer_result.hypotheses
    if not hypotheses:
        return None

    # Filter out terminal hypotheses
    actionable = [h for h in hypotheses if h.get("status", "").lower() not in TERMINAL_STATUSES]
    if not actionable:
        return None

    # Prefer explicitly selected
    for h in actionable:
        if h.get("status", "").lower() == "selected":
            return h["id"]

    # Then by priority among proposed/unmarked
    priority_order = {"high": 0, "medium": 1, "low": 2}
    actionable.sort(key=lambda h: priority_order.get(h.get("priority", "medium").lower(), 1))
    return actionable[0]["id"]


def update_hypothesis_status(config, hypothesis_id: str, new_status: str) -> None:
    """Update a hypothesis status in HYPOTHESES.md.

    Status transitions:
      selected → tried → accepted/rejected
      proposed → selected (when picked) → tried → accepted/rejected
      parked   → (untouched unless explicitly selected)
    """
    hyp_path = Path("agent/HYPOTHESES.md")
    if not hyp_path.exists():
        return

    lines = hyp_path.read_text(encoding="utf-8").split("\n")
    import re as _re
    in_target = False
    updated = False

    for i, line in enumerate(lines):
        stripped = line.strip()
        # Detect hypothesis header (Format A: "- H-001")
        m = _re.match(r'^- (H-\d+)', stripped)
        if m:
            in_target = (m.group(1) == hypothesis_id)
            continue
        # Also handle Format B: "### H-001: ..."
        if stripped.startswith("### "):
            header_id = stripped[4:].split(":")[0].strip()
            in_target = (header_id == hypothesis_id)
            continue

        # Update status field within target hypothesis
        if in_target and "status:" in stripped.lower():
            # Preserve indentation
            indent = line[:len(line) - len(line.lstrip())]
            prefix = "- " if stripped.startswith("- ") else ""
            lines[i] = f"{indent}{prefix}status: {new_status}"
            updated = True
            in_target = False  # Done with this hypothesis

    if updated:
        hyp_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"[hypotheses] {hypothesis_id} -> {new_status}")


# ---------------------------------------------------------------------------
# Planner agent
# ---------------------------------------------------------------------------

def run_planner(config, context: dict[str, str], hypothesis_id: str) -> PlannerResult:
    """Create execution plan for selected hypothesis.

    Reads: PRODUCT_GOAL, TASK, RULES, MEMORY, selected hypothesis
    Output: PlannerResult with change_scope, tests_to_run, reject_conditions

    Currently reads existing PLAN.md. Integration with Codex CLI will
    replace this with dynamic plan generation.
    """
    config.tmp_path.mkdir(parents=True, exist_ok=True)
    plan_text = context.get("plan", "")
    result = PlannerResult(selected_hypothesis=hypothesis_id)

    # Parse PLAN.md sections
    # Supports both "- item" bullet lists and "1. item" numbered lists
    import re as _re
    current_section = ""
    for line in plan_text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("## "):
            current_section = stripped[3:].strip().lower()
        elif current_section and (stripped.startswith("- ") or _re.match(r'^\d+\.\s', stripped)):
            # Extract value from "- item" or "1. item"
            if stripped.startswith("- "):
                value = stripped[2:].strip()
            else:
                value = _re.sub(r'^\d+\.\s*', '', stripped).strip()
            # Remove markdown backticks from paths
            value = value.strip("`")

            if "change scope" in current_section or "변경 범위" in current_section:
                result.change_scope.append(value)
            elif "risk" in current_section or "위험" in current_section:
                result.risks.append(value)
            elif "test" in current_section or "테스트" in current_section:
                result.tests_to_run.append(value)
            elif "reject" in current_section or "기각" in current_section:
                result.reject_conditions.append(value)
            elif "planned change" in current_section or "계획된 변경" in current_section:
                result.planned_change += value + " "
            elif "expected" in current_section or "기대 효과" in current_section:
                result.expected_effect += value + " "
        elif current_section and not stripped.startswith("#"):
            if "planned change" in current_section or "계획된 변경" in current_section:
                if stripped:
                    result.planned_change += stripped + " "
            elif "expected" in current_section or "기대 효과" in current_section:
                if stripped:
                    result.expected_effect += stripped + " "

    result.planned_change = result.planned_change.strip()
    result.expected_effect = result.expected_effect.strip()

    (config.tmp_path / "planner_result.json").write_text(
        json.dumps({
            "selected_hypothesis": result.selected_hypothesis,
            "change_scope": result.change_scope,
            "planned_change": result.planned_change,
            "expected_effect": result.expected_effect,
            "risks": result.risks,
            "tests_to_run": result.tests_to_run,
            "reject_conditions": result.reject_conditions,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return result


# ---------------------------------------------------------------------------
# Implementer agent
# ---------------------------------------------------------------------------

def _build_implementer_prompt(context: dict[str, str], hypothesis: str, plan: PlannerResult | None) -> str:
    """Build the prompt string sent to Claude for implementation.

    Includes system prompt, agent context, plan details, AND the current
    source code of files in scope so Claude can make informed modifications.
    """
    prompt_path = Path("prompts/implementer.md")
    system_prompt = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else ""

    # Put the action instruction FIRST so it doesn't get buried in context
    scope_str = ", ".join(plan.change_scope) if plan and plan.change_scope else "src/query_processor.py"
    change_str = plan.planned_change if plan and plan.planned_change else hypothesis

    sections = [
        f"# YOUR TASK\n"
        f"Edit the file {scope_str} to implement: {change_str}\n"
        f"You MUST use the Edit or Write tool to modify the file on disk.\n"
        f"Do NOT just describe the change -- actually apply it.\n"
        f"Keep the diff small (under 20 lines). After editing, output JSON:\n"
        f'{{"changed_files": ["{scope_str}"], "change_summary": "...", "why_this_change": "...", "notes": []}}\n',
        f"# System\n{system_prompt}",
        f"# Goal\n{context.get('product_goal', '')}",
        f"# Task\n{context.get('task', '')}",
        f"# Rules\n{context.get('rules', '')}",
        f"# Memory\n{context.get('memory', '')}",
        f"# Hypothesis\n{hypothesis}",
    ]
    if plan:
        sections.append(
            f"# Plan\n"
            f"- scope: {plan.change_scope}\n"
            f"- change: {plan.planned_change}\n"
            f"- tests: {plan.tests_to_run}\n"
            f"- reject_conditions: {plan.reject_conditions}"
        )

    # Include current source code of target files
    if plan and plan.change_scope:
        source_parts: list[str] = []
        for filepath in plan.change_scope:
            p = Path(filepath)
            if p.exists():
                try:
                    content = p.read_text(encoding="utf-8")
                    source_parts.append(f"## {filepath}\n```python\n{content}\n```")
                except Exception:
                    source_parts.append(f"## {filepath}\n(could not read)")
        if source_parts:
            sections.append("# Current Source Code\n" + "\n\n".join(source_parts))

    sections.append(
        "# Reminder\n"
        "Now edit the file(s) listed above. Use the Edit tool. Then output the JSON summary."
    )
    return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# LLM Provider abstraction (Claude Code CLI / OpenAI Codex CLI)
# ---------------------------------------------------------------------------

def _find_llm_cmd(provider: str = "claude") -> list[str] | None:
    """Find the LLM CLI command for the given provider.

    Supports:
      - "claude": Claude Code CLI (claude or npx @anthropic-ai/claude-code)
      - "codex":  OpenAI Codex CLI (codex or npx @openai/codex)

    Both use OAuth login -- no API key required.

    On Windows, subprocess needs the .cmd extension for npx.
    """
    import shutil

    package_map = {"claude": "@anthropic-ai/claude-code", "codex": "@openai/codex"}
    pkg = package_map.get(provider)
    if not pkg:
        return None

    # Direct binary
    direct = shutil.which(provider)  # "claude" or "codex"
    if direct:
        return [direct]

    # npx fallback — on Windows, shutil.which finds npx.cmd correctly
    npx = shutil.which("npx")
    if npx:
        return [npx, "--yes", pkg]

    return None


def check_llm_auth(provider: str = "claude") -> dict:
    """Check if the LLM CLI is authenticated via OAuth.

    Returns: {"authenticated": bool, "provider": str, "message": str}
    """
    cmd = _find_llm_cmd(provider)
    if not cmd:
        return {"authenticated": False, "provider": provider,
                "message": f"{provider} CLI not found. Install and run OAuth login first."}

    try:
        if provider == "claude":
            # Check credentials file directly (works for both direct and npx installs)
            cred_path = Path.home() / ".claude" / ".credentials.json"
            if cred_path.exists():
                try:
                    creds = json.loads(cred_path.read_text(encoding="utf-8"))
                    oauth = creds.get("claudeAiOauth", {})
                    if oauth.get("accessToken"):
                        return {"authenticated": True, "provider": "claude",
                                "message": "Claude OAuth credentials found"}
                except Exception:
                    pass
            return {"authenticated": False, "provider": "claude",
                    "message": "Not authenticated. Run: claude auth login"}

        elif provider == "codex":
            # Codex doesn't have `auth status`; check if credentials file exists
            cred_path = Path.home() / ".codex" / "auth.json"
            if cred_path.exists():
                creds = json.loads(cred_path.read_text(encoding="utf-8"))
                if creds.get("token") or creds.get("access_token"):
                    return {"authenticated": True, "provider": "codex",
                            "message": "Codex OAuth credentials found"}
            return {"authenticated": False, "provider": "codex",
                    "message": "Not authenticated. Run: codex login"}

    except Exception as e:
        return {"authenticated": False, "provider": provider,
                "message": f"Auth check failed: {e}"}

    return {"authenticated": False, "provider": provider, "message": "Unknown error"}


def _call_llm_cli(prompt: str, config=None, provider: str = "claude",
                   timeout: int = 300, max_turns: int = 3) -> dict | None:
    """Call LLM CLI (Claude or Codex) to implement changes.

    Both CLIs support OAuth login -- no API key needed.
    Prompt is piped via stdin to avoid command-line length limits.

    Claude: claude --output-format json --max-turns N -p -
    Codex:  codex exec --json -q "prompt"
    """
    tmp_dir = Path(config.tmp_path if config else "tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    # Save prompt for debugging
    (tmp_dir / "implementer_prompt.txt").write_text(prompt, encoding="utf-8")

    cmd = _find_llm_cmd(provider)
    if not cmd:
        print(f"[implementer] {provider} CLI not found --falling back to placeholder")
        return None

    try:
        # Force UTF-8 encoding for subprocess I/O (prevents cp949 errors on Windows)
        env = {**subprocess.os.environ, "PYTHONIOENCODING": "utf-8"}

        if provider == "claude":
            r = subprocess.run(
                cmd + [
                    "--dangerously-skip-permissions",
                    "--output-format", "json",
                    "--max-turns", str(max_turns),
                    "-p", "-",
                ],
                input=prompt,
                capture_output=True, text=True, timeout=timeout, cwd=Path.cwd(),
                encoding="utf-8", errors="replace", env=env,
            )
        elif provider == "codex":
            r = subprocess.run(
                cmd + ["exec", "--json", "-q", prompt[:8000]],
                capture_output=True, text=True, timeout=timeout, cwd=Path.cwd(),
                encoding="utf-8", errors="replace", env=env,
            )
        else:
            print(f"[implementer] Unknown provider: {provider}")
            return None

        if r.returncode != 0:
            print(f"[implementer] {provider} CLI exited {r.returncode}: {r.stderr[:500]}")
            return None

        stdout = r.stdout.strip()
        if not stdout:
            print(f"[implementer] {provider} CLI returned empty output")
            return None

        # Parse JSON output
        return _parse_llm_output(stdout, provider)

    except FileNotFoundError:
        print(f"[implementer] {provider} CLI not found --falling back to placeholder")
        return None
    except subprocess.TimeoutExpired:
        print(f"[implementer] {provider} CLI timed out after {timeout}s")
        return None
    except Exception as e:
        print(f"[implementer] {provider} CLI error: {e}")
        return None


def _parse_llm_output(stdout: str, provider: str) -> dict | None:
    """Parse JSON output from Claude or Codex CLI."""
    try:
        wrapper = json.loads(stdout)
    except json.JSONDecodeError:
        start = stdout.find("{")
        end = stdout.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                wrapper = json.loads(stdout[start:end])
            except json.JSONDecodeError:
                print(f"[implementer] No valid JSON in {provider} output ({len(stdout)} chars)")
                return None
        else:
            print(f"[implementer] No JSON found in {provider} output")
            return None

    if not isinstance(wrapper, dict):
        return None

    # Claude wraps in {"result": "...text with JSON..."}
    if provider == "claude" and "result" in wrapper:
        text = wrapper["result"]
        if isinstance(text, str) and "{" in text:
            inner_start = text.find("{")
            inner_end = text.rfind("}") + 1
            if inner_start >= 0 and inner_end > inner_start:
                try:
                    return json.loads(text[inner_start:inner_end])
                except json.JSONDecodeError:
                    pass

    # Direct structured output
    if "changed_files" in wrapper:
        return wrapper

    # CLI executed but no structured JSON -- git diff will detect changes
    summary = ""
    if "result" in wrapper and isinstance(wrapper["result"], str):
        summary = wrapper["result"][:200]
    elif "output" in wrapper and isinstance(wrapper["output"], str):
        summary = wrapper["output"][:200]

    print(f"[implementer] {provider} executed but no structured JSON; using git diff")
    return {
        "changed_files": [],
        "change_summary": summary or f"{provider} completed",
        "why_this_change": "",
        "notes": [f"change detection via git diff ({provider})"],
    }


# Paths excluded from git diff change detection (pipeline-managed files)
_GIT_DIFF_EXCLUDE = {"agent/", "eval/baseline.json", "tmp/", "reports/", ".venv/", "__pycache__/"}


def _detect_git_changes() -> list[str]:
    """Detect actual source file changes via git diff.

    Excludes pipeline-managed paths (agent/, eval/baseline.json, tmp/)
    so that only implementer-created changes are detected.
    """
    r = subprocess.run(
        ["git", "diff", "--name-only"],
        capture_output=True, text=True, cwd=Path.cwd(),
    )
    if r.returncode != 0:
        return []
    files = [f.strip() for f in r.stdout.strip().split("\n") if f.strip()]
    return [f for f in files if not any(ex in f for ex in _GIT_DIFF_EXCLUDE)]


def run_implementer(config, hypothesis: str, plan: PlannerResult | None = None) -> ImplementerResult:
    """Apply code changes for the selected hypothesis.

    Calls the configured LLM CLI (Claude or Codex) via OAuth login.
    Verifies changes via git diff. Falls back to explicit SKIPPED status
    if CLI is unavailable (no silent placeholder).
    """
    config.tmp_path.mkdir(parents=True, exist_ok=True)
    provider = getattr(config, "llm_provider", "claude")

    # Load context for prompt
    context = load_agent_context(config)
    prompt = _build_implementer_prompt(context, hypothesis, plan)

    # Call LLM CLI (Claude or Codex, both via OAuth)
    cli_result = _call_llm_cli(
        prompt, config=config, provider=provider,
        timeout=getattr(config, "llm_timeout", 300),
        max_turns=getattr(config, "llm_max_turns", 3),
    )

    if cli_result and "changed_files" in cli_result:
        # CLI returned a result --verify actual changes via git
        reported_files = cli_result.get("changed_files", [])
        actual_files = _detect_git_changes() if config.use_git else reported_files
        forbidden_touched = [f for f in actual_files if f in FORBIDDEN_PATHS]

        notes = cli_result.get("notes", [])
        if config.use_git and set(reported_files) != set(actual_files):
            notes.append(
                f"git diff mismatch: CLI reported {reported_files}, "
                f"actual changes: {actual_files or '(none)'}"
            )

        result = ImplementerResult(
            changed_files=actual_files if actual_files else reported_files,
            change_summary=cli_result.get("change_summary", ""),
            why_this_change=cli_result.get("why_this_change", ""),
            notes=notes,
            verification_commands_run=cli_result.get("verification_commands_run", []),
            scope_respected=not forbidden_touched,
            forbidden_paths_touched=forbidden_touched,
            estimated_risk=cli_result.get("estimated_risk", "medium"),
        )
    else:
        # CLI unavailable or failed --report honestly (no silent placeholder)
        install_hints = {
            "claude": [
                "Claude Code CLI is required. Install and login:",
                "  npm install -g @anthropic-ai/claude-code",
                "  claude auth login",
            ],
            "codex": [
                "OpenAI Codex CLI is required. Install and login:",
                "  npm install -g @openai/codex",
                "  codex login",
            ],
        }
        result = ImplementerResult(
            changed_files=[],
            change_summary=f"SKIPPED: {provider} CLI not available or returned invalid response",
            why_this_change=f"hypothesis {hypothesis}",
            notes=install_hints.get(provider, [f"Install {provider} CLI and authenticate via OAuth."]),
            scope_respected=True,
            forbidden_paths_touched=[],
            estimated_risk="high",
            is_placeholder=True,
        )

    _save_implementer_result(config, result)
    return result


def _save_implementer_result(config, result: ImplementerResult) -> None:
    """Persist implementer result to tmp/."""
    config.tmp_path.mkdir(parents=True, exist_ok=True)
    (config.tmp_path / "implementer_result.json").write_text(
        json.dumps({
            "changed_files": result.changed_files,
            "change_summary": result.change_summary,
            "why_this_change": result.why_this_change,
            "notes": result.notes,
            "verification_commands_run": result.verification_commands_run,
            "scope_respected": result.scope_respected,
            "forbidden_paths_touched": result.forbidden_paths_touched,
            "estimated_risk": result.estimated_risk,
            "is_placeholder": result.is_placeholder,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

SUBPROCESS_TIMEOUT = 300  # 5 minutes default


def run_tests(config) -> TestsResult:
    """Execute pytest and return structured result."""
    import time

    start = time.time()
    try:
        r = subprocess.run(
            ["pytest", str(config.tests_path), "-v"],
            capture_output=True, text=True, cwd=Path.cwd(),
            timeout=SUBPROCESS_TIMEOUT,
        )
    except FileNotFoundError:
        r = subprocess.run(
            [sys.executable, "-m", "pytest", str(config.tests_path), "-v"],
            capture_output=True, text=True, cwd=Path.cwd(),
            timeout=SUBPROCESS_TIMEOUT,
        )
    elapsed = round(time.time() - start, 3)

    passed = r.returncode == 0
    total = sum(1 for line in r.stdout.split("\n") if "PASSED" in line or "FAILED" in line)
    failed_tests = [
        line.strip() for line in r.stdout.split("\n")
        if "FAILED" in line
    ]

    result = TestsResult(
        passed=passed,
        summary=r.stdout[-4000:] if r.stdout else ("tests passed" if passed else "tests failed"),
        failed_tests=failed_tests,
        duration_sec=elapsed,
        stderr=r.stderr[-4000:] if r.stderr else "",
        total=total,
    )
    config.tmp_path.mkdir(parents=True, exist_ok=True)
    (config.tmp_path / "tests_result.json").write_text(
        json.dumps({
            "passed": result.passed,
            "summary": result.summary,
            "failed_tests": result.failed_tests,
            "duration_sec": result.duration_sec,
            "stderr": result.stderr,
            "total": result.total,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return result


# ---------------------------------------------------------------------------
# Eval runner
# ---------------------------------------------------------------------------

def run_eval(config) -> EvalResult:
    """Execute frozen_eval.py, run constraints check, and return structured result."""
    from eval.constraints import check_constraints

    # 1. Run frozen eval
    r = subprocess.run(
        [sys.executable, str(config.frozen_eval_path)],
        capture_output=True, text=True, cwd=Path.cwd(),
        timeout=SUBPROCESS_TIMEOUT,
    )
    if r.returncode != 0:
        raise RuntimeError(f"Eval failed: {r.stderr}")

    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Eval returned invalid JSON: {e}\nstdout: {r.stdout[:500]}")

    # 2. Run constraints check (overrides frozen_eval's hardcoded values)
    constraints = check_constraints(eval_output=data)
    data["constraints_ok"] = constraints["constraints_ok"]
    data["latency_ms"] = constraints["latency_ms"]
    data["latency_delta_pct"] = constraints["latency_delta_pct"]
    if constraints.get("violations"):
        data.setdefault("notes", []).extend(constraints["violations"])

    config.tmp_path.mkdir(parents=True, exist_ok=True)
    (config.tmp_path / "eval_result.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8",
    )
    return EvalResult(
        score=data["score"],
        tests_pass=data.get("tests_pass", True),
        constraints_ok=data["constraints_ok"],
        latency_ms=data.get("latency_ms"),
        latency_delta_pct=data.get("latency_delta_pct"),
        regressions=data.get("regressions", []),
        notes=data.get("notes", []),
        details=data,
    )


# ---------------------------------------------------------------------------
# Critic agent
# ---------------------------------------------------------------------------

def run_critic(
    config,
    plan: PlannerResult | None,
    impl_result: ImplementerResult,
    test_result: TestsResult,
    eval_result: EvalResult,
    baseline_score: float,
) -> CriticResult:
    """Analyze changes for false wins, regressions, and overfitting.

    Current implementation uses rule-based heuristics.
    Integration with Codex CLI will replace this with LLM-based critique.
    """
    config.tmp_path.mkdir(parents=True, exist_ok=True)
    severity = "low"
    objections: list[str] = []
    recommendation = "accept"
    reasoning_parts: list[str] = []

    score_delta = eval_result.score - baseline_score

    # Check 1: Narrow win detection (single-fixture improvement)
    if 0 < score_delta < 0.1:
        objections.append("Very small score improvement --potential narrow win")
        reasoning_parts.append(f"Score delta {score_delta:.4f} is marginal")
        severity = "medium"

    # Check 2: Scope violation
    if not impl_result.scope_respected:
        objections.append("Implementation exceeded planned scope")
        severity = "high"
        recommendation = "reject"

    # Check 3: Forbidden paths touched
    if impl_result.forbidden_paths_touched:
        objections.append(f"Forbidden paths touched: {impl_result.forbidden_paths_touched}")
        severity = "high"
        recommendation = "reject"

    # Check 4: Too many files changed
    if len(impl_result.changed_files) > 5:
        objections.append(f"Too many files changed: {len(impl_result.changed_files)}")
        severity = "medium" if severity != "high" else severity

    # Check 5: High risk assessment from implementer
    if impl_result.estimated_risk == "high":
        objections.append("Implementer self-assessed high risk")
        severity = "medium" if severity != "high" else severity

    # Check 6: Latency regression
    if eval_result.latency_delta_pct is not None and eval_result.latency_delta_pct > 5.0:
        objections.append(f"Latency increased by {eval_result.latency_delta_pct:.1f}%")
        severity = "high"
        recommendation = "reject"

    # Check 7: Regressions detected by eval
    if eval_result.regressions:
        objections.append(f"Regressions detected: {eval_result.regressions}")
        severity = "high"
        recommendation = "reject"

    # Check 8: Tests failed but score improved (suspicious)
    if not test_result.passed and eval_result.score > baseline_score:
        objections.append("Score improved but tests failed --suspicious pattern")
        severity = "high"
        recommendation = "reject"

    # Determine final recommendation
    if severity == "low" and not objections:
        recommendation = "accept"
        reasoning_parts.append("No concerns found")
    elif severity == "medium" and recommendation != "reject":
        recommendation = "accept_with_monitoring"
        reasoning_parts.append("Minor concerns noted --monitor in next iterations")

    reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Critic review complete"

    result = CriticResult(
        severity=severity,
        objections=objections,
        recommendation=recommendation,
        reasoning=reasoning,
    )
    (config.tmp_path / "critic_result.json").write_text(
        json.dumps({
            "severity": result.severity,
            "objections": result.objections,
            "recommendation": result.recommendation,
            "reasoning": result.reasoning,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return result


# ---------------------------------------------------------------------------
# Forbidden path / change budget checks
# ---------------------------------------------------------------------------

FORBIDDEN_PATHS = [
    "eval/frozen_eval.py",
    "eval/fixtures.json",
    "eval/baseline.json",
    "agent/RESULTS.tsv",
    "agent/DECISIONS.md",
]


def check_forbidden_changes() -> tuple[bool, list[str]]:
    """Check if any forbidden files were modified via git status."""
    r = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True,
    )
    touched = []
    for line in r.stdout.split("\n"):
        if not line:
            continue
        filepath = line[3:].strip()
        for forbidden in FORBIDDEN_PATHS:
            if filepath == forbidden or filepath.endswith(forbidden):
                touched.append(filepath)
    return len(touched) == 0, touched


def check_change_budget(max_files: int = 5, max_lines: int = 200) -> tuple[bool, dict]:
    """Check if changes are within acceptable budget via git diff."""
    r = subprocess.run(
        ["git", "diff", "--stat", "HEAD"],
        capture_output=True, text=True,
    )
    if not r.stdout:
        return True, {"within_budget": True, "changed_files": 0, "diff_lines": 0}

    changed_files = 0
    total_lines = 0
    for line in r.stdout.split("\n"):
        if not line or line.startswith(" "):
            continue
        parts = line.split("|")
        if len(parts) >= 2:
            changed_files += 1
            line_info = parts[-1].strip()
            if line_info:
                numbers = line_info.split()
                if numbers:
                    try:
                        total_lines += int(numbers[0])
                    except ValueError:
                        pass

    within = changed_files <= max_files and total_lines <= max_lines
    return within, {
        "within_budget": within,
        "changed_files": changed_files,
        "diff_lines": total_lines,
        "max_files": max_files,
        "max_diff_lines": max_lines,
    }


# ---------------------------------------------------------------------------
# Decision Engine --9-level priority chain (doc 08-decision-engine)
# ---------------------------------------------------------------------------

def run_controller(
    config,
    score_before: float,
    eval_result: EvalResult,
    test_result: TestsResult,
    impl_result: ImplementerResult | None = None,
    critic_result: CriticResult | None = None,
) -> ControllerResult:
    """10-level decision engine.

    Priority order:
    0. No actual code change (placeholder/empty diff) → REJECT (NO_CODE_CHANGE)
    1. Tests fail → REJECT (TEST_FAIL)
    2. Constraints fail → REJECT (CONSTRAINT_FAIL)
    3. Forbidden files touched → REJECT (FORBIDDEN_FILE)
    4. Scope violation → REJECT (SCOPE_VIOLATION)
    5. Critic high severity → REJECT or HOLD (CRITIC_BLOCK)
    6. Score regression → REJECT (SCORE_REGRESSION)
    7. No improvement → REJECT (NO_IMPROVEMENT)
    8. All checks pass → ACCEPT
    """
    score_after = eval_result.score
    delta = round(score_after - score_before, 6)
    decision = Decision.REJECT
    code = DecisionCode.NO_IMPROVEMENT
    reason = ""
    next_action = "rollback_and_continue"
    critic_sev = "low"
    critic_rec = "accept"

    if critic_result:
        critic_sev = critic_result.severity
        critic_rec = critic_result.recommendation

    if impl_result is None:
        impl_result = ImplementerResult([], "", "", [])

    # Level 0: No actual code change
    if impl_result.is_placeholder or not impl_result.changed_files:
        code = DecisionCode.NO_CODE_CHANGE
        reason = "No actual code changes were made"
        if impl_result.is_placeholder:
            reason += " (implementer returned placeholder)"
        next_action = "rollback_and_continue"

    # Level 1: Tests
    elif not test_result.passed:
        code = DecisionCode.TEST_FAIL
        reason = f"Tests failed: {len(test_result.failed_tests)} failure(s)"
        next_action = "rollback_and_continue"

    # Level 2: Constraints
    elif not eval_result.constraints_ok:
        code = DecisionCode.CONSTRAINT_FAIL
        reason = "Constraint check failed"
        next_action = "rollback_and_continue"

    # Level 3: Forbidden files
    elif impl_result.forbidden_paths_touched:
        code = DecisionCode.FORBIDDEN_FILE
        reason = f"Forbidden files touched: {impl_result.forbidden_paths_touched}"
        next_action = "rollback_and_continue"

    # Level 4: Scope violation
    elif not impl_result.scope_respected:
        code = DecisionCode.SCOPE_VIOLATION
        reason = "Implementation exceeded planned scope"
        next_action = "rollback_and_continue"

    # Level 5: Critic high severity
    elif critic_sev == "high" and critic_rec in ("reject", "hold"):
        code = DecisionCode.CRITIC_BLOCK
        if critic_rec == "hold":
            decision = Decision.HOLD
            reason = f"Critic flagged high severity --hold for review"
            next_action = "manual_review"
        else:
            reason = f"Critic blocked: {critic_result.reasoning if critic_result else 'high severity'}"
            next_action = "rollback_and_continue"

    # Level 6: Score regression
    elif score_after < score_before:
        code = DecisionCode.SCORE_REGRESSION
        reason = f"Score regressed: {score_before} -> {score_after} (delta: {delta})"
        next_action = "rollback_and_continue"

    # Level 7: No improvement
    elif score_after == score_before:
        code = DecisionCode.NO_IMPROVEMENT
        reason = f"No score improvement: {score_before} -> {score_after}"
        next_action = "rollback_and_continue"

    # Level 8: Accept
    else:
        decision = Decision.ACCEPT
        code = DecisionCode.ACCEPT
        reason = f"Score improved: {score_before} -> {score_after} (delta: +{delta})"
        next_action = "archive_and_continue"

    result = ControllerResult(
        decision=decision.value,
        decision_code=code.value,
        score_after=score_after,
        score_before=score_before,
        score_delta=delta,
        reason=reason,
        next_action=next_action,
        critic_severity=critic_sev,
        critic_recommendation=critic_rec,
    )
    config.tmp_path.mkdir(parents=True, exist_ok=True)
    (config.tmp_path / "controller_result.json").write_text(
        json.dumps({
            "decision": result.decision,
            "decision_code": result.decision_code,
            "score_before": result.score_before,
            "score_after": result.score_after,
            "score_delta": result.score_delta,
            "reason": result.reason,
            "next_action": result.next_action,
            "critic_severity": result.critic_severity,
            "critic_recommendation": result.critic_recommendation,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return result


# ---------------------------------------------------------------------------
# Rollback
# ---------------------------------------------------------------------------

# Paths that must NOT be rolled back (pipeline state/logs).
# git restore would revert these to the last commit, destroying iteration state.
ROLLBACK_EXCLUDE_PATHS = [
    "agent/ITERATION_STATE.json",
    "agent/RESULTS.tsv",
    "agent/DECISIONS.md",
    "agent/MEMORY.md",
    "agent/HYPOTHESES.md",
    "eval/baseline.json",
    "tmp/",
]


def rollback_change(config) -> bool:
    """Rollback uncommitted source changes via git, preserving pipeline state.

    Excludes agent state files and eval/baseline.json from restore
    so that iteration records survive across rollbacks.
    """
    if not config.use_git:
        return True

    # Build exclude args: git restore . -- ':!path' ':!path2'
    exclude_args = [f":!{p}" for p in ROLLBACK_EXCLUDE_PATHS]

    r1 = subprocess.run(
        ["git", "restore", "--", "."] + exclude_args,
        capture_output=True, text=True, cwd=Path.cwd(),
    )
    # git clean: only remove untracked files in src/ and tests/, not agent/ or tmp/
    r2 = subprocess.run(
        ["git", "clean", "-fd", "--", "src/", "tests/"],
        capture_output=True, text=True, cwd=Path.cwd(),
    )
    success = r1.returncode == 0 and r2.returncode == 0
    if success:
        print("[rollback] Rolled back (agent state preserved)")
    else:
        print(f"[rollback] FAILED: restore={r1.returncode}, clean={r2.returncode}")
        if r1.stderr:
            print(f"[rollback] restore stderr: {r1.stderr.strip()}")
        if r2.stderr:
            print(f"[rollback] clean stderr: {r2.stderr.strip()}")
    return success
