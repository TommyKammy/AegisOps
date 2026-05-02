#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"

doc_path="docs/phase-53-closeout-evaluation.md"
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
  echo "Missing Phase 53 closeout evaluation: ${doc_path}" >&2
  exit 1
fi

if [[ ! -s "${readme_path}" ]]; then
  echo "Missing README for Phase 53 closeout link check: README.md" >&2
  exit 1
fi

require_phrase "${readme_path}" "[Phase 53.9 closeout evaluation](docs/phase-53-closeout-evaluation.md)" "README Phase 53.9 closeout link"

required_phrases=()
while IFS= read -r phrase; do
  required_phrases+=("${phrase}")
done <<'EOF'
# Phase 53 Closeout Evaluation
**Status**: Accepted as Wazuh product profile MVP evidence and handoff baseline; Phase 54, Phase 55, and Phase 61 can consume the bounded Wazuh profile MVP with explicit retained blockers.
**Related Issues**: #1135, #1136, #1137, #1138, #1139, #1140, #1141, #1142, #1143, #1144
Phase 53 is accepted as the Wazuh product profile MVP evidence baseline for the `smb-single-node` profile.
Wazuh remains a subordinate detection substrate.
Wazuh detections are analytic signals until admitted and linked by AegisOps.
AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, source admission, release, gate, and closeout truth.
This closeout does not claim Phase 54 Shuffle profile work is complete, Phase 55 guided first-user journey work is complete, Phase 61 SIEM breadth is complete, AegisOps is Beta, RC, GA, self-service commercially ready, or a replacement for every SIEM/SOAR capability.
| #1135 | Epic: Phase 53 Wazuh Product Profile MVP | Open until #1144 lands; accepted when this closeout, focused verifier, Phase 53 verifiers, focused Wazuh tests, path hygiene, and issue-lint pass. |
| #1136 | Phase 53.1 Wazuh SMB single-node profile contract | Closed.
| #1137 | Phase 53.2 Wazuh certificate and credential handling | Closed.
| #1138 | Phase 53.3 Wazuh manager intake binding | Closed.
| #1139 | Phase 53.4 Wazuh sample signal fixture | Closed.
| #1140 | Phase 53.5 Wazuh first agent enrollment helper | Closed.
| #1141 | Phase 53.6 Wazuh source-health projection | Closed.
| #1142 | Phase 53.7 Wazuh upgrade and rollback evidence | Closed.
| #1143 | Phase 53.8 Wazuh authority-boundary negative tests | Closed.
| #1144 | Phase 53.9 Phase 53 closeout evaluation | Open until this closeout lands; accepted when this document and focused negative verifier pass. |
| Wazuh product profile | Deferred placeholder from Phase 52 first-user stack contracts. | Repo-owned `smb-single-node` Wazuh profile contract with manager, indexer, dashboard, exact `4.12.0` pins, resource, port, volume, and certificate expectations. |
| Certificate and credential posture | Generic env, secret, and certificate contract from Phase 52.5. | Wazuh-specific certificate wrapper posture, trusted custody references, default credential rejection, placeholder rejection, and rotation guidance. |
| Intake binding | Reviewed Wazuh-facing analytic-signal expectation. | `/intake/wazuh` and `aegisops-proxy:/intake/wazuh -> aegisops-control-plane:/intake/wazuh` with required provenance and shared-secret custody reference. |
| Sample signal evidence | Existing Wazuh fixture families for earlier source work. | Reviewed SMB single-node SSH authentication failure Wazuh alert and analytic-signal fixtures tied to Phase 53.4 parser mapping evidence. |
| Enrollment | Deferred fleet and agent posture. | One-endpoint enrollment helper contract only, with rollback notes and no fleet-scale Wazuh management claim. |
| Source health | Deferred source-health projection. | Subordinate source-health projection states for Wazuh manager, dashboard, indexer, intake, signal freshness, parser, volume, credential, unavailable, stale, degraded, and mismatched posture. |
| Upgrade and rollback | No Wazuh profile-change evidence template for the MVP. | Evidence template for future Wazuh profile version changes, without live upgrader or upgrade automation. |
| Authority boundary | Wazuh subordinate posture inherited from Phase 51.6 and Phase 52 contracts. | Focused negative tests prove raw Wazuh status cannot close cases and Wazuh-triggered Shuffle runs without AegisOps delegation remain mismatched. |
`docs/deployment/wazuh-smb-single-node-profile-contract.md`
`docs/deployment/wazuh-certificate-credential-contract.md`
`docs/deployment/wazuh-manager-intake-binding-contract.md`
`docs/deployment/wazuh-agent-enrollment-helper-contract.md`
`docs/deployment/wazuh-source-health-projection-contract.md`
`docs/deployment/wazuh-upgrade-rollback-evidence-contract.md`
`docs/deployment/wazuh-authority-boundary-negative-tests.md`
`control-plane/tests/fixtures/wazuh/phase53-smb-single-node-ssh-auth-failure-alert.json`
`control-plane/tests/fixtures/wazuh/phase53-smb-single-node-ssh-auth-failure-analytic-signal.json`
`control-plane/tests/test_wazuh_adapter.py`
`control-plane/tests/test_cross_boundary_negative_e2e_validation.py`
`docs/phase-53-closeout-evaluation.md`
`scripts/verify-phase-53-9-closeout-evaluation.sh`
`scripts/test-verify-phase-53-9-closeout-evaluation.sh`
`bash scripts/verify-phase-53-1-wazuh-profile-contract.sh`
`bash scripts/test-verify-phase-53-1-wazuh-profile-contract.sh`
`bash scripts/verify-phase-53-2-wazuh-cert-credential-contract.sh`
`bash scripts/test-verify-phase-53-2-wazuh-cert-credential-contract.sh`
`bash scripts/verify-phase-53-3-wazuh-intake-binding-contract.sh`
`bash scripts/test-verify-phase-53-3-wazuh-intake-binding-contract.sh`
`PYTHONPATH="${PWD}/control-plane:${PWD}/control-plane/tests" python3 -m unittest test_wazuh_adapter.WazuhAlertAdapterTests`
`bash scripts/verify-phase-53-5-wazuh-agent-enrollment-helper-contract.sh`
`bash scripts/test-verify-phase-53-5-wazuh-agent-enrollment-helper-contract.sh`
`bash scripts/verify-phase-53-6-wazuh-source-health-projection.sh`
`bash scripts/test-verify-phase-53-6-wazuh-source-health-projection.sh`
`bash scripts/verify-phase-53-7-wazuh-upgrade-rollback-evidence.sh`
`bash scripts/test-verify-phase-53-7-wazuh-upgrade-rollback-evidence.sh`
`bash scripts/verify-phase-53-8-wazuh-authority-boundary-negative-tests.sh`
`bash scripts/verify-publishable-path-hygiene.sh`
`bash scripts/verify-phase-53-9-closeout-evaluation.sh`
`bash scripts/test-verify-phase-53-9-closeout-evaluation.sh`
node <codex-supervisor-root>/dist/index.js issue-lint 1135 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1144 --config <supervisor-config-path>
execution_ready=yes
missing_required=none
missing_recommended=none
metadata_errors=none
high_risk_blocking_ambiguity=none
Phase 53 does not implement Phase 54 Shuffle product profiles.
Phase 53 does not implement Phase 55 guided first-user UI journey work.
Phase 53 does not complete Phase 61 SIEM breadth, broad detector catalog coverage, or every source-family expectation.
Phase 53 does not implement Wazuh Active Response as an authority path.
Phase 53 does not approve a direct Wazuh-to-Shuffle shortcut.
Phase 53 does not let Wazuh alert status close AegisOps cases.
Phase 53 does not implement fleet-scale Wazuh agent management, a full live Wazuh upgrader, secret backend integration, customer-specific credential provisioning, Beta readiness, RC readiness, GA readiness, commercial replacement readiness, or Wazuh replacement readiness.
Phase 54 can consume the Wazuh profile MVP as the reviewed Wazuh-side substrate and intake context for Shuffle profile work.
Phase 54 must still implement its own Shuffle profile contract, callback custody, delegated-execution boundary, workflow catalog custody, and negative tests.
Phase 55 can consume the Wazuh profile MVP as one setup and source-health evidence surface for the guided first-user journey.
Phase 55 must still implement the guided journey, user-facing validation flow, runtime custody choices, error handling, and first-user ergonomics.
Phase 61 can consume the Wazuh profile MVP as the first reviewed SIEM substrate profile and evidence pattern.
Phase 61 must still implement SIEM breadth, source-family prioritization, detector coverage expansion, and any additional source profile contracts explicitly.
Phase 53 does not complete Phase 61 SIEM breadth.
This closeout is evidence recording only.
EOF

