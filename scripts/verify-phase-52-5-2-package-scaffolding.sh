#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/adr/0013-phase-52-5-2-package-scaffolding-and-compatibility-shim-policy.md"
package_root="${repo_root}/control-plane/aegisops_control_plane"

required_packages=(
  "core"
  "api"
  "runtime"
  "ingestion"
  "actions"
  "actions/review"
  "evidence"
  "assistant"
  "ml_shadow"
  "reporting"
)

required_doc_phrases=(
  "# ADR-0013: Phase 52.5.2 Package Scaffolding and Compatibility-Shim Policy"
  "- **Status**: Accepted"
  "- **Date**: 2026-05-01"
  "- **Related Issues**: #1084, #1086"
  "- **Depends On**: #1085"
  'The scaffolds are package markers only; they do not move production modules, rename `aegisops_control_plane`, or rename the outer `control-plane/` directory.'
  "Legacy imports remain the stable public compatibility surface until a later child issue documents caller evidence, replacement imports, deprecation window, focused regression tests, and rollback path."
  "Compatibility shims may re-export from a new owner after a module move, but they must stay narrow and cannot introduce runtime behavior, durable-state side effects, or authority-boundary changes."
  "When caller evidence is missing, malformed, ambiguous, or only inferred from path shape, the legacy import path stays available."
  'The initial import compatibility verifier covers `aegisops_control_plane.service:AegisOpsControlPlaneService` and `aegisops_control_plane.models:AlertRecord` as stable legacy imports.'
  "The layout guardrail skeleton rejects new flat root-level Python modules unless the Phase 52.5.1 inventory or the Phase 52.5.2 approved scaffold package set classifies them."
  'Run `bash scripts/verify-phase-52-5-2-package-scaffolding.sh`.'
  'Run `bash scripts/verify-phase-52-5-2-import-compatibility.sh`.'
  'Run `bash scripts/verify-phase-52-5-2-layout-guardrail.sh`.'
  'Run `bash scripts/verify-phase-52-5-1-control-plane-layout-inventory-contract.sh`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1086 --config <supervisor-config-path>`.'
)

if [[ ! -d "${package_root}" ]]; then
  echo "Missing control-plane package root: ${package_root}" >&2
  exit 1
fi

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Phase 52.5.2 package scaffolding policy: ${doc_path}" >&2
  exit 1
fi

for package in "${required_packages[@]}"; do
  package_path="${package_root}/${package}"
  init_path="${package_path}/__init__.py"
  if [[ ! -d "${package_path}" ]]; then
    echo "Missing Phase 52.5.2 target package scaffold: control-plane/aegisops_control_plane/${package}" >&2
    exit 1
  fi
  if [[ ! -f "${init_path}" ]]; then
    echo "Missing Phase 52.5.2 target package marker: control-plane/aegisops_control_plane/${package}/__init__.py" >&2
    exit 1
  fi
  if [[ -s "${init_path}" ]] && ! grep -Fq "Package scaffold only" "${init_path}"; then
    echo "Phase 52.5.2 package marker must state scaffold-only posture: control-plane/aegisops_control_plane/${package}/__init__.py" >&2
    exit 1
  fi
done

for phrase in "${required_doc_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${doc_path}"; then
    echo "Missing Phase 52.5.2 package scaffolding policy statement: ${phrase}" >&2
    exit 1
  fi
done

path_token_boundary="(^|[[:space:]'\"\`(<{=])"
path_token_chars="[^[:space:]'\"\` )>}|]"
home_absolute_path="/(Users|home)/${path_token_chars}+"
windows_user_path="[A-Za-z]:[\\\\/]Users[\\\\/]${path_token_chars}*"
local_path_token="(${home_absolute_path}|${windows_user_path})"

if grep -Eq "(${path_token_boundary}${local_path_token}|file:///?${local_path_token})" "${doc_path}"; then
  echo "Forbidden Phase 52.5.2 package scaffolding policy: workstation-local absolute path detected" >&2
  exit 1
fi

echo "Phase 52.5.2 package scaffolds and compatibility-shim policy are present."
