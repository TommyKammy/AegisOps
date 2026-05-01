#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/deployment/clean-host-smoke-skeleton.md"
readme_path="${repo_root}/README.md"
fixtures_dir="${repo_root}/docs/deployment/fixtures/clean-host-smoke"

required_headings=(
  "# Phase 52.8 Clean-Host Smoke Skeleton"
  "## 1. Purpose"
  "## 2. Authority Boundary"
  "## 3. Smoke Sequence"
  "## 4. Mocked and Skipped States"
  "## 5. Required Contract References"
  "## 6. Fixture Expectations"
  "## 7. Validation Rules"
  "## 8. Forbidden Claims"
  "## 9. Validation"
  "## 10. Non-Goals"
)

required_phrases=(
  "- **Status**: Accepted"
  "- **Date**: 2026-05-01"
  "- **Related Issues**: #1063, #1064, #1067, #1068, #1069, #1070, #1071"
  "This contract defines a clean-host smoke skeleton for the executable first-user stack only. It does not implement full stack startup, Wazuh product profiles, Shuffle product profiles, the first-user guided UI journey, release-candidate behavior, general-availability behavior, or runtime behavior."
  '`init -> up -> doctor -> seed-demo`'
  "Smoke output is validation evidence only."
  "AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, release, gate, and closeout truth."
  'This contract cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md`.'
  "| Step | Command | Required contract reference | Expected skeleton state | Required evidence role |"
  "| State | Meaning | Required follow-up |"
  "| Fixture | Expected validity | Required rejection |"
  'Phase 52.1 CLI command contract: `docs/phase-52-1-cli-command-contract.md`.'
  'Phase 52.4 compose generator contract: `docs/deployment/compose-generator-contract.md`.'
  'Phase 52.5 env secrets certs contract: `docs/deployment/env-secrets-certs-contract.md`.'
  'Phase 52.6 host preflight contract: `docs/deployment/host-preflight-contract.md`.'
  'Phase 52.7 demo seed contract: `docs/deployment/demo-seed-contract.md`.'
  "The smoke skeleton must also name compose, env/secrets/certs, host preflight, and demo seed contract coverage in fixture output."
  'Run `bash scripts/verify-phase-52-8-clean-host-smoke-skeleton.sh`.'
  'Run `bash scripts/test-verify-phase-52-8-clean-host-smoke-skeleton.sh`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1071 --config <supervisor-config-path>`.'
)

command_order=(
  "init"
  "up"
  "doctor"
  "seed-demo"
)

states=(
  "mocked"
  "skipped"
)

coverage_terms=(
  "compose"
  "env/secrets/certs"
  "host preflight"
  "demo seed"
)

required_contract_refs=(
  "docs/phase-52-1-cli-command-contract.md"
  "docs/deployment/compose-generator-contract.md"
  "docs/deployment/env-secrets-certs-contract.md"
  "docs/deployment/host-preflight-contract.md"
  "docs/deployment/demo-seed-contract.md"
)

fixture_expectations=(
  "valid-clean-host-smoke.json|valid|"
  "profile-skipped-clean-host-smoke.json|valid|"
  "false-success.json|invalid|successful full stack"
  "compose-truth.json|invalid|workflow truth"
  "phase-53-54-required.json|invalid|requires Phase 53 or Phase 54 completion"
)

forbidden_claims=(
  "Clean-host smoke success is workflow truth"
  "Clean-host smoke output is source truth"
  "Clean-host smoke output is approval truth"
  "Clean-host smoke output is execution truth"
  "Clean-host smoke output is reconciliation truth"
  "Docker status is AegisOps workflow truth"
  "Docker Compose status is AegisOps workflow truth"
  "Mocked profile work is successful full stack startup"
  "Skipped profile work is successful full stack startup"
  "Phase 52.8 requires Phase 53 profile completion"
  "Phase 52.8 requires Phase 54 profile completion"
  "Phase 52.8 implements Wazuh product profiles"
  "Phase 52.8 implements Shuffle product profiles"
  "Phase 52.8 completes RC behavior"
  "Phase 52.8 completes GA behavior"
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
  echo "Missing Phase 52.8 clean-host smoke skeleton: ${doc_path}" >&2
  exit 1
fi

doc_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${doc_path}"
)"

