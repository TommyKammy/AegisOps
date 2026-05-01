#!/usr/bin/env bash

set -euo pipefail

if [[ $# -gt 0 ]]; then
  repo_root="$1"
else
  repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi
doc_path="${repo_root}/docs/deployment/host-preflight-contract.md"
matrix_path="${repo_root}/docs/deployment/combined-dependency-matrix.md"
readme_path="${repo_root}/README.md"
fixtures_dir="${repo_root}/docs/deployment/fixtures/host-preflight"

required_headings=(
  "# Phase 52.6 Host Preflight Contract"
  "## 1. Purpose"
  "## 2. Authority Boundary"
  "## 3. Checked Inputs"
  "## 4. Output States"
  "## 5. Fixture Expectations"
  "## 6. Dependency Matrix Link"
  "## 7. Validation Rules"
  "## 8. Forbidden Claims"
  "## 9. Validation"
  "## 10. Non-Goals"
)

required_phrases=(
  "- **Status**: Accepted"
  "- **Date**: 2026-05-01"
  "- **Related Issues**: #1063, #1066, #1069"
  "This contract defines host preflight input and output expectations for the executable first-user stack only. It does not implement the installer, stack startup, live host probing, Wazuh product profiles, Shuffle product profiles, production supportability, release-candidate behavior, general-availability behavior, or runtime behavior."
  'The contract covers Docker, Docker Compose, RAM, disk, ports, `vm.max_map_count`, and setup profile validity.'
  'The contract consumes the Phase 52.3 dependency matrix fields in `docs/deployment/combined-dependency-matrix.md` and must not redefine dependency authority outside that matrix.'
  "Host preflight output is setup readiness evidence only."
  'Docker state, Docker Compose state, RAM, disk, port state, `vm.max_map_count`, generated config, setup profile selection, fixture output, or preflight status is not alert, case, evidence, approval, execution, reconciliation, workflow, gate, release, production, or closeout truth.'
  "AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, release, gate, and closeout truth."
  'This contract cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md`.'
  "| Check | Required input | Pass condition | Fail-closed condition |"
  "| State | Meaning | Accepted use |"
  "| Fixture | Required state | Required failing check |"
  'Negative fixtures must fail closed when a missing Docker engine, missing Docker Compose plugin, bad port conflict, low RAM, missing Linux `vm.max_map_count`, or invalid profile is reported as `pass`, `skip`, or `mocked`.'
  "Known incompatible versions, missing prerequisites, malformed fields, placeholder-backed credentials, direct backend exposure, raw forwarded-header trust, and inferred scope bindings must fail closed."
  '`pass`, `fail`, `skip`, and `mocked` output states are not distinguished;'
  'Run `bash scripts/verify-phase-52-6-host-preflight-contract.sh`.'
  'Run `bash scripts/test-verify-phase-52-6-host-preflight-contract.sh`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1069 --config <supervisor-config-path>`.'
)

checks=(
  "Docker engine"
  "Docker Compose"
  "RAM"
  "Disk"
  "Ports"
  "vm.max_map_count"
  "Profile validity"
)

states=(
  "pass"
  "fail"
  "skip"
  "mocked"
)

required_preflight_fields=(
  "AEGISOPS_PREFLIGHT_DOCKER_ENGINE_VERSION"
  "AEGISOPS_PREFLIGHT_COMPOSE_VERSION"
  "AEGISOPS_PREFLIGHT_HOST_RAM_GB"
  "AEGISOPS_PREFLIGHT_HOST_DISK_GB"
  "AEGISOPS_PREFLIGHT_PROXY_PUBLIC_PORTS"
  "AEGISOPS_PREFLIGHT_VM_MAX_MAP_COUNT"
  "AEGISOPS_PREFLIGHT_PROFILE"
)

fixture_expectations=(
  "valid-pass.json|pass|"
  "mocked-pass.json|mocked|"
  "non-linux-vm-max-map-count-skip.json|skip|"
  "missing-docker.json|fail|Docker engine"
  "missing-compose.json|fail|Docker Compose"
  "bad-ports.json|fail|Ports"
  "low-ram.json|fail|RAM"
  "missing-vm-max-map-count.json|fail|vm.max_map_count"
  "invalid-profile.json|fail|Profile validity"
)

forbidden_claims=(
  "Host preflight status is AegisOps workflow truth"
  "Docker status is AegisOps workflow truth"
  "Docker Compose status is AegisOps workflow truth"
  "Port state is AegisOps release truth"
  "Mocked preflight output is live readiness evidence"
  "Skipped vm.max_map_count is valid on Linux"
  "Missing Docker reported as success"
  "Bad port conflict reported as success"
  "Low RAM reported as success"
  "Missing vm.max_map_count reported as success"
  "Invalid profile reported as success"
  "This contract implements the installer"
  "This contract starts the stack"
  "This contract implements Wazuh product profiles"
  "This contract implements Shuffle product profiles"
)

rendered_markdown_without_code_blocks() {
  local markdown_path="$1"

  awk '
    /^[[:space:]]*(```|~~~)/ {
      in_fenced_block = !in_fenced_block
      next
    }
    in_fenced_block { next }
    substr($0, 1, 1) == "\t" { next }
    substr($0, 1, 4) == "    " { next }
    { print }
  ' "${markdown_path}" | perl -0pe 's/<!--.*?-->//gs'
}

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Phase 52.6 host preflight contract: ${doc_path}" >&2
  exit 1
fi

doc_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${doc_path}"
)"

for heading in "${required_headings[@]}"; do
  if ! grep -Fxq -- "${heading}" <<<"${doc_rendered_markdown}"; then
    echo "Missing Phase 52.6 host preflight contract heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" <<<"${doc_rendered_markdown}"; then
    echo "Missing Phase 52.6 host preflight contract statement: ${phrase}" >&2
    exit 1
  fi
done

for check in "${checks[@]}"; do
  if ! grep -Fq -- "| ${check} |" <<<"${doc_rendered_markdown}" && \
      ! grep -Fq -- "| \`${check}\` |" <<<"${doc_rendered_markdown}"; then
    echo "Missing complete Phase 52.6 checked input row: ${check}" >&2
    exit 1
  fi
done

for state in "${states[@]}"; do
  if ! grep -Eq "^\\| \`${state}\` \\| [^|]+ \\| [^|]+ \\|$" <<<"${doc_rendered_markdown}"; then
    echo "Missing complete Phase 52.6 output state row: ${state}" >&2
    exit 1
  fi
done

for field in "${required_preflight_fields[@]}"; do
  if ! grep -Fq -- "\`${field}\`" <<<"${doc_rendered_markdown}"; then
    echo "Missing Phase 52.6 host preflight field: ${field}" >&2
    exit 1
  fi
done

contains_forbidden_outside_forbidden_section() {
  local claim="$1"

  awk -v claim="${claim}" '
    BEGIN { claim_lower = tolower(claim) }
    /^## 8\. Forbidden Claims$/ { in_forbidden_claims = 1; next }
    /^## / && in_forbidden_claims { in_forbidden_claims = 0 }
    !in_forbidden_claims && index(tolower($0), claim_lower) { found = 1 }
    END { exit(found ? 0 : 1) }
  ' "${doc_path}"
}

contains_false_success_claim() {
  awk '
    /^## 8\. Forbidden Claims$/ { in_forbidden_claims = 1; next }
    /^## / && in_forbidden_claims { in_forbidden_claims = 0 }
    {
      line = tolower($0)
      negative_context = line ~ /(must fail|fail closed|fails validation|invalid|must not|cannot|not satisfy|blocks setup|reported as `pass`, `skip`, or `mocked`)/
      if (!in_forbidden_claims && !negative_context && line ~ /(missing docker|bad port|low ram|missing.*vm\.max_map_count|invalid profile).*reported as success/) {
        found = 1
      }
    }
    END { exit(found ? 0 : 1) }
  ' <<<"${doc_rendered_markdown}"
}

for claim in "${forbidden_claims[@]}"; do
  if contains_forbidden_outside_forbidden_section "${claim}"; then
    echo "Forbidden Phase 52.6 host preflight contract claim: ${claim}" >&2
    exit 1
  fi
done

if contains_false_success_claim; then
  echo "Forbidden Phase 52.6 host preflight contract claim: failed prerequisite reported as success" >&2
  exit 1
fi

path_token_boundary="(^|[[:space:]'\"\`(<{=])"
path_token_chars="[^[:space:]'\"\` )>}|]"
home_absolute_path="/(Users|home)/${path_token_chars}+"
windows_user_path="[A-Za-z]:[\\\\/]Users[\\\\/]${path_token_chars}*"
local_path_token="(${home_absolute_path}|${windows_user_path})"

if grep -REq "(${path_token_boundary}${local_path_token}|file:///?${local_path_token})" "${doc_path}" "${fixtures_dir}" 2>/dev/null; then
  echo "Forbidden Phase 52.6 host preflight contract: workstation-local absolute path detected" >&2
  exit 1
fi

if [[ ! -f "${matrix_path}" ]]; then
  echo "Missing Phase 52.3 dependency matrix for Phase 52.6 link check: ${matrix_path}" >&2
  exit 1
fi

for field in AEGISOPS_PREFLIGHT_DOCKER_ENGINE_VERSION AEGISOPS_PREFLIGHT_COMPOSE_VERSION AEGISOPS_PREFLIGHT_PROXY_PUBLIC_PORTS; do
  if ! grep -Fq -- "\`${field}\`" "${matrix_path}"; then
    echo "Phase 52.6 dependency matrix link missing matrix field: ${field}" >&2
    exit 1
  fi
done

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing README for Phase 52.6 host preflight contract link check: ${readme_path}" >&2
  exit 1
fi

readme_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${readme_path}" | perl -pe 's/`[^`]*`//g'
)"

if ! grep -Eq '\[[^]]+\]\(docs/deployment/host-preflight-contract\.md\)' <<<"${readme_rendered_markdown}"; then
  echo "README must link the Phase 52.6 host preflight contract." >&2
  exit 1
fi

if [[ ! -d "${fixtures_dir}" ]]; then
  echo "Missing Phase 52.6 host preflight fixture directory: ${fixtures_dir}" >&2
  exit 1
fi

python3 - "$fixtures_dir" "${fixture_expectations[@]}" <<'PY'
import json
import pathlib
import sys

fixtures_dir = pathlib.Path(sys.argv[1])
expectations = sys.argv[2:]
allowed_states = {"pass", "fail", "skip", "mocked"}
required_result_fields = {"check", "state", "source", "summary", "safe_next_action"}

for expectation in expectations:
    filename, expected_state, required_check = expectation.split("|", 2)
    path = fixtures_dir / filename
    if not path.is_file():
        print(f"Missing Phase 52.6 host preflight fixture: {filename}", file=sys.stderr)
        sys.exit(1)
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if payload.get("overall_state") != expected_state:
        print(
            f"Invalid Phase 52.6 host preflight fixture state for {filename}: "
            f"expected {expected_state}",
            file=sys.stderr,
        )
        sys.exit(1)
    if payload.get("overall_state") not in allowed_states:
        print(f"Unknown Phase 52.6 fixture state in {filename}", file=sys.stderr)
        sys.exit(1)
    results = payload.get("results")
    if not isinstance(results, list) or not results:
        print(f"Missing Phase 52.6 fixture results: {filename}", file=sys.stderr)
        sys.exit(1)
    for result in results:
        missing = required_result_fields.difference(result)
        if missing:
            print(
                f"Missing Phase 52.6 fixture result fields in {filename}: "
                f"{', '.join(sorted(missing))}",
                file=sys.stderr,
            )
            sys.exit(1)
        if result["state"] not in allowed_states:
            print(f"Unknown Phase 52.6 result state in {filename}", file=sys.stderr)
            sys.exit(1)
    if expected_state != "fail" and any(result["state"] != expected_state for result in results):
        print(
            f"Invalid Phase 52.6 host preflight fixture state for {filename}: "
            f"expected all results to be {expected_state}",
            file=sys.stderr,
        )
        sys.exit(1)
    if expected_state == "fail":
        if not any(
            result.get("check") == required_check and result.get("state") == "fail"
            for result in results
        ):
            print(
                f"Missing Phase 52.6 failing fixture check for {filename}: {required_check}",
                file=sys.stderr,
            )
            sys.exit(1)
    elif required_check:
        print(f"Unexpected Phase 52.6 required failing check for {filename}", file=sys.stderr)
        sys.exit(1)
PY

echo "Phase 52.6 host preflight contract is present and preserves checked inputs, output states, negative fixtures, dependency-matrix linkage, and authority boundaries."