for phrase in "${required_phrases[@]}"; do
  require_phrase "${absolute_doc_path}" "${phrase}" "required Phase 53 closeout term in ${doc_path}"
done

mac_home_prefix="$(printf '/%s/' 'Users')"
unix_home_prefix="$(printf '/%s/' 'home')"
windows_backslash_prefix="$(printf '[A-Za-z]:\\\\%s\\\\' 'Users')"
windows_slash_prefix="$(printf '[A-Za-z]:/%s/' 'Users')"
absolute_path_pattern="(${mac_home_prefix}|${unix_home_prefix}|${windows_backslash_prefix}|${windows_slash_prefix})[^ <\`]+"
if grep -Eq -- "${absolute_path_pattern}" "${absolute_doc_path}" "${readme_path}"; then
  echo "Forbidden Phase 53 closeout evaluation: workstation-local absolute path detected" >&2
  exit 1
fi

for forbidden in \
  "Phase 54 Shuffle profile work is complete" \
  "Phase 55 guided first-user journey work is complete" \
  "Phase 61 SIEM breadth is complete" \
  "Phase 53 proves Beta readiness" \
  "Phase 53 proves RC readiness" \
  "Phase 53 proves GA readiness" \
  "Phase 53 proves self-service commercial readiness" \
  "Phase 53 proves commercial replacement readiness" \
  "AegisOps replaces every SIEM/SOAR capability" \
  "Wazuh Active Response is an authority path" \
  "Direct Wazuh-to-Shuffle shortcuts are approved" \
  "Wazuh alert status closes AegisOps cases" \
  "Wazuh dashboard state is AegisOps workflow truth" \
  "Wazuh source-health projection is AegisOps closeout truth" \
  "Wazuh version state is AegisOps release truth"; do
  if grep -F -- "${forbidden}" "${absolute_doc_path}" | grep -Fvq -- "does not claim"; then
    echo "Forbidden Phase 53 closeout evaluation claim: ${forbidden}" >&2
    exit 1
  fi
done

echo "Phase 53 closeout evaluation records Wazuh profile MVP outcomes, subordinate authority posture, verifier evidence, accepted limitations, and bounded Phase 54/55/61 handoff."
