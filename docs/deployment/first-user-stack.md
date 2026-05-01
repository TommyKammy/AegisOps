# Phase 52.9 First-User Stack Overview

- **Status**: Accepted
- **Date**: 2026-05-01
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/phase-52-1-cli-command-contract.md`, `docs/deployment/combined-dependency-matrix.md`, `docs/deployment/compose-generator-contract.md`, `docs/deployment/env-secrets-certs-contract.md`, `docs/deployment/host-preflight-contract.md`, `docs/deployment/demo-seed-contract.md`, `docs/deployment/clean-host-smoke-skeleton.md`, `docs/adr/0011-phase-51-1-replacement-boundary.md`, `docs/phase-51-6-authority-boundary-negative-test-policy.md`
- **Related Issues**: #1063, #1064, #1065, #1068, #1069, #1070, #1071, #1072

This overview is the operator-facing first-user path for the executable Phase 52 stack. It is workflow guidance only. It does not implement installer behavior, Wazuh product profiles, Shuffle product profiles, first-login UI, AI operations, release-candidate behavior, general-availability behavior, or runtime behavior.

## 1. Purpose and Status

Phase 52.9 gives a first user one few-command path through setup, startup, readiness review, demo rehearsal, status inspection, browser access, log review, and shutdown.

AegisOps remains pre-GA. The Phase 52 path is not self-service commercial readiness and is not GA readiness. It is a reviewed setup and rehearsal path that later Phase 53 and Phase 54 work must close for product profiles and operational completeness.

The replacement boundary remains the Phase 51.1 boundary in `docs/adr/0011-phase-51-1-replacement-boundary.md`: AegisOps replaces the SMB operating experience and authoritative record chain above Wazuh and Shuffle, not Wazuh internals, Shuffle internals, or every SIEM/SOAR capability.

## 2. Few-Command Path

Run the first-user stack from a repository checkout with reviewed profile input and documented placeholders. Commands are shown at overview level; later executable issues own the concrete runtime implementation.

| Step | Command | Operator intent | Expected outcome | Troubleshooting link |
| --- | --- | --- | --- | --- |
| 1 | `aegisops init --profile smb-single-node --runtime-env <runtime-env-file>` | Create or validate local first-user setup placeholders. | Runtime config placeholders are present and safe next actions are shown. | [Env, secrets, and certs](env-secrets-certs-contract.md). |
| 2 | `aegisops up --profile smb-single-node --runtime-env <runtime-env-file>` | Start the reviewed stack components available for the selected profile. | Available components start or report explicit `skipped` or `mocked` prerequisites. | [Compose generation](compose-generator-contract.md). |
| 3 | `aegisops doctor --profile smb-single-node --runtime-env <runtime-env-file>` | Check host prerequisites, profile binding, readiness, and boundary warnings. | Docker, Compose, RAM, disk, ports, `vm.max_map_count`, and profile validity are reported as setup evidence. | [Host preflight](host-preflight-contract.md). |
| 4 | `aegisops seed-demo --profile smb-single-node --demo-mode explicit` | Seed reviewed demo-only records for workflow rehearsal. | Demo records are labeled as demo-only and not production truth. | [Demo seed separation](demo-seed-contract.md). |
| 5 | `aegisops status --profile smb-single-node` | Inspect current local stack and first-user readiness. | Current setup state, skipped or mocked profile gaps, and safe next actions are shown. | [Host preflight](host-preflight-contract.md). |
| 6 | `aegisops open --profile smb-single-node` | Print or open the reviewed operator access URL. | The reviewed access path is surfaced without using browser state as workflow truth. | [Compose generation](compose-generator-contract.md). |
| 7 | `aegisops logs --selector <log-selector>` | Review bounded setup logs for the selected stack component. | Redacted, bounded logs are shown as evidence only. | [Env, secrets, and certs](env-secrets-certs-contract.md). |
| 8 | `aegisops down --profile smb-single-node` | Stop managed local components without deleting operator-owned state. | Managed components stop or are already stopped, with retained state paths surfaced. | [Clean-host smoke skeleton](clean-host-smoke-skeleton.md). |

## 3. Troubleshooting Index

Use the scoped troubleshooting contracts before widening the investigation:

- Host preflight failures: `docs/deployment/host-preflight-contract.md` covers missing Docker, missing Compose, low RAM, low disk, port conflicts, Linux `vm.max_map_count`, invalid profile identity, and safe next actions.
- Env, secrets, and cert failures: `docs/deployment/env-secrets-certs-contract.md` covers runtime env files, generated config directories, ignored secret and cert paths, demo token posture, production TLS custody, and placeholder-secret rejection.
- Compose generation failures: `docs/deployment/compose-generator-contract.md` covers generated Compose shape, proxy-only ingress, internal ports, manual-edit rejection, snapshot expectations, and subordinate Docker or Compose state.
- Demo seed separation failures: `docs/deployment/demo-seed-contract.md` covers demo-only labels, fixture provenance, reset boundaries, production exclusion, and fake credential rejection.

## 4. Authority Boundary

First-user docs are operator guidance only. CLI output, generated config, demo data, Docker state, Docker Compose state, host preflight state, Wazuh state, Shuffle state, browser state, UI cache, AI output, tickets, logs, downstream receipts, or operator-facing summaries cannot become workflow truth, source truth, approval truth, execution truth, reconciliation truth, gate truth, release truth, production truth, or closeout truth.

AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, release, gate, and closeout truth.

This overview cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md`.

