#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"
export AEGISOPS_PREFLIGHT_REPO_ROOT="${repo_root}"

exec python3 - "$@" <<'PY'
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set


REPO_ROOT = Path(os.environ["AEGISOPS_PREFLIGHT_REPO_ROOT"])
DEFAULT_GRAPH = REPO_ROOT / "docs" / "automation" / "roadmap-materialization-phase-graph.json"
LINT_KEYS = (
    "execution_ready",
    "missing_required",
    "missing_recommended",
    "metadata_errors",
    "high_risk_blocking_ambiguity",
)
OWNER_ACCEPTANCE_RE = re.compile(r"(?m)^Explicit owner acceptance: yes$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preflight AegisOps roadmap phase materialization from a repo-local graph and GitHub issue facts."
    )
    parser.add_argument("--graph", default=str(DEFAULT_GRAPH), help="Repo-local roadmap phase graph JSON.")
    parser.add_argument("--target-phase", default="49.0", help="Later phase being gated, for example 49.0 or 49.")
    parser.add_argument(
        "--issue-source",
        choices=("auto", "graph", "github"),
        default="auto",
        help="Read issue facts from graph fixtures or live GitHub issue bodies.",
    )
    parser.add_argument("--repo", default="TommyKammy/AegisOps", help="GitHub repository for live issue reads.")
    parser.add_argument("--supervisor-root", default=os.environ.get("CODEX_SUPERVISOR_ROOT", ""))
    parser.add_argument("--supervisor-config", default=os.environ.get("CODEX_SUPERVISOR_CONFIG", ""))
    return parser.parse_args()


def emit(payload: dict, exit_code: int) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))
    raise SystemExit(exit_code)


def base_payload(graph: dict, target_phase: str, classifications: Optional[dict] = None) -> dict:
    return {
        "pass": False,
        "fail": True,
        "target_phase_id": target_phase,
        "phase_classification": classifications or {},
        "invalid_phase_id": None,
        "invalid_field": None,
        "invalid_issue_number": None,
        "suggested_next_safe_action": "repair the roadmap phase graph and rerun the preflight",
        "evidence": {
            "snapshot_id": graph.get("snapshot_id"),
            "phase_graph_source": graph.get("phase_graph_source"),
            "issue_numbers_read": [],
            "lint_command": "node <codex-supervisor-root>/dist/index.js issue-lint <issue-number> --config <supervisor-config-path>",
        },
    }


def fail(
    graph: dict,
    target_phase: str,
    classifications: dict,
    phase_id: str,
    classification: str,
    invalid_field: str,
    suggested: str,
    issue_number: Optional[int] = None,
    issue_numbers_read: Optional[List[int]] = None,
) -> None:
    updated = dict(classifications)
    if phase_id:
        updated[phase_id] = classification
    payload = base_payload(graph, target_phase, updated)
    payload["invalid_phase_id"] = phase_id or None
    payload["invalid_field"] = invalid_field
    payload["invalid_issue_number"] = issue_number
    payload["suggested_next_safe_action"] = suggested
    payload["evidence"]["issue_numbers_read"] = sorted(issue_numbers_read or [])
    emit(payload, 1)


def run_json(command: List[str], description: str) -> dict:
    try:
        completed = subprocess.run(command, check=True, text=True, capture_output=True)
    except FileNotFoundError:
        raise RuntimeError(f"{description} command is unavailable")
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        raise RuntimeError(f"{description} failed: {detail}")
    return json.loads(completed.stdout)


def run_lint(issue_number: int, supervisor_root: str, supervisor_config: str) -> dict:
    if not supervisor_root or not supervisor_config:
        raise RuntimeError("issue-lint requires CODEX_SUPERVISOR_ROOT and CODEX_SUPERVISOR_CONFIG or explicit arguments")
    command = [
        "node",
        str(Path(supervisor_root) / "dist" / "index.js"),
        "issue-lint",
        str(issue_number),
        "--config",
        supervisor_config,
    ]
    try:
        completed = subprocess.run(command, check=True, text=True, capture_output=True)
    except FileNotFoundError:
        raise RuntimeError("node is unavailable for issue-lint")
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        raise RuntimeError(f"issue-lint failed for #{issue_number}: {detail}")

    lint = {}
    for line in completed.stdout.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key in LINT_KEYS:
            lint[key] = value.strip()
    return lint


