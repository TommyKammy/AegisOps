#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"

doc_path="docs/phase-52-closeout-evaluation.md"
absolute_doc_path="${repo_root}/${doc_path}"
readme_path="${repo_root}/README.md"

require_phrase() {
  local file="$1"
  local phrase="$2"
  local description="$3"

  if ! grep -Fq -- "${phrase}" "${file}"; then
    echo "Missing ${description}: ${phrase}" >&2
    exit 1
  fi
}

if [[ ! -s "${absolute_doc_path}" ]]; then
  echo "Missing Phase 52 closeout evaluation: ${doc_path}" >&2
  exit 1
fi

require_phrase "${readme_path}" "[Phase 52.10 closeout evaluation](docs/phase-52-closeout-evaluation.md)" "README Phase 52.10 closeout link"

required_phrases=(
  "# Phase 52 Closeout Evaluation"
  "**Status**: Accepted as executable first-user stack contract foundation; Phase 53 and Phase 54 materialization unblocked with explicit blockers"
  "**Related Issues**: #1063, #1064, #1065, #1066, #1067, #1068, #1069, #1070, #1071, #1072, #1073"
  "Phase 52 is accepted as the executable first-user stack contract foundation."
  "This closeout does not claim that AegisOps is GA, RC, Beta, self-service commercially ready, or that Wazuh or Shuffle product profiles are complete."
  "| #1064 | Phase 52.1 CLI command contract | Closed."
  "| #1065 | Phase 52.2 SMB single-node profile model | Closed."
  "| #1066 | Phase 52.3 combined dependency matrix | Closed."
  "| #1067 | Phase 52.4 compose generator contract | Closed."
  "| #1068 | Phase 52.5 env secrets certs contract | Closed."
  "| #1069 | Phase 52.6 host preflight contract | Closed."
  "| #1070 | Phase 52.7 demo seed contract | Closed."
  "| #1071 | Phase 52.8 clean-host smoke skeleton | Closed."
  "| #1072 | Phase 52.9 first-user stack docs | Closed."
  "| #1073 | Phase 52.10 closeout evaluation | Open until this closeout lands; accepted when this document and focused verifier pass."
  "bash scripts/verify-phase-52-1-cli-command-contract.sh"
  "bash scripts/test-verify-phase-52-1-cli-command-contract.sh"
  "bash scripts/verify-phase-52-2-smb-single-node-profile-model.sh"
  "bash scripts/test-verify-phase-52-2-smb-single-node-profile-model.sh"
  "bash scripts/verify-phase-52-3-combined-dependency-matrix.sh"
  "bash scripts/test-verify-phase-52-3-combined-dependency-matrix.sh"
  "bash scripts/verify-phase-52-4-compose-generator-contract.sh"
  "bash scripts/test-verify-phase-52-4-compose-generator-contract.sh"
  "bash scripts/verify-phase-52-5-env-secrets-certs-contract.sh"
  "bash scripts/test-verify-phase-52-5-env-secrets-certs-contract.sh"
  "bash scripts/verify-phase-52-6-host-preflight-contract.sh"
  "bash scripts/test-verify-phase-52-6-host-preflight-contract.sh"
  "bash scripts/verify-phase-52-7-demo-seed-contract.sh"
  "bash scripts/test-verify-phase-52-7-demo-seed-contract.sh"
  "bash scripts/verify-phase-52-8-clean-host-smoke-skeleton.sh"
  "bash scripts/test-verify-phase-52-8-clean-host-smoke-skeleton.sh"
  "bash scripts/verify-phase-52-9-first-user-stack-docs.sh"
  "bash scripts/test-verify-phase-52-9-first-user-stack-docs.sh"
  "execution_ready=yes"
  "missing_required=none"
  "missing_recommended=none"
  "metadata_errors=none"
  "high_risk_blocking_ambiguity=none"
  "node <codex-supervisor-root>/dist/index.js issue-lint 1063 --config <supervisor-config-path>"
  "node <codex-supervisor-root>/dist/index.js issue-lint 1064 --config <supervisor-config-path>"
  "node <codex-supervisor-root>/dist/index.js issue-lint 1065 --config <supervisor-config-path>"
  "node <codex-supervisor-root>/dist/index.js issue-lint 1066 --config <supervisor-config-path>"
  "node <codex-supervisor-root>/dist/index.js issue-lint 1067 --config <supervisor-config-path>"
  "node <codex-supervisor-root>/dist/index.js issue-lint 1068 --config <supervisor-config-path>"
  "node <codex-supervisor-root>/dist/index.js issue-lint 1069 --config <supervisor-config-path>"
  "node <codex-supervisor-root>/dist/index.js issue-lint 1070 --config <supervisor-config-path>"
  "node <codex-supervisor-root>/dist/index.js issue-lint 1071 --config <supervisor-config-path>"
  "node <codex-supervisor-root>/dist/index.js issue-lint 1072 --config <supervisor-config-path>"
  "node <codex-supervisor-root>/dist/index.js issue-lint 1073 --config <supervisor-config-path>"
  "The accepted smoke result is a skeleton and fixture-backed contract only."
  "The clean-host smoke skeleton preserves command order, mocked or skipped states, contract references, Phase 53/54 prerequisite markers, and false-success rejection."
  "AegisOps records remain the authoritative workflow truth."
  "Generated config, demo seed, CLI status, Docker/Compose state, Wazuh state, Shuffle state, AI output, tickets, evidence systems, browser state, UI cache, downstream receipts, and demo data remain subordinate evidence or setup context."
  "Phase 52 does not implement the Wazuh profile MVP."
  "Phase 52 does not implement the Shuffle profile MVP."
  "Phase 52 does not implement a guided first-user UI journey."
  "Phase 52 clean-host smoke remains a skeleton and must not be reported as a live clean-host product smoke result."
  "Materialize Phase 53 Wazuh profile work next."
  "Explicit blockers for Phase 53 are live Wazuh profile implementation, reviewed Wazuh version pinning, trusted Wazuh secret references, Wazuh volume separation, Wazuh ingest route binding, and replacement of fixture-backed \`init\`, \`up\`, and \`doctor\` checks with live profile-backed behavior."
  "Materialize Phase 54 Shuffle profile work after or alongside the Wazuh-profile sequencing only where dependencies are explicit."
  "Explicit blockers for Phase 54 are live Shuffle profile implementation, reviewed Shuffle version pinning, trusted Shuffle API and callback secret references, Shuffle workflow-catalog custody, callback route binding, volume separation, and replacement of fixture-backed \`seed-demo\` or delegated-execution checks with live profile-backed behavior."
  "Do not treat this recommendation as a claim that Phase 53 or Phase 54 product profiles are complete."
  "Do not claim GA, RC, Beta, or self-service commercial readiness from Phase 52 closeout."
)

