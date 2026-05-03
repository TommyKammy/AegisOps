#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"

doc_path="docs/phase-55-closeout-evaluation.md"
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
  echo "Missing Phase 55 closeout evaluation: ${doc_path}" >&2
  exit 1
fi

if [[ ! -s "${readme_path}" ]]; then
  echo "Missing README for Phase 55 closeout link check: README.md" >&2
  exit 1
fi

require_phrase "${readme_path}" "[Phase 55.7 closeout evaluation](docs/phase-55-closeout-evaluation.md)" "README Phase 55.7 closeout link"

required_phrases=()
while IFS= read -r phrase; do
  required_phrases+=("${phrase}")
done <<'EOF'
# Phase 55 Closeout Evaluation
**Status**: Accepted as guided first-user journey evidence and handoff baseline; Phase 56, Phase 57, Phase 58, Phase 60, and Phase 66 can consume the bounded Phase 55 first-user journey with explicit retained blockers.
**Related Issues**: #1175, #1176, #1177, #1178, #1179, #1180, #1181, #1182
Phase 55 is accepted as the guided first-user journey evidence baseline for the `smb-single-node` profile.
AegisOps control-plane records remain authoritative for alert, case, evidence, recommendation, action review, approval, action request, delegation, execution receipt, reconciliation, audit, limitation, release, gate, and closeout truth.
First-user docs, checklist state, demo seed records, demo reset output, demo report export output, empty-state copy, failure-state copy, browser state, UI cache, Wazuh state, Shuffle state, AI output, tickets, verifier output, and issue-lint output remain subordinate context.
Demo records and demo report exports are rehearsal evidence only.
This closeout does not claim Phase 56 daily SOC workbench is complete, Phase 57 packaging is complete, Phase 58 supportability is complete, Phase 60 audit or reporting breadth is complete, Phase 62 SOAR breadth is complete, Phase 66 RC proof is complete, AegisOps is Beta, RC, GA, self-service commercially ready, or a commercial replacement for every SIEM/SOAR capability.
| #1175 | Epic: Phase 55 Guided First-User Journey | Open until #1182 lands; accepted when this closeout, focused verifier, Phase 55 verifiers, focused first-user/UI/demo tests, path hygiene, and issue-lint pass. |
| #1176 | Phase 55.1 first-user journey and first-30-minutes docs | Closed.
| #1177 | Phase 55.2 first-login checklist UI contract | Closed.
| #1178 | Phase 55.3 demo seed record family bundle | Closed.
| #1179 | Phase 55.4 demo reset and mode separation | Closed.
| #1180 | Phase 55.5 empty-state and failure-state copy | Closed.
| #1181 | Phase 55.6 first-user report export skeleton | Closed.
| #1182 | Phase 55.7 Phase 55 closeout evaluation | Open until this document and focused closeout verifier land. |
| First-user docs | Phase 52 first-user stack docs described the few-command setup path but did not provide a workflow-first guided journey. | Phase 55.1 documents the first-user flow from stack health, seeded queue, sample Wazuh alert, case, evidence, AI summary, action review, receipt, reconciliation, and report export. |
| First-login checklist | Operator UI did not have the Phase 55 checklist surface. | Phase 55.2 renders the checklist from backend authoritative records only and rejects browser cache, wrong record family, duplicate, missing, unsupported, or malformed checklist state. |
| Demo seed bundle | Phase 52.7 described demo seed expectations without the Phase 55 linked family bundle. | Phase 55.3 adds a linked demo family spanning Wazuh alert, analytic signal, AegisOps alert, case, evidence, recommendation, action review, execution receipt, and reconciliation. |
| Demo reset | Demo reset behavior was not bounded for repeatable first-user rehearsal. | Phase 55.4 requires demo-only selectors, stable identifiers, live-record preservation, and fail-closed rejection of production cleanup or backup/restore claims. |
| Failure states | Checklist failure copy was not enumerated for common first-user blockers. | Phase 55.5 adds bounded copy for missing Wazuh, missing Shuffle, missing secrets, port conflict, missing IdP, missing seed data, and protected-surface denial without authorizing repair or supportability completion. |
| Demo report export | The first-user journey lacked a bounded report export skeleton. | Phase 55.6 defines demo-labeled report export output with direct demo record references, unavailable follow-up handling, secret hygiene, and commercial-reporting guardrails. |
`docs/getting-started/first-user-journey.md`
`docs/getting-started/first-30-minutes.md`
`apps/operator-ui/src/app/operatorConsolePages/firstLoginChecklistPages.tsx`
`apps/operator-ui/src/app/OperatorRoutes.firstLoginChecklist.testSuite.tsx`
`docs/deployment/demo-seed-contract.md`
`docs/deployment/fixtures/demo-seed/valid-demo-seed.json`
`docs/deployment/demo-reset-mode-separation.md`
`docs/getting-started/first-user-demo-report-export.md`
`docs/phase-55-closeout-evaluation.md`
`scripts/verify-phase-55-7-closeout-evaluation.sh`
`scripts/test-verify-phase-55-7-closeout-evaluation.sh`
`bash scripts/verify-phase-55-1-first-user-journey-docs.sh`
`bash scripts/test-verify-phase-55-1-first-user-journey-docs.sh`
`npm run test --workspace @aegisops/operator-ui -- OperatorRoutes`
`bash scripts/verify-phase-52-7-demo-seed-contract.sh`
`bash scripts/test-verify-phase-52-7-demo-seed-contract.sh`
`bash scripts/verify-phase-55-4-demo-reset-mode-separation.sh`
`bash scripts/test-verify-phase-55-4-demo-reset-mode-separation.sh`
`bash scripts/verify-phase-55-6-first-user-report-export-skeleton.sh`
`bash scripts/test-verify-phase-55-6-first-user-report-export-skeleton.sh`
`bash scripts/verify-publishable-path-hygiene.sh`
`bash scripts/verify-phase-55-7-closeout-evaluation.sh`
`bash scripts/test-verify-phase-55-7-closeout-evaluation.sh`
node <codex-supervisor-root>/dist/index.js issue-lint 1175 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1176 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1177 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1178 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1179 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1180 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1181 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1182 --config <supervisor-config-path>
execution_ready=yes
missing_required=none
missing_recommended=none
metadata_errors=none
high_risk_blocking_ambiguity=none
Phase 55 does not implement Phase 56 daily SOC workbench breadth, queue optimization, production daily operations completeness, or analyst productivity breadth.
Phase 55 does not implement Phase 57 packaging, installer completeness, release packaging, or customer-ready distribution.
Phase 55 does not implement Phase 58 supportability, break-glass support workflows, backup/restore support operations, support bundles, support diagnostics, or customer support operations.
Phase 55 does not implement Phase 60 audit export administration, commercial reporting breadth, executive reporting completeness, or compliance reporting completeness.
Phase 55 does not implement Phase 62 SOAR breadth, broad workflow catalog coverage, marketplace work, or every action-family expectation.
Phase 55 does not implement Phase 66 RC proof, RC readiness, GA readiness, Beta readiness, or self-service commercial readiness.
Phase 56 can consume the Phase 55 first-user journey as the bounded workflow sequence for daily SOC workbench design.
Phase 55 does not complete Phase 56 daily SOC workbench.
Phase 57 can consume the Phase 55 first-user journey as one package-entry acceptance fixture.
Phase 55 does not complete Phase 57 packaging.
Phase 58 can consume the Phase 55 failure-state copy and reset/report boundaries as supportability inputs.
Phase 55 does not complete Phase 58 supportability.
Phase 60 can consume the Phase 55 demo report export skeleton as a demo-only export shape.
Phase 55 does not complete Phase 60 audit or reporting breadth.
Phase 66 can consume the Phase 55 first-user journey as one prerequisite evidence packet for RC proof.
Phase 55 does not complete Phase 66 RC proof.
This closeout is release and planning evidence only.
EOF