## 5. Validation Rules

Validation must fail closed when:

- the first-user docs page is missing;
- the README link is missing;
- any required command is missing or out of order;
- troubleshooting links for host preflight, env/secrets/certs, compose generation, or demo seed separation are missing;
- the docs claim self-service commercial readiness, RC readiness, GA readiness, or production readiness;
- demo state, CLI status, Docker state, Compose state, Wazuh state, Shuffle state, AI output, tickets, logs, downstream receipts, browser state, or UI cache is promoted to AegisOps workflow truth;
- the Phase 51.1 replacement boundary and Phase 51.6 authority-boundary policy citations are missing; or
- publishable guidance uses workstation-local absolute paths instead of repo-relative commands, documented env vars, or placeholders.

## 6. Forbidden Claims

- AegisOps is GA ready.
- AegisOps is self-service commercial ready.
- Phase 52 completes RC readiness.
- Phase 52 completes GA readiness.
- Demo data is workflow truth.
- Demo data is production truth.
- CLI status is workflow truth.
- Docker status is AegisOps workflow truth.
- Docker Compose status is AegisOps workflow truth.
- Wazuh state is AegisOps workflow truth.
- Shuffle state is AegisOps workflow truth.
- AI output is AegisOps workflow truth.
- Tickets are AegisOps workflow truth.
- Logs are authoritative workflow truth.
- This overview implements Wazuh product profiles.
- This overview implements Shuffle product profiles.

## 7. Validation

Run `bash scripts/verify-phase-52-9-first-user-stack-docs.sh`.

Run `bash scripts/test-verify-phase-52-9-first-user-stack-docs.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1072 --config <supervisor-config-path>`.

The verifier must fail when first-user docs are missing, when the few-command path omits a command, when troubleshooting links are absent, when Phase 52 is described as self-service commercial, RC, or GA readiness, when demo data or CLI status is promoted to workflow truth, when Phase 51 boundary citations are missing, or when publishable guidance uses workstation-local absolute paths.

## 8. Non-Goals

- No Phase 52 runtime behavior is implemented by this overview.
- No Wazuh product profile, Shuffle product profile, guided first-login UI, AI operation, RC behavior, GA behavior, production supportability, or commercial launch claim is approved here.
- No CLI output, generated config, demo data, Docker state, Docker Compose state, host preflight output, Wazuh state, Shuffle state, AI output, ticket, log text, downstream receipt, browser state, UI cache, or operator-facing summary becomes authoritative AegisOps truth.
