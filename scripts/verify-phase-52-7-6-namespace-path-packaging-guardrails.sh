#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
control_plane_root="${repo_root}/control-plane"
canonical_root="${control_plane_root}/aegisops/control_plane"
legacy_root="${control_plane_root}/aegisops_control_plane"
doc_path="${repo_root}/docs/adr/0018-phase-52-7-6-namespace-path-packaging-guardrails.md"

for required_path in \
  "${doc_path}" \
  "${canonical_root}/__init__.py" \
  "${canonical_root}/service.py" \
  "${canonical_root}/models.py" \
  "${canonical_root}/core/legacy_import_aliases.py" \
  "${legacy_root}/__init__.py" \
  "${control_plane_root}/main.py"; do
  if [[ ! -f "${required_path}" ]]; then
    echo "Missing Phase 52.7.6 namespace/path packaging guardrail path: ${required_path#"${repo_root}/"}" >&2
    exit 1
  fi
done

required_phrases=(
  "# ADR-0018: Phase 52.7.6 Namespace, Path, And Packaging Guardrails"
  "Phase 52.7.4 moved implementation ownership to \`control-plane/aegisops/control_plane/\`."
  "Legacy compatibility package | \`control-plane/aegisops_control_plane/__init__.py\` only"
  "Canonical import namespace | \`aegisops.control_plane\`"
  "Packaging entrypoint | \`python3 control-plane/main.py\`"
  "Supervisor command guidance | \`node <codex-supervisor-root>/dist/index.js issue-lint 1126 --config <supervisor-config-path>\`"
  "New guidance that points implementation ownership at \`control-plane/aegisops_control_plane/\` is rejected unless the file is an approved compatibility note, compatibility verifier, or negative fixture."
  "\`bash scripts/verify-phase-52-7-6-namespace-path-packaging-guardrails.sh\`"
  "\`bash scripts/test-verify-phase-52-7-6-namespace-path-packaging-guardrails.sh\`"
)

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${doc_path}"; then
    echo "Missing Phase 52.7.6 guardrail statement: ${phrase}" >&2
    exit 1
  fi
done

path_token_boundary="(^|[[:space:]'\"\`(<{=])"
path_token_chars="[^[:space:]'\"\` )>}|]"
home_absolute_path="/(Users|home)/${path_token_chars}+"
windows_user_path="[A-Za-z]:[\\\\/]Users[\\\\/]${path_token_chars}*"
local_path_token="(${home_absolute_path}|${windows_user_path})"

if grep -Eq "(${path_token_boundary}${local_path_token}|file:///?${local_path_token})" \
  "${doc_path}" \
  "${repo_root}/scripts/verify-phase-52-7-6-namespace-path-packaging-guardrails.sh" \
  "${repo_root}/scripts/test-verify-phase-52-7-6-namespace-path-packaging-guardrails.sh"; then
  echo "Forbidden Phase 52.7.6 guardrail artifact: workstation-local absolute path detected" >&2
  exit 1
fi

export PHASE52_7_6_REPO_ROOT="${repo_root}"

python3 - <<'PY'
from __future__ import annotations

import os
from pathlib import Path
import re
import sys

repo_root = Path(os.environ["PHASE52_7_6_REPO_ROOT"]).resolve()
control_plane_root = repo_root / "control-plane"
canonical_root = control_plane_root / "aegisops" / "control_plane"
legacy_root = control_plane_root / "aegisops_control_plane"

retained_root_files = {
    "__init__.py",
    "cli.py",
    "config.py",
    "models.py",
    "operator_inspection.py",
    "persistence_lifecycle.py",
    "publishable_paths.py",
    "record_validation.py",
    "reviewed_slice_policy.py",
    "service.py",
    "service_composition.py",
    "structured_events.py",
}

legacy_root_files = sorted(path.name for path in legacy_root.glob("*.py"))
if legacy_root_files != ["__init__.py"]:
    print(
        "Phase 52.7.6 guardrail rejected legacy implementation files: "
        + ", ".join(legacy_root_files),
        file=sys.stderr,
    )
    sys.exit(1)

actual_root_files = sorted(path.name for path in canonical_root.glob("*.py"))
if actual_root_files != sorted(retained_root_files):
    print(
        "Phase 52.7.6 guardrail expected canonical root files "
        + ", ".join(sorted(retained_root_files))
        + "; found "
        + ", ".join(actual_root_files),
        file=sys.stderr,
    )
    sys.exit(1)

