# Phase 52.8 Clean-Host Smoke Skeleton

- **Status**: Accepted
- **Date**: 2026-05-01
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/phase-52-1-cli-command-contract.md`, `docs/deployment/compose-generator-contract.md`, `docs/deployment/env-secrets-certs-contract.md`, `docs/deployment/host-preflight-contract.md`, `docs/deployment/demo-seed-contract.md`
- **Related Issues**: #1063, #1064, #1067, #1068, #1069, #1070, #1071

This contract defines a clean-host smoke skeleton for the executable first-user stack only. It does not implement full stack startup, Wazuh product profiles, Shuffle product profiles, the first-user guided UI journey, release-candidate behavior, general-availability behavior, or runtime behavior.

## 1. Purpose

Phase 52.8 gives later executable-stack work one repo-owned smoke shape for the first user path:

`init -> up -> doctor -> seed-demo`

The smoke may run entirely from reviewed fixtures until actual profile-backed commands exist. Mocked and skipped states are expected in this phase, but the smoke must surface them as incomplete prerequisites instead of reporting a successful full stack.

## 2. Authority Boundary

Smoke output is validation evidence only. Smoke output, fixture output, Docker state, Docker Compose state, generated config state, host preflight state, demo seed output, Wazuh state, Shuffle state, browser state, UI cache, logs, tickets, downstream receipts, or operator-facing summaries cannot become workflow truth, source truth, approval truth, execution truth, reconciliation truth, gate truth, release truth, production truth, or closeout truth.

AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, release, gate, and closeout truth.

This contract cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md`.

## 3. Smoke Sequence

| Step | Command | Required contract reference | Expected skeleton state | Required evidence role |
| --- | --- | --- | --- | --- |
| 1 | `init` | Phase 52.1 CLI command contract and Phase 52.5 env/secrets/certs contract. | `mocked` or `skipped` until generated runtime config is implemented. | Setup fixture evidence only. |
| 2 | `up` | Phase 52.1 CLI command contract and Phase 52.4 compose generator contract. | `mocked` or `skipped` until stack startup and product profiles are implemented. | Compose/runtime posture fixture evidence only. |
| 3 | `doctor` | Phase 52.1 CLI command contract and Phase 52.6 host preflight contract. | `mocked` or `skipped` until live host preflight is implemented. | Host preflight fixture evidence only. |
| 4 | `seed-demo` | Phase 52.1 CLI command contract and Phase 52.7 demo seed contract. | `mocked` or `skipped` until demo seed command execution is implemented. | Demo rehearsal fixture evidence only. |

The sequence order is fixed. A fixture that omits a command, repeats a command, reorders commands, or runs `seed-demo` before `doctor` fails validation.

## 4. Mocked and Skipped States

| State | Meaning | Required follow-up |
| --- | --- | --- |
| `mocked` | The smoke used a reviewed fixture or test double instead of a live clean host. | Replace the mocked step with a real implementation in the later owning phase named by the fixture. |
| `skipped` | The smoke intentionally did not attempt a profile-backed operation because a reviewed prerequisite is absent. | Close the missing prerequisite before claiming full stack startup or production readiness. |

Each mocked or skipped step must include the command, the missing prerequisite, the later closing phase, and a safe next action. A mocked or skipped step cannot be summarized as `ok`, full-stack success, production readiness, RC readiness, GA readiness, gate truth, release truth, or closeout truth.

## 5. Required Contract References

The smoke skeleton must reference:

- Phase 52.1 CLI command contract: `docs/phase-52-1-cli-command-contract.md`.
- Phase 52.4 compose generator contract: `docs/deployment/compose-generator-contract.md`.
- Phase 52.5 env secrets certs contract: `docs/deployment/env-secrets-certs-contract.md`.
- Phase 52.6 host preflight contract: `docs/deployment/host-preflight-contract.md`.
- Phase 52.7 demo seed contract: `docs/deployment/demo-seed-contract.md`.

The smoke skeleton must also name compose, env/secrets/certs, host preflight, and demo seed contract coverage in fixture output.

## 6. Fixture Expectations

The required fixture directory is `docs/deployment/fixtures/clean-host-smoke`.

| Fixture | Expected validity | Required rejection |
| --- | --- | --- |
| `valid-clean-host-smoke.json` | valid | None. |
| `profile-skipped-clean-host-smoke.json` | valid | None. |
| `false-success.json` | invalid | Smoke reports skipped or mocked profile work as successful full stack. |
| `compose-truth.json` | invalid | Smoke treats Docker or Compose status as workflow truth. |
| `phase-53-54-required.json` | invalid | Smoke requires Phase 53 or Phase 54 profile completion. |

## 7. Validation Rules

Clean-host smoke skeleton validation must fail closed when:

- the contract document is missing;
- the README link is missing;
- any required command is missing, repeated, or out of order;
- mocked or skipped states are missing from the document or fixture set;
- a mocked or skipped step is treated as full-stack success;
- Docker status or Docker Compose status is treated as workflow truth;
- the smoke requires Phase 53 or Phase 54 profile completion;
- compose, env/secrets/certs, host preflight, or demo seed contract references are missing;
- fixture output omits missing prerequisites, later closing phases, or safe next actions for mocked or skipped steps;
- any fixture uses workstation-local absolute paths; or
- the smoke claims RC, GA, production readiness, release truth, gate truth, closeout truth, workflow truth, approval truth, execution truth, or reconciliation truth.

## 8. Forbidden Claims

- Clean-host smoke success is workflow truth.
- Clean-host smoke output is source truth.
- Clean-host smoke output is approval truth.
- Clean-host smoke output is execution truth.
- Clean-host smoke output is reconciliation truth.
- Docker status is AegisOps workflow truth.
- Docker Compose status is AegisOps workflow truth.
- Mocked profile work is successful full stack startup.
- Skipped profile work is successful full stack startup.
- Phase 52.8 requires Phase 53 profile completion.
- Phase 52.8 requires Phase 54 profile completion.
- Phase 52.8 implements Wazuh product profiles.
- Phase 52.8 implements Shuffle product profiles.
- Phase 52.8 completes RC behavior.
- Phase 52.8 completes GA behavior.

## 9. Validation

Run `bash scripts/verify-phase-52-8-clean-host-smoke-skeleton.sh`.

Run `bash scripts/test-verify-phase-52-8-clean-host-smoke-skeleton.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1071 --config <supervisor-config-path>`.

The verifier must fail when skipped or mocked profile work is reported as successful full stack startup, when Docker or Docker Compose state is treated as workflow truth, when Phase 53 or Phase 54 profile completion is required, when required contract references are missing, or when publishable guidance uses workstation-local absolute paths.

## 10. Non-Goals

- No full stack startup implementation is approved by this contract.
- No Wazuh product profile, Shuffle product profile, guided UI journey, RC behavior, GA behavior, production readiness, release gate, or runtime behavior is implemented here.
- No smoke output, fixture output, Docker state, Docker Compose state, generated config state, host preflight state, demo seed output, Wazuh state, Shuffle state, browser state, UI cache, logs, tickets, downstream receipts, or operator-facing summary becomes authoritative AegisOps truth.
