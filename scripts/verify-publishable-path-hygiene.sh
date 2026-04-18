#!/usr/bin/env bash

set -euo pipefail

tool_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${tool_root}}"

if ! git -C "${repo_root}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not a Git working tree: ${repo_root}" >&2
  exit 1
fi

export AEGISOPS_TOOL_ROOT="${tool_root}"
export AEGISOPS_REPO_ROOT="${repo_root}"
export PYTHONPATH="${tool_root}/control-plane${PYTHONPATH:+:${PYTHONPATH}}"

python3 - <<'PY'
from __future__ import annotations

import os
import pathlib
import subprocess
import sys

from aegisops_control_plane.publishable_paths import ALLOWLIST_MARKER, is_workstation_local_path

repo_root = pathlib.Path(os.environ["AEGISOPS_REPO_ROOT"])

tracked_paths = subprocess.run(
    [
        "git",
        "-C",
        str(repo_root),
        "ls-files",
        "--",
        "README.md",
        ".github/workflows",
        "docs",
        "control-plane/tests",
    ],
    capture_output=True,
    text=True,
    check=True,
).stdout.splitlines()

offenders: list[tuple[str, int]] = []
for relative_path in tracked_paths:
    path = repo_root / relative_path
    if not path.is_file():
        continue

    raw_bytes = path.read_bytes()
    if b"\x00" in raw_bytes:
        continue

    text = raw_bytes.decode("utf-8", errors="replace")
    for line_number, line in enumerate(text.splitlines(), start=1):
        if ALLOWLIST_MARKER in line:
            continue
        if is_workstation_local_path(line):
            offenders.append((relative_path, line_number))

if offenders:
    print("Publishable docs and tests must not contain workstation-local absolute paths.", file=sys.stderr)
    for relative_path, line_number in offenders:
        print(
            f"{relative_path}:{line_number}: contains workstation-local absolute path",
            file=sys.stderr,
        )
    sys.exit(1)

print("Publishable docs and tests do not contain workstation-local absolute paths.")
PY
