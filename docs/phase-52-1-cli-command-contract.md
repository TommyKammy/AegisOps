# Phase 52.1 CLI Command Contract

- **Status**: Accepted
- **Date**: 2026-05-01
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/adr/0011-phase-51-1-replacement-boundary.md`, `docs/phase-51-6-authority-boundary-negative-test-policy.md`
- **Related Issues**: #1063, #1064

This contract defines the first-user CLI command contract only. It does not implement installer behavior, Wazuh profile generation, Shuffle profile generation, first-user UI flows, AI operations, SIEM breadth, SOAR breadth, packaging, release-candidate behavior, or general-availability behavior.

## 1. Purpose

Phase 52.1 gives later executable-stack issues one stable contract for the first-user CLI surface. The CLI may guide an operator through setup, startup, readiness review, demo seeding, status inspection, browser opening, log inspection, and shutdown.

The approved command names are `init`, `up`, `doctor`, `seed-demo`, `status`, `open`, `logs`, and `down`.

## 2. Authority Boundary

CLI output is operator guidance and readiness evidence only. CLI output is not alert, case, evidence, approval, execution, reconciliation, gate, release, or production truth.

AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, and closeout truth.

This command contract cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md`. The CLI must preserve the Phase 51.6 rule that subordinate surfaces, including Wazuh, Shuffle, tickets, AI, browser state, UI cache, downstream receipts, and demo data, cannot become workflow truth.

## 3. Shared Output Contract

Every command must emit structured operator-facing output with:

- `command`: the invoked command name.
- `result`: one of `ok`, `skipped`, `mocked`, `degraded`, or `failed`.
- `summary`: a short human-readable operator summary.
- `next_actions`: zero or more safe follow-up commands or prerequisite actions.
- `evidence`: zero or more readiness evidence references, never authoritative workflow truth.

The CLI must use repo-relative commands, documented environment variables, and placeholders such as `<runtime-env-file>`, `<profile-name>`, `<log-selector>`, `<evidence-dir>`, `<supervisor-config-path>`, and `<codex-supervisor-root>` in publishable guidance.

## 4. Command Contract

| Command | Purpose | Required inputs | Expected outputs | Failure behavior | Safe retry guidance |
| --- | --- | --- | --- | --- | --- |
| `init` | Create or validate the local first-user AegisOps workspace skeleton and runtime configuration placeholders. | Repository checkout; writable working directory; optional `<runtime-env-file>`; selected `<profile-name>`. | `result=ok` when placeholders are present; generated or reused config paths; explicit next action `aegisops up`; readiness evidence references only. | Fail closed if the target directory is not writable, required templates are missing, or an existing config conflicts with the selected profile. Do not overwrite operator-owned files without an explicit reviewed flag. | Safe to retry after fixing permissions, restoring templates, or choosing a non-conflicting profile. Retry must be idempotent and preserve existing operator-owned values. |
| `up` | Start the reviewed first-user stack components that are available for the selected profile. | Initialized workspace; `<runtime-env-file>`; selected `<profile-name>`; available container or process runtime. | `result=ok` only for components actually started or already healthy; `result=skipped` or `result=mocked` for unavailable Wazuh or Shuffle profiles; service endpoints and next action `aegisops doctor`. | Fail closed when required control-plane prerequisites are missing, startup exits non-zero, readiness cannot be checked, or profile binding is ambiguous. Do not claim Wazuh or Shuffle profile completion when those profiles are absent. | Safe to retry after `doctor` identifies the missing prerequisite. Retry may reuse already-running components and must surface any skipped or mocked state again. |
| `doctor` | Inspect local prerequisites, profile selection, readiness probes, and authority-boundary warnings. | Repository checkout; optional `<runtime-env-file>`; selected or discoverable `<profile-name>`. | Readiness checklist with `ok`, `skipped`, `mocked`, `degraded`, or `failed` per check; explicit prerequisite follow-ups; evidence references only. | Fail closed when required readiness checks cannot run, snapshots are mixed, profile identity is missing, or a subordinate surface is presented as authoritative truth. | Safe to retry after resolving prerequisites. Retry must recompute checks from current state instead of trusting stale output. |
| `seed-demo` | Seed reviewed demo-only records and fixtures for first-user evaluation without production claims. | Initialized workspace; explicit demo mode flag; selected `<profile-name>`; demo fixture bundle. | `result=ok` only for demo fixture admission; demo record identifiers; warning that demo data is not production truth; next action `aegisops status`. | Fail closed if demo mode is not explicit, fixture provenance is missing, fake credentials are treated as real, or seed data would overwrite production-bound records. | Safe to retry after cleaning partial demo state or supplying a reviewed fixture bundle. Retry must not duplicate authoritative records silently. |
| `status` | Summarize local stack health and first-user readiness from current checks. | Initialized workspace; optional `<runtime-env-file>`; selected or discoverable `<profile-name>`. | Current component health; skipped or mocked Wazuh and Shuffle states; links to AegisOps record identifiers when available; operator guidance only. | Fail closed when the status read mixes snapshots, cannot bind to the selected profile, or attempts to treat CLI status as workflow truth. | Safe to retry at any time. Retry must refresh from current checks and must not promote cached summaries to authoritative state. |
| `open` | Open or print the reviewed operator access URL for the local stack. | Initialized workspace; selected `<profile-name>`; reviewed access URL or route. | Operator URL or browser-open result; warning that browser state is not workflow truth; next action `aegisops doctor` if readiness is unknown. | Fail closed if the URL is missing, unreviewed, points outside the approved access path, or would bypass the reviewed reverse proxy boundary. | Safe to retry after fixing access configuration. Retry must not infer tenant, profile, or readiness from browser state. |
| `logs` | Show bounded logs for selected first-user stack components. | Initialized workspace; `<log-selector>` or default selector; optional time window. | Bounded log stream or retained log path; redaction and truncation notice; evidence references only. | Fail closed if the selector is ambiguous, logs cannot be bounded, redaction cannot run, or log text is used as authoritative workflow truth. | Safe to retry with a narrower selector or time window. Retry must not require destructive cleanup. |
| `down` | Stop the local first-user stack without deleting authoritative or operator-owned state. | Initialized workspace; selected `<profile-name>`; optional reviewed cleanup flag. | `result=ok` when managed components are stopped or already stopped; retained state paths; next actions for restart or cleanup. | Fail closed if component ownership is ambiguous, cleanup would delete operator-owned state, or shutdown cannot verify component identity. | Safe to retry. Retry may treat already-stopped managed components as `ok`, while preserving retained state and surfacing unmanaged components. |

