# AegisOps Phase 61.1 Minimum Source Catalog Contract

## 1. Purpose

Phase 61 defines the minimum source catalog that Phase 61.1 accepts as reviewed source families for bounded SIEM replacement posture. It documents the required evidence, owner, source-health, authority, and limitation fields for each family before downstream detection and operator workflows can depend on it.

This contract keeps Wazuh as the detection substrate and AegisOps as workflow authority.

## 2. Approved Source Catalog Entries

| Source Family | Reviewed owner | Authority posture | Evidence linkage | Source-health requirements | Explicit limitations |
| ---- | ---- | ---- | ---- | ---- | ---- |
| `wazuh_detection` (Wazuh manager and agent origin telemetry) | IT Operations, Information Systems Department | Wazuh alerts remain a reviewed detection substrate only. Wazuh status, manager status, or decoder status is subordinate evidence and does not become AegisOps alert, case, approval, action request, execution, reconciliation, audit, release, gate, or closeout truth. | Required fixtures: `control-plane/tests/fixtures/wazuh/agent-origin-alert.json`, `control-plane/tests/fixtures/wazuh/manager-origin-alert.json`; parser/provenance fields `rule.id`, `rule.level`, `rule.description`, `decoder.name`, `location`, `timestamp`; required reviewed correlation fields include accountable source identity, `agent.id`/`manager.name`, and `data.source_family`. | If `source_family` is `wazuh_detection`, adapter-level required provenance fields must remain present and verified (`data.product_profile`, `data.source_system == "wazuh"`, `data.source_id`, `data.wazuh_manager_id`, `data.wazuh_rule_id`, `data.wazuh_rule_level`, `data.ingest_channel`, `data.admission_channel`, `data.secret_custody_reference`, `data.proxy_route`, `data.reviewed_by`, and `data.event_timestamp`). | Not a source-marketplace claim. No standalone SIEM replacement, no raw Wazuh-to-workflow truth shortcuts, no production onboarding approval, and no direct source-owned workflow authority in this catalog slice. |
| `github_audit` | IT Operations, Information Systems Department | `reviewed_context.source.source_family = github_audit` is source evidence context only. It supports analyst workload and detection prerequisites but does not become AegisOps workflow truth. | Onboarding package: `docs/source-families/github-audit/onboarding-package.md`; reviewed fixture: `control-plane/tests/fixtures/wazuh/github-audit-alert.json`; triage posture: `docs/source-families/github-audit/analyst-triage-runbook.md`. | Source-family acceptance requires explicit `source_family = "github_audit"`; accepted evidence coverage must include accountable source identity, actor identity, target identity, repository/org context, privilege-change context, and provenance fields. Missing ownership or malformed payload fields must keep the path rejected or reviewed as exception only. | Detection activation remains blocked until separate detector review and rollout review approve each candidate. No raw GitHub API actioning, no non-audit GitHub telemetry family expansion, and no claim of production-wide source marketplace scope. |
| `microsoft_365_audit` | IT Operations, Information Systems Department | `reviewed_context.source.source_family = microsoft_365_audit` is reviewed evidence context only. It cannot grant AegisOps alert/case/action/reconciliation truth by itself. | Onboarding package: `docs/source-families/microsoft-365-audit/onboarding-package.md`; reviewed fixture: `control-plane/tests/fixtures/wazuh/microsoft-365-audit-alert.json`; triage posture: `docs/source-families/microsoft-365-audit/analyst-triage-runbook.md`. | Source-system and parser linkage must preserve tenant context, actor/target identity, authentication context, and parser/provenance linkage (rule/decode/time path) before detections may treat this family as a prerequisite. | This family remains `schema-reviewed` for Phase 61.1 and does not become automatically detection-ready for all Microsoft 365 workloads. No non-audit Microsoft 365 telemetry family expansion, no source-native status as workflow truth, no raw source actioning. |
| `entra_id` | IT Operations, Information Systems Department | `reviewed_context.source.source_family = entra_id` is reviewed evidence context only. It remains advisory source context for workflow and case admission logic and never source truth. | Onboarding package: `docs/source-families/entra-id/onboarding-package.md`; reviewed fixture: `control-plane/tests/fixtures/wazuh/entra-id-alert.json`; triage posture: `docs/source-families/entra-id/analyst-triage-runbook.md`. | Source-system and parser linkage must preserve tenant/context + actor/target + request/correlation evidence and Wazuh provenance before any broader detection dependency is allowed. | Phase 61.1 accepts it as detection-ready but only within bounded evidence posture; no directory/action authority bypass, no non-audit Entra ID telemetry expansion, and no source-native workflow truth claim. |
| `windows_security_endpoint` (Windows endpoint detection-ready path) | IT Operations, Information Systems Department | This is a Windows endpoint path entry mapped to `docs/source-families/windows-security-and-endpoint/onboarding-package.md`; it remains an evidence-path contract and does not grant direct workflow authority. | Onboarding package: `docs/source-families/windows-security-and-endpoint/onboarding-package.md`; reviewed fixtures: `ingest/replay/windows-security-and-endpoint/raw/*`, `ingest/replay/windows-security-and-endpoint/normalized/*`. | Windows endpoint path must preserve host identity, event classification, provenance, and timestamp semantics with explicit edge-case handling for missing actor and forwarded-timestamp cases before detections depend on those fields. | This family is bounded by explicit gaps: parser/version maturity, full process/network coverage, and remote-origin event continuity are out of scope in this slice. No broad endpoint market, no direct host-remediation actioning, and no workflow-truth authority inference from endpoint surface alone. |

## 3. Catalog Boundedness Rules

- This catalog must stay bounded to the five families above.
- No raw SIEM replacement.
- No raw Wazuh replacement of AegisOps workflow truth.
- The catalog must reject claims that broaden into marketplace, replacement, or product-scope coverage.
- No broad SIEM source marketplace expansion.
- No broad source-marketplace expansion.
- Source-native alerts, statuses, and parser fields remain subordinate evidence and cannot replace AegisOps record-chain truth.
- Missing owner, missing source-health evidence, malformed provenance, or missing authority posture blocks admission of catalog claims for the slice.

## 4. Out-of-scope for Phase 61.1

- Phase 62 automation breadth, Phase 66 RC proof, Beta/RC/GA, commercial replacement readiness, raw SIEM replacement, raw Wazuh replacement of AegisOps workflow truth, and multi-site source management.
- Source profile runtime onboarding, live credentials, and live source enrollment approval.

## 5. Validation

Run the Phase 61.1 source catalog verifier and focused tests before widening detector slices.

- Run `bash scripts/verify-phase-61-1-source-catalog-contract.sh`.
- Run `python3 -m unittest control-plane.tests.test_phase61_source_catalog_contract`.
- Run `bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh`.
- Run `python3 -m unittest control-plane.tests.test_cross_boundary_negative_e2e_validation` with test subset for Wazuh source-bridge boundary failures.
- Run `bash scripts/verify-publishable-path-hygiene.sh`.