for phrase in "${required_phrases[@]}"; do
  require_phrase "${absolute_doc_path}" "${phrase}" "required Phase 55 closeout term in ${doc_path}"
done

mac_home_prefix="$(printf '/%s/' 'Users')"
unix_home_prefix="$(printf '/%s/' 'home')"
windows_backslash_prefix="$(printf '[A-Za-z]:\\\\%s\\\\' 'Users')"
windows_slash_prefix="$(printf '[A-Za-z]:/%s/' 'Users')"
absolute_path_pattern="(${mac_home_prefix}|${unix_home_prefix}|${windows_backslash_prefix}|${windows_slash_prefix})[^ <\`]+"
if grep -Eq -- "${absolute_path_pattern}" "${absolute_doc_path}" "${readme_path}"; then
  echo "Forbidden Phase 55 closeout evaluation: workstation-local absolute path detected" >&2
  exit 1
fi

allowed_non_claim_line="This closeout does not claim Phase 56 daily SOC workbench is complete, Phase 57 packaging is complete, Phase 58 supportability is complete, Phase 60 audit or reporting breadth is complete, Phase 62 SOAR breadth is complete, Phase 66 RC proof is complete, AegisOps is Beta, RC, GA, self-service commercially ready, or a commercial replacement for every SIEM/SOAR capability."

for forbidden in \
  "Phase 56 daily SOC workbench is complete" \
  "Phase 57 packaging is complete" \
  "Phase 58 supportability is complete" \
  "Phase 60 audit or reporting breadth is complete" \
  "Phase 62 SOAR breadth is complete" \
  "Phase 66 RC proof is complete" \
  "AegisOps is Beta" \
  "AegisOps is RC" \
  "AegisOps is GA" \
  "AegisOps is self-service commercially ready" \
  "AegisOps is a commercial replacement for every SIEM/SOAR capability" \
  "Phase 55 proves Beta readiness" \
  "Phase 55 proves RC readiness" \
  "Phase 55 proves GA readiness" \
  "Phase 55 proves commercial replacement readiness" \
  "Demo records are production truth" \
  "Demo report exports are production truth" \
  "Demo reset output is production truth" \
  "Checklist UI state is workflow truth" \
  "Browser state is workflow truth" \
  "Wazuh state is AegisOps workflow truth" \
  "Shuffle state is AegisOps workflow truth"; do
  if grep -Fxv -- "${allowed_non_claim_line}" "${absolute_doc_path}" | grep -Fq -- "${forbidden}"; then
    echo "Forbidden Phase 55 closeout evaluation claim: ${forbidden}" >&2
    exit 1
  fi
done

echo "Phase 55 closeout evaluation records first-user journey outcomes, subordinate authority posture, verifier evidence, accepted limitations, and bounded Phase 56/57/58/60/66 handoff."