approved_legacy_path_text_files = {
    "docs/adr/0003-phase-49-service-decomposition-boundaries.md",
    "docs/adr/0004-phase-50-maintainability-hotspot-map-and-migration-order.md",
    "docs/adr/0005-phase-50-8-residual-service-hotspot-migration-contract.md",
    "docs/adr/0006-phase-50-9-residual-facade-convergence-and-projection-guard.md",
    "docs/adr/0007-phase-50-10-facade-floor-and-external-evidence-guard.md",
    "docs/adr/0008-phase-50-11-service-residual-extraction-contract.md",
    "docs/adr/0009-phase-50-12-service-facade-pressure-contract.md",
    "docs/adr/0010-phase-50-13-public-facade-api-inventory-and-compatibility-policy.md",
    "docs/adr/0012-phase-52-5-1-control-plane-layout-inventory-and-migration-contract.md",
    "docs/adr/0013-phase-52-5-2-package-scaffolding-and-compatibility-shim-policy.md",
    "docs/adr/0014-phase-52-6-1-root-shim-inventory-and-deprecation-contract.md",
    "docs/adr/0015-phase-52-6-3-legacy-import-alias-registry.md",
    "docs/adr/0016-phase-52-7-1-namespace-and-layout-inventory-contract.md",
    "docs/adr/0017-phase-52-7-2-canonical-namespace-bridge.md",
    "docs/adr/0018-phase-52-7-6-namespace-path-packaging-guardrails.md",
    "docs/phase-52-5-closeout-evaluation.md",
    "docs/phase-52-6-closeout-evaluation.md",
    "docs/control-plane-service-internal-boundaries.md",
    "docs/maintainability-decomposition-thresholds.md",
    "docs/phase-45-daily-soc-queue-and-operator-ux-hardening-boundary.md",
    "docs/phase-45-daily-soc-queue-and-operator-ux-hardening-validation.md",
    "docs/phase-47-control-plane-responsibility-decomposition-boundary.md",
    "docs/phase-47-control-plane-responsibility-decomposition-validation.md",
    "docs/phase-49-5-pilot-reporting-executive-summary-export-validation.md",
    "docs/phase-50-10-5-facade-method-rewiring.md",
    "docs/phase-50-maintainability-closeout.md",
    "scripts/test-verify-control-plane-runtime-skeleton.sh",
    "scripts/test-verify-maintainability-hotspots.sh",
    "scripts/test-verify-phase-9-control-plane-runtime-boundary-validation.sh",
    "scripts/test-verify-phase-50-8-residual-service-hotspot-contract.sh",
    "scripts/test-verify-phase-50-9-residual-facade-convergence-contract.sh",
    "scripts/test-verify-phase-50-10-facade-floor-external-evidence-contract.sh",
    "scripts/test-verify-phase-50-11-service-residual-extraction-contract.sh",
    "scripts/test-verify-phase-50-12-service-facade-pressure-contract.sh",
    "scripts/test-verify-phase-50-13-public-facade-inventory-contract.sh",
    "scripts/test-verify-phase-50-maintainability-adr.sh",
    "scripts/verify-control-plane-runtime-skeleton.sh",
    "scripts/verify-maintainability-hotspots.sh",
    "scripts/verify-phase-50-8-residual-service-hotspot-contract.sh",
    "scripts/verify-phase-50-9-residual-facade-convergence-contract.sh",
    "scripts/verify-phase-50-10-facade-floor-external-evidence-contract.sh",
    "scripts/verify-phase-50-11-service-residual-extraction-contract.sh",
    "scripts/verify-phase-50-12-service-facade-pressure-contract.sh",
    "scripts/verify-phase-50-13-public-facade-inventory-contract.sh",
    "scripts/verify-phase-50-maintainability-adr.sh",
    "scripts/verify-phase-52-5-1-control-plane-layout-inventory-contract.sh",
    "scripts/verify-phase-52-5-2-import-compatibility.sh",
    "scripts/verify-phase-52-5-2-layout-guardrail.sh",
    "scripts/verify-phase-52-5-2-package-scaffolding.sh",
    "scripts/verify-phase-52-6-1-root-shim-inventory-contract.sh",
    "scripts/verify-phase-52-6-2-canonical-domain-imports.sh",
    "scripts/verify-phase-52-6-3-legacy-import-alias-registry.sh",
    "scripts/verify-phase-52-6-5-retire-phase29-root-filenames.sh",
    "scripts/verify-phase-52-6-6-root-package-guardrails.sh",
    "scripts/verify-phase-52-7-1-namespace-layout-inventory-contract.sh",
    "scripts/verify-phase-52-7-2-canonical-namespace-bridge.sh",
    "scripts/verify-phase-52-7-3-repo-owned-canonical-namespace.sh",
    "scripts/verify-phase-52-7-4-physical-layout-migration.sh",
    "scripts/verify-phase-52-7-5-root-shim-reduction.sh",
    "scripts/verify-phase-52-7-6-namespace-path-packaging-guardrails.sh",
    "scripts/test-verify-phase-52-5-1-control-plane-layout-inventory-contract.sh",
    "scripts/test-verify-phase-52-5-2-package-scaffolding-and-shim-policy.sh",
    "scripts/test-verify-phase-52-6-1-root-shim-inventory-contract.sh",
    "scripts/test-verify-phase-52-6-2-canonical-domain-imports.sh",
    "scripts/test-verify-phase-52-6-3-legacy-import-alias-registry.sh",
    "scripts/test-verify-phase-52-6-5-retire-phase29-root-filenames.sh",
    "scripts/test-verify-phase-52-6-6-root-package-guardrails.sh",
    "scripts/test-verify-phase-52-7-1-namespace-layout-inventory-contract.sh",
    "scripts/test-verify-phase-52-7-2-canonical-namespace-bridge.sh",
    "scripts/test-verify-phase-52-7-3-repo-owned-canonical-namespace.sh",
    "scripts/test-verify-phase-52-7-4-physical-layout-migration.sh",
    "scripts/test-verify-phase-52-7-5-root-shim-reduction.sh",
    "scripts/test-verify-phase-52-7-6-namespace-path-packaging-guardrails.sh",
}