def normalize_number(value) -> Optional[int]:
    if isinstance(value, int) and value > 0:
        return value
    return None


def metadata_value(body: str, field: str) -> Optional[str]:
    match = re.search(rf"(?im)^\s*{re.escape(field)}\s*(?P<value>[^\n]+)", body or "")
    if not match:
        return None
    return match.group("value").strip()


def is_placeholder(value: Optional[str]) -> bool:
    if value is None:
        return True
    normalized = value.strip().lower()
    if not normalized:
        return True
    if any(token in normalized for token in ("tbd", "todo", "placeholder", "sample", "<", ">")):
        return True
    if normalized in {"n/a", "na", "unknown", "none yet"}:
        return True
    if re.search(r"#0+\b|#123\b|#999\b", normalized):
        return True
    return False


def dependency_numbers(value: str) -> List[int]:
    return [int(match) for match in re.findall(r"#([1-9][0-9]*)", value or "")]


def phase_done(phase: dict) -> bool:
    if phase.get("phase_status") == "explicitly_deferred":
        return True
    completion = str(phase.get("phase_completion_state", "")).lower()
    evaluation = str(phase.get("phase_evaluation_state", "")).lower()
    return completion in {"done", "closed", "complete", "completed", "merged", "evaluated"} and evaluation in {
        "done",
        "closed",
        "complete",
        "completed",
        "evaluated",
        "explicitly_deferred",
    }


def issue_closed_or_accepted(issue: dict) -> bool:
    state = str(issue.get("state", "")).lower()
    if state == "closed" or issue.get("explicitly_accepted") is True:
        return True
    return bool(OWNER_ACCEPTANCE_RE.search(issue.get("body") or ""))


def load_graph(path: str) -> dict:
    graph_path = Path(path)
    if not graph_path.is_file():
        emit(
            {
                "pass": False,
                "fail": True,
                "target_phase_id": None,
                "phase_classification": {},
                "invalid_field": "phase_graph",
                "invalid_issue_number": None,
                "suggested_next_safe_action": "provide a readable repo-local phase graph JSON file",
                "evidence": {"phase_graph_source": str(graph_path), "issue_numbers_read": []},
            },
            1,
        )
    return json.loads(graph_path.read_text(encoding="utf-8"))


def collect_predecessors(graph: dict, target_phase: str) -> List[dict]:
    phases = {str(phase.get("phase_id")): phase for phase in graph.get("phases", [])}
    target = phases.get(target_phase)
    if not target:
        fail(
            graph,
            target_phase,
            {},
            target_phase,
            "blocked",
            "phase_id",
            "add the requested target phase to the repo-local phase graph",
        )
    predecessor_ids = target.get("predecessor_phase_ids")
    if not isinstance(predecessor_ids, list) or not predecessor_ids:
        fail(
            graph,
            target_phase,
            {},
            target_phase,
            "blocked",
            "predecessor_phase_ids",
            "bind the target phase to explicit predecessor phases before scheduling",
        )
    predecessors = []
    classifications = {}
    for phase_id in predecessor_ids:
        phase = phases.get(str(phase_id))
        if not phase:
            fail(
                graph,
                target_phase,
                classifications,
                str(phase_id),
                "missing",
                "phase_id",
                "add the missing predecessor phase record to the phase graph",
            )
        predecessors.append(phase)
    return predecessors