for phrase in "${required_phrases[@]}"; do
  require_phrase "${absolute_doc_path}" "${phrase}" "required closeout term in ${doc_path}"
done

mac_home_prefix="$(printf '/%s/' 'Users')"
unix_home_prefix="$(printf '/%s/' 'home')"
windows_backslash_prefix="$(printf '[A-Za-z]:\\\\%s\\\\' 'Users')"
windows_slash_prefix="$(printf '[A-Za-z]:/%s/' 'Users')"
absolute_path_pattern="(${mac_home_prefix}|${unix_home_prefix}|${windows_backslash_prefix}|${windows_slash_prefix})[^ <\`]+"
if grep -Eq -- "${absolute_path_pattern}" "${absolute_doc_path}" "${readme_path}"; then
  echo "Forbidden Phase 52 closeout evaluation: workstation-local absolute path detected" >&2
  exit 1
fi

for forbidden in \
  "Phase 52 proves GA readiness" \
  "Phase 52 proves RC readiness" \
  "Phase 52 proves Beta readiness" \
  "Phase 52 proves self-service commercial readiness" \
  "Phase 53 product profile is complete" \
  "Phase 54 product profile is complete" \
  "Wazuh state is AegisOps workflow truth" \
  "Shuffle state is AegisOps workflow truth" \
  "Docker Compose state is AegisOps workflow truth" \
  "CLI status is AegisOps workflow truth" \
  "Demo data is AegisOps workflow truth" \
  "The clean-host smoke skeleton is a live clean-host product smoke result"; do
  if grep -Fq -- "${forbidden}" "${absolute_doc_path}"; then
    echo "Forbidden Phase 52 closeout evaluation claim: ${forbidden}" >&2
    exit 1
  fi
done

echo "Phase 52 closeout evaluation records child outcomes, verifier evidence, issue-lint summary, accepted limitations, authority boundary, and Phase 53/54 recommendation."
