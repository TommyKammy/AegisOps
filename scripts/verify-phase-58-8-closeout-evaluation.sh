#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"

doc_path="docs/phase-58-closeout-evaluation.md"
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
  echo "Missing Phase 58 closeout evaluation: ${doc_path}" >&2
  exit 1
fi

if [[ ! -s "${readme_path}" ]]; then
  echo "Missing README for Phase 58 closeout link check: README.md" >&2
  exit 1
fi

require_phrase "${readme_path}" "- [Phase 58.8 closeout evaluation](docs/phase-58-closeout-evaluation.md)" "README canonical cross-phase boundary bullet"
require_phrase "${readme_path}" "The Phase 58.8 closeout evaluation is defined by the [Phase 58.8 closeout evaluation](docs/phase-58-closeout-evaluation.md)." "README Product positioning reference"

required_phrases=()
while IFS= read -r phrase; do
  required_phrases+=("${phrase}")
done <<'EOF'
# Phase 58 Closeout Evaluation
**Status**: Accepted as supportability MVP evidence and handoff baseline; Phase 59, Phase 60, and Phase 66 can consume the bounded Phase 58 doctor, backup, restore dry-run, upgrade/rollback planning, support bundle, and supportability summary evidence with explicit retained blockers.
**Related Issues**: #1235, #1236, #1237, #1238, #1239, #1240, #1241, #1242, #1243
Phase 58 is accepted as the Doctor / Backup / Restore / Upgrade / Supportability MVP before AI daily operations, reporting breadth, SOAR breadth, RC, Beta, GA, or commercial replacement expansion.
AegisOps control-plane records remain authoritative for alert, case, evidence, recommendation, action review, approval, action request, delegation, execution receipt, reconciliation, audit event, limitation, release, gate, restore, workflow, and closeout truth.
Doctor output, backup manifests, restore dry-run output, upgrade/rollback plans, support bundles, supportability summaries, support links, verifier output, issue-lint output, and operator-facing diagnostic text remain subordinate supportability or validation evidence.
The Phase 58 supportability surfaces must reject automatic repair authority, support output as workflow truth, support output as release or gate truth, restore dry-run as live restore completion, backup manifest as restore success, upgrade/rollback plans as live mutation, support bundles as customer support truth, support collaborator authority expansion, stale or missing evidence success inference, secret leakage, workstation-local path leakage, mixed-snapshot bundle claims, and Phase 59/60/66 completion claims.
This closeout does not claim Phase 59 AI daily operations is complete, Phase 60 audit or reporting breadth is complete, Phase 66 RC proof is complete, AegisOps is Beta, RC, GA, self-service commercially ready, or a commercial replacement for every SIEM/SOAR capability.
| #1235 | Epic: Phase 58 Doctor / Backup / Restore / Upgrade / Supportability MVP | Open until #1243 lands; accepted when this closeout, focused verifier, doctor/backup/restore/supportability tests, path hygiene, maintainability hotspot verifier, and issue-lint pass. |
| #1236 | Phase 58.1 Add aegisops doctor contract | Closed.
| #1237 | Phase 58.2 Add doctor explanation outputs | Closed.
| #1238 | Phase 58.3 Add backup command contract | Closed.
| #1239 | Phase 58.4 Add restore dry-run contract | Closed.
| #1240 | Phase 58.5 Add upgrade plan and rollback plan contracts | Closed.
| #1241 | Phase 58.6 Add support bundle and redaction contract | Closed.
| #1242 | Phase 58.7 Add supportability UI/CLI summary | Closed.
| #1243 | Phase 58.8 Phase 58 closeout evaluation | Open until this document and focused closeout verifier land. |
| #1244 | Phase 58.1 doctor contract | Merged doctor contract runtime, CLI/HTTP route, and focused negative tests. |
| #1245 | Phase 58.2 doctor explanation outputs | Merged bounded explanations, safe next steps, and support links for doctor output. |
| #1246 | Phase 58.3 backup command contract | Merged backup custody manifest behavior, tests, and contract verifier. |
| #1247 | Phase 58.4 restore dry-run contract | Merged restore dry-run preflight behavior, tests, and contract verifier. |
| #1248 | Phase 58.5 upgrade and rollback plan contract | Merged plan-contract documentation and verifier tests; no live upgrade or rollback execution. |
| #1249 | Phase 58.6 support bundle and redaction contract | Merged support-bundle redaction contract and negative verifier tests. |
| #1250 | Phase 58.7 supportability UI/CLI summary | Merged read-only supportability summary CLI/runtime/tests; no separate new UI route is claimed by this closeout. |
| Current branch | Phase 58.8 closeout evaluation | Adds this closeout document, closeout verifier, verifier negative tests, and README cross-reference before the final closeout PR. |
| Doctor output | Readiness details existed, but there was no product-facing doctor contract for common support states. | Phase 58.1 defines the read-only doctor contract across control plane, Wazuh, Shuffle, database, proxy, stale source, AI enablement, evidence availability, workflow template, and execution receipt families. |
| Doctor explanations | Diagnostic output did not consistently provide bounded operator guidance for degraded or unavailable support states. | Phase 58.2 adds explanations, safe next steps, support links, and recommended next-step rendering without repair authority or sensitive-data leakage. |
| Backup custody | Record-chain backup existed as recovery data, but the product-facing custody posture was not explicit. | Phase 58.3 adds a backup manifest with schema version, source revision, profile, timestamp, record-family counts, redaction expectations, and non-authority uses. |
| Restore dry-run | Restore validation existed, but there was no explicit read-only preflight command for reviewed backup payloads. | Phase 58.4 adds dry-run preflight evidence that validates payload shape, provenance, source/profile binding, staleness, duplicates, and clean restore target requirements before live restore review. |
| Upgrade and rollback planning | Upgrade and rollback evidence was not bounded as a reviewed plan contract. | Phase 58.5 defines required plan fields and fail-closed states while leaving live upgrade, rollback, scheduler, package migration, and substrate mutation out of scope. |
| Support bundle redaction | Customer-safe support bundle boundaries were not materialized as a contract. | Phase 58.6 defines allowed contents, forbidden contents, redaction rules, retention prerequisites, authority boundaries, and mixed-snapshot rejection for future support bundles. |
| Supportability UI/CLI summary | Operators had separate supportability signals but no bounded summary surface. | Phase 58.7 adds a read-only CLI summary that rereads doctor, backup, restore dry-run, upgrade/rollback, and support-bundle posture for the reviewed support diagnostics role; this closeout does not claim a new separate UI route. |
`docs/phase-58-1-aegisops-doctor-contract.md`
`control-plane/aegisops/control_plane/runtime/doctor_contract.py`
`control-plane/aegisops/control_plane/runtime/supportability_summary.py`
`control-plane/aegisops/control_plane/api/cli.py`
`control-plane/aegisops/control_plane/api/http_runtime_surface.py`
`control-plane/tests/test_phase58_1_doctor_contract.py`
`control-plane/tests/test_cli_inspection_restore_readiness.py`
`control-plane/tests/test_service_restore_backup_codec.py`
`docs/phase-58-3-backup-command-contract.md`
`docs/phase-58-4-restore-dry-run-contract.md`
`docs/phase-58-5-upgrade-rollback-plan-contract.md`
`docs/phase-58-6-support-bundle-redaction-contract.md`
`scripts/verify-phase-58-3-backup-command-contract.sh`
`scripts/test-verify-phase-58-3-backup-command-contract.sh`
`scripts/verify-phase-58-4-restore-dry-run-contract.sh`
`scripts/test-verify-phase-58-4-restore-dry-run-contract.sh`
`scripts/verify-phase-58-5-upgrade-rollback-plan-contract.sh`
`scripts/test-verify-phase-58-5-upgrade-rollback-plan-contract.sh`
`scripts/verify-phase-58-6-support-bundle-redaction-contract.sh`
`scripts/test-verify-phase-58-6-support-bundle-redaction-contract.sh`
`docs/phase-58-closeout-evaluation.md`
`scripts/verify-phase-58-8-closeout-evaluation.sh`
`scripts/test-verify-phase-58-8-closeout-evaluation.sh`
`python3 -m unittest control-plane.tests.test_phase58_1_doctor_contract`
`python3 -m unittest control-plane.tests.test_cli_inspection_restore_readiness.CliInspectionRestoreReadinessTests.test_backup_command_renders_manifest_custody_metadata_without_secrets`
`python3 -m unittest control-plane.tests.test_cli_inspection_restore_readiness.CliInspectionRestoreReadinessTests.test_restore_dry_run_command_renders_preflight_evidence_without_mutation`
`python3 -m unittest control-plane.tests.test_cli_inspection_restore_readiness.CliInspectionRestoreReadinessTests.test_supportability_summary_cli_renders_bounded_state_without_mutation`
`python3 -m unittest control-plane.tests.test_service_restore_backup_codec`
`bash scripts/verify-phase-58-3-backup-command-contract.sh`
`bash scripts/test-verify-phase-58-3-backup-command-contract.sh`
`bash scripts/verify-phase-58-4-restore-dry-run-contract.sh`
`bash scripts/test-verify-phase-58-4-restore-dry-run-contract.sh`
`bash scripts/verify-phase-58-5-upgrade-rollback-plan-contract.sh`
`bash scripts/test-verify-phase-58-5-upgrade-rollback-plan-contract.sh`
`bash scripts/verify-phase-58-6-support-bundle-redaction-contract.sh`
`bash scripts/test-verify-phase-58-6-support-bundle-redaction-contract.sh`
`bash scripts/verify-maintainability-hotspots.sh`
`bash scripts/verify-publishable-path-hygiene.sh`
`bash scripts/verify-phase-58-8-closeout-evaluation.sh`
`bash scripts/test-verify-phase-58-8-closeout-evaluation.sh`
Doctor tests reject missing or malformed readiness signals, missing Wazuh prerequisites, missing execution receipt success inference, and degraded receipt reconciliation as success.
Doctor explanation tests require bounded `explanation`, `safe_next_steps`, and `support_link` output for degraded or unavailable families without automatic repair authority.
Backup tests reject invalid backup paths and prove the backup manifest omits plaintext secrets, credential DSNs, customer-private raw payload posture, and workstation-local path claims.
Restore dry-run tests reject stale or failed preflight input, keep `read_only` true, keep `mutates_authoritative_records` false, and prove durable restore targets remain clean on dry-run paths.
Upgrade and rollback contract verifier tests reject silent upgrade claims, unsafe rollback claims, missing owner evidence, missing trigger evidence, placeholder evidence, plan-as-release-truth claims, substrate mutation claims, incompatible version claims, missing backup evidence, and workstation-local absolute path guidance.
Support bundle redaction verifier tests reject secret-looking values, authorization headers, credential URLs, cert material, private keys, workstation-local paths, private payloads, private ticket content, support bundle as workflow truth, support collaborator operator expansion, and missing redaction manifest coverage.
Supportability summary tests deny unsupported roles, reject invalid restore input, surface degraded doctor state without inference, keep summary claims false for workflow/release/gate/restore/closeout truth, and prove the summary does not mutate authoritative records.
Maintainability hotspot verification preserves the existing hotspot baseline rather than hiding new growth.
Publishable path hygiene rejects workstation-local absolute paths in publishable tracked Markdown, scripts, docs, and tests.
node <codex-supervisor-root>/dist/index.js issue-lint 1235 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1236 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1237 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1238 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1239 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1240 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1241 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1242 --config <supervisor-config-path>
node <codex-supervisor-root>/dist/index.js issue-lint 1243 --config <supervisor-config-path>
execution_ready=yes
missing_required=none
missing_recommended=none
metadata_errors=none
high_risk_blocking_ambiguity=none
Phase 58 does not implement Phase 59 AI governance expansion, AI daily-operations breadth, agent/tool registry posture, trace governance expansion, citation requirements, AI approval authority, AI execution authority, or AI reconciliation authority.
Phase 58 does not implement Phase 60 audit export administration breadth, commercial reporting breadth, executive reporting completeness, compliance reporting completeness, report custody, retention execution, or production report templates.
Phase 58 does not implement broad SOAR workflow catalog coverage, broad SIEM source marketplace breadth, marketplace breadth, every action-family expectation, or standalone Wazuh or Shuffle replacement.
Phase 58 does not implement live upgrade execution, live rollback execution, silent upgrade, automatic rollback, schema migration, package migration, substrate mutation, restore execution, restore success proof, support portal workflow, remote support upload, or direct backend access for support collaborators.
Phase 58 does not implement Phase 66 RC proof, RC readiness, GA readiness, Beta readiness, self-service commercial readiness, or commercial replacement readiness.
Phase 58 does not make doctor output, backup manifests, restore dry-run output, upgrade/rollback plans, support bundles, supportability summaries, support links, verifier output, issue-lint output, browser state, local cache, CLI output, HTTP output, or operator-facing summaries authoritative AegisOps truth.
Phase 59 can consume the Phase 58 doctor explanation pattern, degraded AI posture reporting, support links, negative-authority vocabulary, and supportability summary boundaries as operational context.
Phase 58 does not complete Phase 59 AI daily operations.
Phase 60 can consume the Phase 58 backup custody manifest, restore dry-run evidence, support bundle redaction contract, and supportability summary posture as report design inputs.
Phase 58 does not complete Phase 60 audit or reporting breadth.
Phase 66 can consume the Phase 58 supportability MVP as one prerequisite evidence packet for RC proof.
Phase 58 does not complete Phase 66 RC proof.
This closeout is release and planning evidence only.
EOF

