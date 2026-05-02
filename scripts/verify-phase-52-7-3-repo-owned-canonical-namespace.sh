#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

export PHASE52_7_3_REPO_ROOT="${repo_root}"

python3 - <<'PY'
from __future__ import annotations

import ast
import os
from pathlib import Path
import re
import sys

repo_root = Path(os.environ["PHASE52_7_3_REPO_ROOT"]).resolve()

required_paths = (
    "control-plane/aegisops/__init__.py",
    "control-plane/aegisops/control_plane/__init__.py",
    "control-plane/aegisops_control_plane/__init__.py",
)
for required_path in required_paths:
    if not (repo_root / required_path).is_file():
        print(
            f"Missing Phase 52.7.3 namespace cleanup prerequisite: {required_path}",
            file=sys.stderr,
        )
        sys.exit(1)

approved_legacy_python_files = {
    "control-plane/aegisops/control_plane/__init__.py",
    "control-plane/aegisops_control_plane/__init__.py",
    "control-plane/aegisops_control_plane/core/legacy_import_aliases.py",
    "control-plane/tests/test_phase52_6_3_legacy_import_alias_registry.py",
    "control-plane/tests/test_phase52_6_4_root_shim_alias_removal.py",
    "control-plane/tests/test_phase52_6_5_phase29_root_filename_retirement.py",
    "control-plane/tests/test_phase52_7_2_canonical_namespace_bridge.py",
}

approved_legacy_text_files = {
    "docs/adr/0014-phase-52-6-1-root-shim-inventory-and-deprecation-contract.md",
    "docs/adr/0015-phase-52-6-3-legacy-import-alias-registry.md",
    "docs/adr/0017-phase-52-7-2-canonical-namespace-bridge.md",
    "docs/phase-52-6-closeout-evaluation.md",
    "scripts/verify-phase-52-5-2-import-compatibility.sh",
    "scripts/verify-phase-52-6-1-root-shim-inventory-contract.sh",
    "scripts/verify-phase-52-6-3-legacy-import-alias-registry.sh",
    "scripts/verify-phase-52-6-5-retire-phase29-root-filenames.sh",
    "scripts/verify-phase-52-7-2-canonical-namespace-bridge.sh",
    "scripts/test-verify-phase-52-5-2-package-scaffolding-and-shim-policy.sh",
    "scripts/test-verify-phase-52-6-1-root-shim-inventory-contract.sh",
    "scripts/test-verify-phase-52-6-2-canonical-domain-imports.sh",
    "scripts/test-verify-phase-52-6-3-legacy-import-alias-registry.sh",
    "scripts/test-verify-phase-52-6-5-retire-phase29-root-filenames.sh",
    "scripts/test-verify-phase-52-7-2-canonical-namespace-bridge.sh",
} | approved_legacy_python_files

legacy_import_pattern = re.compile(r"\baegisops_control_plane(?:\.|\b)")


def relative(path: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def python_candidates() -> list[Path]:
    roots = [
        repo_root / "control-plane",
        repo_root / "scripts",
    ]
    paths: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        paths.extend(root.rglob("*.py"))
    return sorted(set(paths))


def text_candidates() -> list[Path]:
    paths: list[Path] = []
    for root_name, patterns in {
        ".github": ("*.yml", "*.yaml", "*.md"),
    }.items():
        root = repo_root / root_name
        if not root.exists():
            continue
        for pattern in patterns:
            paths.extend(root.rglob(pattern))
    for extra in ("README.md", "package.json", "package-lock.json"):
        path = repo_root / extra
        if path.exists():
            paths.append(path)
    return sorted(set(paths))


violations: list[str] = []
for path in python_candidates():
    rel = relative(path)
    text = path.read_text(encoding="utf-8")
    if rel in approved_legacy_python_files:
        continue
    try:
        tree = ast.parse(text, filename=rel)
    except SyntaxError as exc:
        print(f"Could not parse {rel}: {exc}", file=sys.stderr)
        sys.exit(1)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "aegisops_control_plane" or alias.name.startswith(
                    "aegisops_control_plane."
                ):
                    violations.append(
                        f"{rel}:{node.lineno} imports {alias.name}; use aegisops.control_plane"
                    )
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            if node.module == "aegisops_control_plane" or (
                node.module is not None
                and node.module.startswith("aegisops_control_plane.")
            ):
                replacement = "aegisops.control_plane" + node.module.removeprefix(
                    "aegisops_control_plane"
                )
                violations.append(
                    f"{rel}:{node.lineno} imports {node.module}; use {replacement}"
                )

for path in text_candidates():
    rel = relative(path)
    text = path.read_text(encoding="utf-8")
    if not legacy_import_pattern.search(text) or rel in approved_legacy_text_files:
        continue
    for line_number, line in enumerate(text.splitlines(), start=1):
        if legacy_import_pattern.search(line):
            violations.append(
                f"{rel}:{line_number} mentions aegisops_control_plane; use aegisops.control_plane or document an approved compatibility exception"
            )

if violations:
    print(
        "Phase 52.7.3 repo-owned canonical namespace verifier found non-approved legacy references:",
        file=sys.stderr,
    )
    for violation in violations:
        print(f"- {violation}", file=sys.stderr)
    sys.exit(1)

print(
    "Phase 52.7.3 repo-owned canonical namespace verifier passed: repo-owned references use aegisops.control_plane except approved compatibility surfaces."
)
PY
