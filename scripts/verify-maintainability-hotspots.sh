#!/usr/bin/env bash

set -euo pipefail

tool_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${tool_root}}"
threshold_doc="docs/maintainability-decomposition-thresholds.md"
baseline_file="docs/maintainability-hotspot-baseline.txt"

if ! git -C "${repo_root}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not a Git working tree: ${repo_root}" >&2
  exit 1
fi

if [[ ! -f "${repo_root}/${threshold_doc}" ]]; then
  echo "Missing maintainability decomposition threshold document: ${threshold_doc}" >&2
  exit 1
fi

if ! grep -Eq "^## .*How To Interpret Verifier Output" "${repo_root}/${threshold_doc}"; then
  echo "Maintainability threshold document must explain verifier output: ${threshold_doc}" >&2
  exit 1
fi

export AEGISOPS_REPO_ROOT="${repo_root}"
export AEGISOPS_MAINTAINABILITY_BASELINE="${baseline_file}"
export AEGISOPS_MAINTAINABILITY_DOC="${threshold_doc}"

python3 - <<'PY'
from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys

repo_root = pathlib.Path(os.environ["AEGISOPS_REPO_ROOT"])
baseline_path = repo_root / os.environ["AEGISOPS_MAINTAINABILITY_BASELINE"]
threshold_doc = os.environ["AEGISOPS_MAINTAINABILITY_DOC"]

minimum_effective_lines = int(os.environ.get("AEGISOPS_MAINTAINABILITY_MIN_EFFECTIVE_LINES", "900"))
minimum_signals = int(os.environ.get("AEGISOPS_MAINTAINABILITY_MIN_SIGNALS", "4"))

signal_patterns: dict[str, re.Pattern[str]] = {
    "runtime/auth boundary": re.compile(r"(auth|principal|runtime|boundary|tenant|scope)", re.I),
    "operator surface": re.compile(r"(operator|queue|detail|projection|inspect|summary|snapshot|status)", re.I),
    "casework mutation": re.compile(r"(case|triage|promot|lifecycle|transition|mutation)", re.I),
    "assistant/advisory assembly": re.compile(r"(assistant|advisory|recommendation|citation)", re.I),
    "action/reconciliation governance": re.compile(r"(action|approval|execution|reconciliation|delegat)", re.I),
    "readiness/restore/export": re.compile(r"(readiness|backup|restore|export|shutdown|startup)", re.I),
    "source/evidence admission": re.compile(r"(evidence|ingest|source|detector|alert|admission)", re.I),
}

required_boundary_signals = {
    "runtime/auth boundary",
    "operator surface",
    "action/reconciliation governance",
}


def tracked_python_files() -> list[str]:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repo_root),
            "ls-files",
            "--",
            "control-plane/aegisops_control_plane/*.py",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line.endswith(".py")]


def read_baseline() -> set[str]:
    if not baseline_path.exists():
        return set()

    entries: set[str] = set()
    for line in baseline_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        entries.add(stripped.split()[0])
    return entries


def effective_line_count(text: str) -> int:
    count = 0
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            count += 1
    return count


def candidate_for(relative_path: str) -> tuple[str, int, tuple[str, ...]] | None:
    path = repo_root / relative_path
    text = path.read_text(encoding="utf-8", errors="replace")
    facade_like = (
        pathlib.Path(relative_path).name == "service.py"
        or "facade" in relative_path.lower()
        or re.search(r"^class\s+\w*(Service|Facade)\b", text, re.M) is not None
    )
    if not facade_like:
        return None

    effective_lines = effective_line_count(text)
    present_signals = tuple(
        signal_name
        for signal_name, pattern in signal_patterns.items()
        if pattern.search(text)
    )

    if effective_lines < minimum_effective_lines:
        return None
    if len(present_signals) < minimum_signals:
        return None
    if not required_boundary_signals.intersection(present_signals):
        return None

    return (relative_path, effective_lines, present_signals)


baseline_entries = read_baseline()
candidates = [candidate for relative_path in tracked_python_files() if (candidate := candidate_for(relative_path))]
candidate_paths = {relative_path for relative_path, _, _ in candidates}

unknown_candidates = [candidate for candidate in candidates if candidate[0] not in baseline_entries]
stale_baseline_entries = sorted(baseline_entries - candidate_paths)

if unknown_candidates:
    print(
        "Maintainability hotspot candidates exceeded the reviewed baseline.",
        file=sys.stderr,
    )
    print(
        f"Review {threshold_doc} before extending these files or open a decomposition backlog.",
        file=sys.stderr,
    )
    for relative_path, effective_lines, signals in unknown_candidates:
        print(
            f"- {relative_path}: effective_lines={effective_lines}, signals={', '.join(signals)}",
            file=sys.stderr,
        )
    sys.exit(1)

if stale_baseline_entries:
    print(
        "Maintainability hotspot baseline contains entries that no longer match candidates.",
        file=sys.stderr,
    )
    for relative_path in stale_baseline_entries:
        print(f"- {relative_path}", file=sys.stderr)
    print(f"Update {baseline_path.relative_to(repo_root)} after confirming the hotspot was decomposed.", file=sys.stderr)
    sys.exit(1)

if candidates:
    print("Known maintainability hotspot baseline remains present:")
    for relative_path, effective_lines, signals in candidates:
        print(
            f"- {relative_path}: effective_lines={effective_lines}, signals={len(signals)}; see {threshold_doc}"
        )
else:
    print(f"No maintainability hotspot candidates found. See {threshold_doc}.")
PY