def required_issue_numbers(predecessors: List[dict], graph: dict, target_phase: str) -> List[int]:
    numbers: List[int] = []
    classifications: Dict[str, str] = {}
    for phase in predecessors:
        phase_id = str(phase.get("phase_id"))
        if phase.get("phase_status") == "explicitly_deferred":
            continue
        epic = normalize_number(phase.get("epic_issue_number"))
        if epic is None:
            fail(
                graph,
                target_phase,
                classifications,
                phase_id,
                "missing",
                "epic_issue_number",
                "create or bind the missing Epic issue before scheduling dependent phases",
            )
        children = phase.get("child_issue_numbers")
        if not isinstance(children, list) or not children:
            fail(
                graph,
                target_phase,
                classifications,
                phase_id,
                "missing",
                "child_issue_numbers",
                "create or bind the missing child issue list before scheduling dependent phases",
                issue_number=epic,
            )
        numbers.append(epic)
        for child in children:
            number = normalize_number(child)
            if number is None:
                fail(
                    graph,
                    target_phase,
                    classifications,
                    phase_id,
                    "missing",
                    "child_issue_numbers",
                    "replace malformed child issue references with real GitHub issue numbers",
                )
            numbers.append(number)
    return sorted(set(numbers))


def load_issues(graph: dict, issue_numbers: List[int], source: str, repo: str, supervisor_root: str, supervisor_config: str) -> Dict[int, dict]:
    issue_fixtures = {int(issue["number"]): issue for issue in graph.get("issues", []) if normalize_number(issue.get("number"))}
    if source == "auto":
        source = "graph" if issue_fixtures else "github"

    loaded: Dict[int, dict] = {}
    for number in issue_numbers:
        if source == "graph":
            if number not in issue_fixtures:
                continue
            loaded[number] = dict(issue_fixtures[number])
            loaded[number].setdefault("lint", issue_fixtures[number].get("lint", {}))
            continue

        issue = run_json(
            ["gh", "issue", "view", str(number), "--repo", repo, "--json", "number,title,state,body"],
            f"GitHub issue read for #{number}",
        )
        issue["lint"] = run_lint(number, supervisor_root, supervisor_config)
        loaded[number] = issue
    return loaded


def lint_failure(issue: dict) -> Optional[str]:
    lint = issue.get("lint") or {}
    expected = {
        "execution_ready": "yes",
        "missing_required": "none",
        "missing_recommended": "none",
        "metadata_errors": "none",
        "high_risk_blocking_ambiguity": "none",
    }
    for key, value in expected.items():
        if lint.get(key) != value:
            return key
    return None