for heading in "${required_headings[@]}"; do
  if ! grep -Fxq -- "${heading}" <<<"${doc_rendered_markdown}"; then
    echo "Missing Phase 52.8 clean-host smoke skeleton heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" <<<"${doc_rendered_markdown}"; then
    echo "Missing Phase 52.8 clean-host smoke skeleton statement: ${phrase}" >&2
    exit 1
  fi
done

for index in "${!command_order[@]}"; do
  step=$((index + 1))
  command="${command_order[$index]}"
  if ! grep -Eq "^\\| ${step} \\| \`${command}\` \\| [^|]+ \\| [^|]+ \\| [^|]+ \\|$" <<<"${doc_rendered_markdown}"; then
    echo "Missing complete Phase 52.8 smoke sequence row: ${command}" >&2
    exit 1
  fi
done

for state in "${states[@]}"; do
  if ! grep -Eq "^\\| \`${state}\` \\| [^|]+ \\| [^|]+ \\|$" <<<"${doc_rendered_markdown}"; then
    echo "Missing complete Phase 52.8 state row: ${state}" >&2
    exit 1
  fi
done

for coverage_term in "${coverage_terms[@]}"; do
  if ! grep -Fq -- "${coverage_term}" <<<"${doc_rendered_markdown}"; then
    echo "Missing Phase 52.8 coverage term: ${coverage_term}" >&2
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
      negative_context = line ~ /(cannot|must not|fail|fails|invalid|rejected|required rejection|forbidden|instead of reporting|not implement|before claiming|treated as)/
      if (!in_forbidden_claims && !negative_context && line ~ /((mocked|skipped).*(successful full stack|full-stack success|production readiness|rc readiness|ga readiness)|(docker|docker compose).*workflow truth)/) {
        found = 1
      }
    }
    END { exit(found ? 0 : 1) }
  ' <<<"${doc_rendered_markdown}"
}

for claim in "${forbidden_claims[@]}"; do
  if contains_forbidden_outside_forbidden_section "${claim}"; then
    echo "Forbidden Phase 52.8 clean-host smoke skeleton claim: ${claim}" >&2
    exit 1
  fi
done

if contains_false_success_claim; then
  echo "Forbidden Phase 52.8 clean-host smoke skeleton claim: false success or workflow truth" >&2
  exit 1
fi

path_token_boundary="(^|[[:space:]'\"\`(<{=])"
path_token_chars="[^[:space:]'\"\` )>}|]"
home_absolute_path="/(Users|home)/${path_token_chars}+"
windows_user_path="[A-Za-z]:[\\\\/]Users[\\\\/]${path_token_chars}*"
local_path_token="(${home_absolute_path}|${windows_user_path})"

if grep -REq "(${path_token_boundary}${local_path_token}|file:///?${local_path_token})" "${doc_path}" "${fixtures_dir}" 2>/dev/null; then
  echo "Forbidden Phase 52.8 clean-host smoke skeleton: workstation-local absolute path detected" >&2
  exit 1
fi

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing README for Phase 52.8 clean-host smoke skeleton link check: ${readme_path}" >&2
  exit 1
fi

readme_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${readme_path}" | perl -pe 's/`[^`]*`//g'
)"

if ! grep -Eq '\[[^]]+\]\(docs/deployment/clean-host-smoke-skeleton\.md\)' <<<"${readme_rendered_markdown}"; then
  echo "README must link the Phase 52.8 clean-host smoke skeleton." >&2
  exit 1
fi

python3 - "${fixtures_dir}" "${fixture_expectations[@]}" "${required_contract_refs[@]}" <<'PY'
import json
import pathlib
import sys