## 5. Mocked and Skipped States

Before reviewed Wazuh and Shuffle product profiles exist, commands must report unavailable substrate work as explicit `skipped` or `mocked` states. `skipped` means the command intentionally did not attempt a profile-backed operation because the reviewed profile is absent or disabled. `mocked` means the command used a reviewed demo or placeholder path that is not production-capable.

`skipped` and `mocked` states must not be reported as false success. They must include the missing prerequisite, the affected command, and the later profile issue that must replace the placeholder path before production use.

Wazuh alert status is not AegisOps workflow truth. Shuffle workflow success is not AegisOps workflow truth. Demo data is not production truth. Browser state, UI cache, logs, tickets, downstream receipts, and CLI summaries are not AegisOps workflow truth.

## 6. Failure and Retry Rules

All commands fail closed when provenance, profile binding, runtime scope, auth context, snapshot consistency, or authority-boundary signals are missing, malformed, stale, mixed, or only partially trusted.

Safe retry means a command can be rerun after the stated prerequisite is repaired without destructive cleanup, duplicate authoritative writes, hidden state promotion, or widened product scope.

Failed, rejected, skipped, mocked, and degraded paths must leave durable state clean. If a command writes multiple records in later implementation work, that logical change must be atomic and later verification must prove no orphan record or partial durable write survives a failed path.

## 7. Forbidden Claims

- CLI status is workflow truth.
- CLI output is authoritative for AegisOps records.
- Phase 52 completes Wazuh profiles.
- Phase 52 completes Shuffle profiles.
- Wazuh alert status is AegisOps workflow truth.
- Shuffle workflow success is AegisOps workflow truth.
- Demo data is production truth.
- Browser state is workflow truth.
- Logs are authoritative workflow truth.

## 8. Validation

Run `bash scripts/verify-phase-52-1-cli-command-contract.sh`.

Run `bash scripts/test-verify-phase-52-1-cli-command-contract.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1064 --config <supervisor-config-path>`.

The verifier must fail when any required command is missing, when command purpose, inputs, outputs, failure behavior, or safe retry guidance is missing, when CLI status is claimed as workflow truth, when Phase 52 is claimed to complete Wazuh or Shuffle profiles, when mocked or skipped states can be false success, when the Phase 51.6 policy citation is missing, or when publishable guidance uses workstation-local absolute paths.

## 9. Non-Goals

- No runtime CLI implementation is approved by this contract.
- No installer, Wazuh profile, Shuffle profile, first-user UI journey, AI operation, SIEM breadth, SOAR breadth, packaging, RC, or GA behavior is implemented here.
- No CLI output, browser state, UI cache, log text, demo data, Wazuh state, Shuffle state, ticket state, downstream receipt, or operator-facing summary becomes authoritative AegisOps truth.