def rel(path: Path) -> str:
    return path.relative_to(repo_root).as_posix()


violations: list[str] = []
legacy_path_pattern = re.compile(r"control-plane/aegisops_control_plane/?")
for root_name, patterns in {
    "docs": ("*.md", "*.txt", "*.rst"),
    "scripts": ("*.sh",),
    ".github": ("*.yml", "*.yaml", "*.md"),
}.items():
    root = repo_root / root_name
    if not root.exists():
        continue
    for pattern in patterns:
        for path in root.rglob(pattern):
            relative = rel(path)
            if relative in approved_legacy_path_text_files:
                continue
            text = path.read_text(encoding="utf-8")
            for line_number, line in enumerate(text.splitlines(), start=1):
                if legacy_path_pattern.search(line):
                    violations.append(
                        f"{relative}:{line_number} points implementation guidance at control-plane/aegisops_control_plane/"
                    )

for extra in ("README.md", "package.json", "package-lock.json"):
    path = repo_root / extra
    if path.exists():
        text = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if legacy_path_pattern.search(line):
                violations.append(
                    f"{extra}:{line_number} points implementation guidance at control-plane/aegisops_control_plane/"
                )

if violations:
    print("Phase 52.7.6 namespace/path packaging guardrail found violations:", file=sys.stderr)
    for violation in violations:
        print(f"- {violation}", file=sys.stderr)
    sys.exit(1)

print(
    "Phase 52.7.6 namespace/path packaging guardrails passed: canonical implementation path, "
    "legacy shim boundary, retained root set, compatibility imports, and publishable guidance are pinned."
)
PY

for prerequisite in \
  "${repo_root}/scripts/verify-phase-52-7-3-repo-owned-canonical-namespace.sh" \
  "${repo_root}/scripts/verify-phase-52-7-5-root-shim-reduction.sh" \
  "${repo_root}/scripts/verify-phase-52-6-6-root-package-guardrails.sh" \
  "${repo_root}/scripts/verify-publishable-path-hygiene.sh" \
  "${repo_root}/scripts/verify-phase-52-5-2-import-compatibility.sh"; do
  if [[ ! -f "${prerequisite}" ]]; then
    echo "Missing Phase 52.7.6 prerequisite verifier: ${prerequisite#"${repo_root}/"}" >&2
    exit 1
  fi
  bash "${prerequisite}" "${repo_root}" >/dev/null
done
