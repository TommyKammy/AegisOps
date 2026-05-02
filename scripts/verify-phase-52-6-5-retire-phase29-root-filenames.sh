#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
control_plane_root="${repo_root}/control-plane"
package_root="${control_plane_root}/aegisops_control_plane"
registry_path="${package_root}/core/legacy_import_aliases.py"
compatibility_test="${repo_root}/control-plane/tests/test_phase52_6_5_phase29_root_filename_retirement.py"
legacy_scoring_adapter="${package_root}/ml_shadow/legacy_scoring_adapter.py"

retired_root_files=(
  "phase29_shadow_dataset.py"
  "phase29_shadow_scoring.py"
  "phase29_evidently_drift_visibility.py"
  "phase29_mlflow_shadow_model_registry.py"
)

if [[ ! -d "${package_root}" ]]; then
  echo "Missing control-plane package root: control-plane/aegisops_control_plane" >&2
  exit 1
fi

if [[ ! -f "${registry_path}" ]]; then
  echo "Missing legacy import alias registry: control-plane/aegisops_control_plane/core/legacy_import_aliases.py" >&2
  exit 1
fi

if [[ ! -f "${compatibility_test}" ]]; then
  echo "Missing Phase 52.6.5 compatibility regression: control-plane/tests/test_phase52_6_5_phase29_root_filename_retirement.py" >&2
  exit 1
fi

if [[ ! -f "${legacy_scoring_adapter}" ]]; then
  echo "Missing legacy scoring adapter owner: control-plane/aegisops_control_plane/ml_shadow/legacy_scoring_adapter.py" >&2
  exit 1
fi

for retired_root_file in "${retired_root_files[@]}"; do
  if [[ -e "${package_root}/${retired_root_file}" ]]; then
    echo "Phase 52.6.5 Phase29 root filename must be retired: control-plane/aegisops_control_plane/${retired_root_file}" >&2
    exit 1
  fi
done

path_token_boundary="(^|[[:space:]'\"\`(<{=])"
path_token_chars="[^[:space:]'\"\` )>}|]"
home_absolute_path="/(Users|home)/${path_token_chars}+"
windows_user_path="[A-Za-z]:[\\\\/]Users[\\\\/]${path_token_chars}*"
local_path_token="(${home_absolute_path}|${windows_user_path})"

if grep -Eq "(${path_token_boundary}${local_path_token}|file:///?${local_path_token})" \
  "${registry_path}" "${compatibility_test}" "${legacy_scoring_adapter}"; then
  echo "Forbidden Phase 52.6.5 Phase29 retirement artifact: workstation-local absolute path detected" >&2
  exit 1
fi

export PHASE52_6_5_CONTROL_PLANE_ROOT="${control_plane_root}"

python3 - <<'PY'
from __future__ import annotations

import importlib
import os
from pathlib import Path
import sys

control_plane_root = Path(os.environ["PHASE52_6_5_CONTROL_PLANE_ROOT"])
if str(control_plane_root) not in sys.path:
    sys.path.insert(0, str(control_plane_root))

registry = importlib.import_module("aegisops_control_plane.core.legacy_import_aliases")

expected_aliases = {
    "aegisops_control_plane.phase29_shadow_dataset": (
        "aegisops_control_plane.ml_shadow.dataset",
        "ml_shadow",
        "ml_shadow/dataset.py",
        "Phase29ShadowDatasetSnapshot",
        True,
    ),
    "aegisops_control_plane.phase29_evidently_drift_visibility": (
        "aegisops_control_plane.ml_shadow.drift_visibility",
        "ml_shadow",
        "ml_shadow/drift_visibility.py",
        "Phase29EvidentlyDriftVisibilityReport",
        True,
    ),
    "aegisops_control_plane.phase29_mlflow_shadow_model_registry": (
        "aegisops_control_plane.ml_shadow.mlflow_registry",
        "ml_shadow",
        "ml_shadow/mlflow_registry.py",
        "Phase29MlflowShadowModelTrackingResult",
        True,
    ),
    "aegisops_control_plane.phase29_shadow_scoring": (
        "aegisops_control_plane.ml_shadow.legacy_scoring_adapter",
        "ml_shadow",
        "ml_shadow/legacy_scoring_adapter.py",
        "Phase29ShadowScoreResult",
        False,
    ),
}

for legacy_path, (
    target_path,
    target_family,
    owner,
    attribute,
    require_same_module,
) in expected_aliases.items():
    alias = registry.LEGACY_IMPORT_ALIASES.get(legacy_path)
    if alias is None:
        print(
            f"Phase 52.6.5 missing Phase29 legacy alias: {legacy_path}",
            file=sys.stderr,
        )
        sys.exit(1)
    if alias.target_module != target_path:
        print(
            f"Phase 52.6.5 Phase29 alias target mismatch for {legacy_path}: {alias.target_module}",
            file=sys.stderr,
        )
        sys.exit(1)
    if alias.target_family != target_family or alias.owner != owner:
        print(
            f"Phase 52.6.5 Phase29 alias owner metadata mismatch for {legacy_path}",
            file=sys.stderr,
        )
        sys.exit(1)
    if legacy_path in registry.RETAINED_COMPATIBILITY_BLOCKERS:
        print(
            f"Phase 52.6.5 Phase29 path still listed as a retained blocker: {legacy_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    legacy_module = importlib.import_module(legacy_path)
    target_module = importlib.import_module(target_path)
    if require_same_module and legacy_module is not target_module:
        print(
            f"Phase 52.6.5 Phase29 alias changed module identity for {legacy_path}",
            file=sys.stderr,
        )
        sys.exit(1)
    if getattr(legacy_module, attribute) is not getattr(target_module, attribute):
        print(
            f"Phase 52.6.5 Phase29 alias changed compatibility attribute for {legacy_path}:{attribute}",
            file=sys.stderr,
        )
        sys.exit(1)

legacy_scoring = importlib.import_module("aegisops_control_plane.phase29_shadow_scoring")
canonical_scoring = importlib.import_module("aegisops_control_plane.ml_shadow.scoring")
if legacy_scoring is canonical_scoring:
    print(
        "Phase 52.6.5 legacy scoring path must preserve wrapper behavior outside canonical scoring.",
        file=sys.stderr,
    )
    sys.exit(1)
if legacy_scoring.Phase29ShadowScoringError is not canonical_scoring.Phase29ShadowScoringError:
    print(
        "Phase 52.6.5 legacy scoring path lost canonical error compatibility.",
        file=sys.stderr,
    )
    sys.exit(1)
expected_compatibility_owners = {
    "feature_frequencies_at_inference_time": legacy_scoring.Phase29ShadowScoreResult,
    "scored_examples": legacy_scoring.Phase29OfflineShadowScoringSnapshot,
}
for compatibility_attribute, owner in expected_compatibility_owners.items():
    if not hasattr(owner, compatibility_attribute):
        print(
            "Phase 52.6.5 legacy scoring wrapper is missing "
            + compatibility_attribute,
            file=sys.stderr,
        )
        sys.exit(1)

print(
    "Phase 52.6.5 Phase29 root filenames are retired, ml_shadow remains the owner, "
    "and legacy import compatibility is explicitly registered."
)
PY