fixtures_dir = pathlib.Path(sys.argv[1])
expectations = [item.split("|", 2) for item in sys.argv[2:7]]
required_contract_refs = set(sys.argv[7:])
required_order = ["init", "up", "doctor", "seed-demo"]
allowed_states = {"mocked", "skipped"}
required_coverage = {"compose", "env/secrets/certs", "host preflight", "demo seed"}
truth_markers = (
    "workflow truth",
    "source truth",
    "approval truth",
    "execution truth",
    "reconciliation truth",
    "gate truth",
    "release truth",
    "production truth",
    "closeout truth",
)

if not fixtures_dir.is_dir():
    print(f"Missing Phase 52.8 clean-host smoke fixture directory: {fixtures_dir}", file=sys.stderr)
    sys.exit(1)


def text_contains_truth_claim(value):
    if isinstance(value, str):
        lowered = value.lower()
        return any(marker in lowered for marker in truth_markers)
    if isinstance(value, list):
        return any(text_contains_truth_claim(item) for item in value)
    if isinstance(value, dict):
        return any(text_contains_truth_claim(item) for item in value.values())
    return False


def rejection_reasons(payload):
    reasons = []
    sequence = payload.get("sequence")
    if not isinstance(sequence, list) or len(sequence) != len(required_order):
        reasons.append("missing smoke sequence")
        return reasons

    commands = [step.get("command") for step in sequence]
    if commands != required_order:
        reasons.append("invalid command order")

    if payload.get("overall_state") not in allowed_states:
        reasons.append("invalid overall state")

    coverage = payload.get("contract_coverage")
    if not isinstance(coverage, list) or set(coverage) != required_coverage:
        reasons.append("missing contract coverage")

    if payload.get("full_stack_success") is True:
        reasons.append("successful full stack")

    if payload.get("requires_phase_53_or_54_completion") is True:
        reasons.append("requires Phase 53 or Phase 54 completion")

    if text_contains_truth_claim(payload):
        reasons.append("workflow truth")

    seen_states = set()
    seen_contract_refs = set()
    for expected_step, step in enumerate(sequence, start=1):
        if step.get("step") != expected_step:
            reasons.append("invalid step number")
        state = step.get("state")
        if state not in allowed_states:
            reasons.append("invalid step state")
        else:
            seen_states.add(state)
        for field in ("missing_prerequisite", "closing_phase", "safe_next_action", "evidence_role"):
            if not isinstance(step.get(field), str) or not step[field].strip():
                reasons.append(f"missing {field}")
        contract_refs = step.get("contract_refs")
        if not isinstance(contract_refs, list) or not contract_refs:
            reasons.append("missing contract refs")
        else:
            seen_contract_refs.update(contract_refs)

    if not seen_states.intersection(allowed_states):
        reasons.append("missing mocked or skipped states")

    missing_refs = required_contract_refs.difference(seen_contract_refs)
    if missing_refs:
        reasons.append("missing contract refs")

    return reasons


for filename, expected_validity, required_rejection in expectations:
    path = fixtures_dir / filename
    if not path.is_file():
        print(f"Missing Phase 52.8 clean-host smoke fixture: {filename}", file=sys.stderr)
        sys.exit(1)
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    reasons = rejection_reasons(payload)
    if expected_validity == "valid" and reasons:
        print(
            f"Invalid Phase 52.8 clean-host smoke fixture state for {filename}: "
            f"expected valid; got {', '.join(sorted(set(reasons)))}",
            file=sys.stderr,
        )
        sys.exit(1)
    if expected_validity == "invalid":
        if not reasons:
            print(
                f"Invalid Phase 52.8 clean-host smoke fixture state for {filename}: "
                "expected rejection",
                file=sys.stderr,
            )
            sys.exit(1)
        if required_rejection and required_rejection not in reasons:
            print(
                f"Missing Phase 52.8 clean-host smoke fixture rejection for {filename}: "
                f"{required_rejection}; got {', '.join(sorted(set(reasons)))}",
                file=sys.stderr,
            )
            sys.exit(1)
PY

echo "Phase 52.8 clean-host smoke skeleton preserves sequence order, mocked/skipped states, contract references, and false-success rejection."
