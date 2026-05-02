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
import ast
from typing import Mapping

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
            ":(glob)control-plane/aegisops/control_plane/**/*.py",
            ":(glob)control-plane/aegisops_control_plane/**/*.py",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    paths = {
        line
        for line in result.stdout.splitlines()
        if line.endswith(".py") and (repo_root / line).is_file()
    }
    canonical_root = repo_root / "control-plane" / "aegisops" / "control_plane"
    if canonical_root.exists():
        paths.update(
            path.relative_to(repo_root).as_posix()
            for path in canonical_root.rglob("*.py")
        )
    return sorted(paths)


def read_baseline() -> dict[str, dict[str, str]]:
    if not baseline_path.exists():
        return {}

    entries: dict[str, dict[str, str]] = {}
    for line in baseline_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        metadata: dict[str, str] = {}
        for part in parts[1:]:
            if "=" not in part:
                continue
            key, value = part.split("=", 1)
            if key:
                metadata[key] = value
        entries[parts[0]] = metadata
    return entries


def physical_line_count(text: str) -> int:
    return len(text.splitlines())


def effective_line_count(text: str) -> int:
    """Return maintained non-comment lines; docstrings intentionally count."""
    count = 0
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            count += 1
    return count


def read_python_file(relative_path: str) -> str:
    return (repo_root / relative_path).read_text(encoding="utf-8", errors="replace")


def class_method_count(text: str, class_name: str) -> int | None:
    tree = ast.parse(text)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return sum(
                1
                for child in node.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            )
    return None


def detected_facade_class(text: str) -> str | None:
    tree = ast.parse(text)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and re.search(r"(Service|Facade)$", node.name):
            return node.name
    return None


def candidate_for(
    relative_path: str,
) -> tuple[str, int, int, str | None, int | None, tuple[str, ...]] | None:
    text = read_python_file(relative_path)
    facade_class = detected_facade_class(text)
    facade_like = (
        pathlib.Path(relative_path).name == "service.py"
        or "facade" in relative_path.lower()
        or facade_class is not None
    )
    if not facade_like:
        return None

    physical_lines = physical_line_count(text)
    effective_lines = effective_line_count(text)
    facade_method_count = (
        class_method_count(text, facade_class) if facade_class is not None else None
    )
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

    return (
        relative_path,
        physical_lines,
        effective_lines,
        facade_class,
        facade_method_count,
        present_signals,
    )


def integer_metadata(
    metadata: Mapping[str, str],
    key: str,
    relative_path: str,
) -> int | None:
    value = metadata.get(key)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        print(
            f"Maintainability baseline entry for {relative_path} has invalid {key}={value!r}.",
            file=sys.stderr,
        )
        sys.exit(1)


baseline_entries = read_baseline()
candidates = [candidate for relative_path in tracked_python_files() if (candidate := candidate_for(relative_path))]
candidate_paths = {relative_path for relative_path, _, _, _, _, _ in candidates}

unknown_candidates = [candidate for candidate in candidates if candidate[0] not in baseline_entries]
stale_baseline_entries = sorted(set(baseline_entries) - candidate_paths)
baseline_regressions: list[str] = []

for relative_path, physical_lines, effective_lines, facade_class, facade_method_count, _signals in candidates:
    metadata = baseline_entries.get(relative_path, {})
    max_lines = integer_metadata(metadata, "max_lines", relative_path)
    max_effective_lines = integer_metadata(
        metadata,
        "max_effective_lines",
        relative_path,
    )
    max_facade_methods = integer_metadata(
        metadata,
        "max_facade_methods",
        relative_path,
    )
    configured_facade_class = metadata.get("facade_class") or facade_class
    configured_facade_method_count = (
        class_method_count(read_python_file(relative_path), configured_facade_class)
        if configured_facade_class is not None
        else None
    )

    if max_lines is not None and physical_lines > max_lines:
        baseline_regressions.append(
            f"{relative_path}: lines={physical_lines} exceeds max_lines={max_lines}"
        )
    if max_effective_lines is not None and effective_lines > max_effective_lines:
        baseline_regressions.append(
            f"{relative_path}: effective_lines={effective_lines} exceeds max_effective_lines={max_effective_lines}"
        )
    if (
        max_facade_methods is not None
        and configured_facade_class is None
    ):
        baseline_regressions.append(
            f"{relative_path}: facade_class is required for max_facade_methods={max_facade_methods}"
        )
    if (
        max_facade_methods is not None
        and configured_facade_class is not None
        and configured_facade_method_count is None
    ):
        baseline_regressions.append(
            f"{relative_path}: facade_class={configured_facade_class} not found for max_facade_methods={max_facade_methods}"
        )
    if (
        max_facade_methods is not None
        and configured_facade_method_count is not None
        and configured_facade_method_count > max_facade_methods
    ):
        baseline_regressions.append(
            f"{relative_path}: {configured_facade_class} methods={configured_facade_method_count} exceeds max_facade_methods={max_facade_methods}"
        )

if unknown_candidates:
    print(
        "Maintainability hotspot candidates exceeded the reviewed baseline.",
        file=sys.stderr,
    )
    print(
        f"Review {threshold_doc} before extending these files or open a decomposition backlog.",
        file=sys.stderr,
    )
    for relative_path, physical_lines, effective_lines, facade_class, facade_method_count, signals in unknown_candidates:
        method_summary = (
            f", {facade_class} methods={facade_method_count}"
            if facade_class is not None and facade_method_count is not None
            else ""
        )
        print(
            f"- {relative_path}: lines={physical_lines}, effective_lines={effective_lines}{method_summary}, signals={', '.join(signals)}",
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

if baseline_regressions:
    print(
        "Maintainability hotspot baseline limits were exceeded.",
        file=sys.stderr,
    )
    print(
        "Open or update a decomposition decision before allowing facade hotspot growth.",
        file=sys.stderr,
    )
    for regression in baseline_regressions:
        print(f"- {regression}", file=sys.stderr)
    sys.exit(1)

if candidates:
    print("Known maintainability hotspot baseline remains present:")
    for relative_path, physical_lines, effective_lines, facade_class, facade_method_count, signals in candidates:
        method_summary = (
            f", {facade_class} methods={facade_method_count}"
            if facade_class is not None and facade_method_count is not None
            else ""
        )
        print(
            f"- {relative_path}: lines={physical_lines}, effective_lines={effective_lines}{method_summary}, signals={len(signals)}; see {threshold_doc}"
        )
else:
    print(f"No maintainability hotspot candidates found. See {threshold_doc}.")
PY