def validate_phase(
    phase: dict,
    graph: dict,
    target_phase: str,
    issues: Dict[int, dict],
    all_issue_numbers: Set[int],
    issue_numbers_read: List[int],
    classifications: dict,
) -> None:
    phase_id = str(phase.get("phase_id"))
    if phase.get("phase_status") == "explicitly_deferred":
        classifications[phase_id] = "done"
        return

    epic = normalize_number(phase.get("epic_issue_number"))
    children = [normalize_number(child) for child in phase.get("child_issue_numbers", [])]
    children = [child for child in children if child is not None]

    for number in [epic] + children:
        if number not in issues:
            fail(
                graph,
                target_phase,
                classifications,
                phase_id,
                "missing",
                "child_issue_numbers" if number != epic else "epic_issue_number",
                "create or bind the missing issue before scheduling dependent phases",
                issue_number=number,
                issue_numbers_read=issue_numbers_read,
            )

    for number in [epic] + children:
        issue = issues[number]
        state = str(issue.get("state", "")).lower()
        if not state or state == "unknown":
            fail(
                graph,
                target_phase,
                classifications,
                phase_id,
                "blocked",
                "issue_state",
                "refresh GitHub issue state from a trusted read before scheduling dependent phases",
                issue_number=number,
                issue_numbers_read=issue_numbers_read,
            )

        body = issue.get("body") or ""
        if number != epic:
            part_of = metadata_value(body, "Part of:")
            if is_placeholder(part_of) or int(epic) not in dependency_numbers(part_of):
                fail(
                    graph,
                    target_phase,
                    classifications,
                    phase_id,
                    "blocked",
                    "Part of:",
                    "replace the placeholder parent binding with the authoritative Epic issue number and rerun issue-lint",
                    issue_number=number,
                    issue_numbers_read=issue_numbers_read,
                )

        depends_on = metadata_value(body, "Depends on:")
        if is_placeholder(depends_on):
            fail(
                graph,
                target_phase,
                classifications,
                phase_id,
                "blocked",
                "Depends on:",
                "replace the placeholder dependency and rerun issue-lint",
                issue_number=number,
                issue_numbers_read=issue_numbers_read,
            )
        normalized_depends = depends_on.strip().lower()
        if normalized_depends != "none":
            deps = dependency_numbers(depends_on)
            if not deps or any(dep not in all_issue_numbers for dep in deps):
                fail(
                    graph,
                    target_phase,
                    classifications,
                    phase_id,
                    "blocked",
                    "Depends on:",
                    "bind dependencies to real issue numbers present in the authoritative phase graph",
                    issue_number=number,
                    issue_numbers_read=issue_numbers_read,
                )

        for field in ("Parallelizable:",):
            if is_placeholder(metadata_value(body, field)):
                fail(
                    graph,
                    target_phase,
                    classifications,
                    phase_id,
                    "blocked",
                    field,
                    f"add the required {field} metadata and rerun issue-lint",
                    issue_number=number,
                    issue_numbers_read=issue_numbers_read,
                )

        if not re.search(r"(?im)^\s*##\s*Execution order\b", body):
            fail(
                graph,
                target_phase,
                classifications,
                phase_id,
                "blocked",
                "Execution order",
                "add the required execution-order metadata and rerun issue-lint",
                issue_number=number,
                issue_numbers_read=issue_numbers_read,
            )

        lint_key = lint_failure(issue)
        if lint_key:
            fail(
                graph,
                target_phase,
                classifications,
                phase_id,
                "blocked",
                lint_key,
                "repair the issue body and rerun issue-lint",
                issue_number=number,
                issue_numbers_read=issue_numbers_read,
            )

        if not issue_closed_or_accepted(issue):
            fail(
                graph,
                target_phase,
                classifications,
                phase_id,
                "materialized_open",
                "issue_state",
                "close or explicitly accept every predecessor Epic and child issue before dependent scheduling",
                issue_number=number,
                issue_numbers_read=issue_numbers_read,
            )

    if phase_done(phase):
        classifications[phase_id] = "done"
    elif str(phase.get("phase_completion_state", "")).lower() in {"done", "closed", "complete", "completed", "merged"}:
        classifications[phase_id] = "merge_or_evaluation_needed"
        fail(
            graph,
            target_phase,
            classifications,
            phase_id,
            "merge_or_evaluation_needed",
            "phase_evaluation_state",
            "record evaluation closure or explicit deferral before dependent scheduling",
            issue_numbers_read=issue_numbers_read,
        )
    else:
        classifications[phase_id] = "materialized_open"
        fail(
            graph,
            target_phase,
            classifications,
            phase_id,
            "materialized_open",
            "phase_completion_state",
            "complete and evaluate the materialized predecessor phase before dependent scheduling",
            issue_numbers_read=issue_numbers_read,
        )


def main() -> None:
    args = parse_args()
    graph = load_graph(args.graph)
    predecessors = collect_predecessors(graph, args.target_phase)
    numbers = required_issue_numbers(predecessors, graph, args.target_phase)
    try:
        issues = load_issues(graph, numbers, args.issue_source, args.repo, args.supervisor_root, args.supervisor_config)
    except Exception as exc:
        phase_id = str(predecessors[0].get("phase_id")) if predecessors else args.target_phase
        fail(
            graph,
            args.target_phase,
            {},
            phase_id,
            "blocked",
            "issue-lint" if "issue-lint" in str(exc) else "issue_graph_read",
            str(exc),
        )

    classifications: Dict[str, str] = {}
    issue_numbers_read = sorted(issues)
    all_issue_numbers = set(numbers)
    for phase in predecessors:
        validate_phase(phase, graph, args.target_phase, issues, all_issue_numbers, issue_numbers_read, classifications)

    payload = base_payload(graph, args.target_phase, classifications)
    payload["pass"] = True
    payload["fail"] = False
    payload["invalid_field"] = None
    payload["suggested_next_safe_action"] = "evaluate next phase gate"
    payload["evidence"]["issue_numbers_read"] = issue_numbers_read
    emit(payload, 0)


if __name__ == "__main__":
    main()
PY