for phrase in "${required_phrases[@]}"; do
  require_phrase "${absolute_doc_path}" "${phrase}" "required Phase 58 closeout term in ${doc_path}"
done

mac_home_prefix="$(printf '/%s/' 'Users')"
unix_home_prefix="$(printf '/%s/' 'home')"
windows_backslash_prefix="$(printf '[A-Za-z]:\\\\%s\\\\' 'Users')"
windows_slash_prefix="$(printf '[A-Za-z]:/%s/' 'Users')"
absolute_path_boundary='(^|[[:space:]`"'\''(<[{=])'
absolute_path_pattern="${absolute_path_boundary}(${mac_home_prefix}|${unix_home_prefix}|${windows_backslash_prefix}|${windows_slash_prefix})[^ <\`]+"
if grep -Eq -- "${absolute_path_pattern}" "${absolute_doc_path}" "${readme_path}"; then
  echo "Forbidden Phase 58 closeout evaluation: workstation-local absolute path detected" >&2
  exit 1
fi

allowed_non_claim_line="This closeout does not claim Phase 59 AI daily operations is complete, Phase 60 audit or reporting breadth is complete, Phase 66 RC proof is complete, AegisOps is Beta, RC, GA, self-service commercially ready, or a commercial replacement for every SIEM/SOAR capability."

for forbidden in \
  "Phase 59 AI daily operations is complete" \
  "Phase 60 audit or reporting breadth is complete" \
  "Phase 66 RC proof is complete" \
  "AegisOps is Beta" \
  "AegisOps is RC" \
  "AegisOps is GA" \
  "AegisOps is self-service commercially ready" \
  "AegisOps is a commercial replacement for every SIEM/SOAR capability" \
  "Phase 58 proves Beta readiness" \
  "Phase 58 proves RC readiness" \
  "Phase 58 proves GA readiness" \
  "Phase 58 proves commercial replacement readiness" \
  "Doctor output is workflow truth" \
  "Doctor output can repair state" \
  "Backup manifest proves restore success" \
  "Backup manifest is restore truth" \
  "Restore dry-run proves live restore completion" \
  "Restore dry-run is restore truth" \
  "Upgrade plan executes live upgrades" \
  "Rollback plan executes live rollbacks" \
  "Support bundle is customer support truth" \
  "Support bundle is workflow truth" \
  "Support collaborator has operator authority" \
  "Supportability summary is release truth" \
  "Supportability summary is closeout truth" \
  "Supportability summary completes Phase 59"; do
  if grep -Fxv -- "${allowed_non_claim_line}" "${absolute_doc_path}" | grep -Fq -- "${forbidden}"; then
    echo "Forbidden Phase 58 closeout evaluation claim: ${forbidden}" >&2
    exit 1
  fi
done

echo "Phase 58 closeout evaluation records supportability MVP outcomes, subordinate authority posture, verifier evidence, accepted limitations, and bounded Phase 59/60/66 handoff."
