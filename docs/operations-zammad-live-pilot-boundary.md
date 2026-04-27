# Operations Zammad-First Live Pilot Boundary and Credential Custody

## 1. Purpose

This document defines the first live coordination-substrate pilot boundary for AegisOps operations.

It supplements `docs/phase-26-first-coordination-substrate-and-non-authoritative-ticket-boundary.md`, `docs/auth-baseline.md`, `docs/network-exposure-and-access-path-policy.md`, and `docs/runbook.md` by narrowing the first live coordination path to one substrate and by recording the credential, endpoint, unavailable, and degraded-state posture required before that path can be activated.

This document defines policy and verification expectations only. It does not provision Zammad, mint credentials, create a bidirectional synchronization service, authorize ticket-system workflow truth, or store live secrets.

The pilot readiness checklist in `docs/deployment/pilot-readiness-checklist.md` consumes this Zammad-first boundary as the coordination pilot scope and credential-custody prerequisite for pilot entry.

## 2. Pilot Scope and Non-Authority Boundary

Zammad is the only approved live coordination substrate for the first pilot.

GLPI remains a documented fallback only after a separate reviewed change rejects Zammad for the pilot.

The pilot is link-first and coordination-only. AegisOps may record a reviewed Zammad ticket pointer, ticket URL, external receipt, and bounded operator-facing coordination status when those values are explicitly bound to the authoritative AegisOps case or action-review record.

AegisOps remains authoritative for case, action, approval, execution, and reconciliation records.

Ticket state, SLA state, comments, assignee, queue, priority, escalation, or closure in Zammad must not become AegisOps case, action, approval, execution, or reconciliation authority.

The following are out of scope for this pilot:

- multi-ITSM abstraction;
- bidirectional sync;
- ticket-system authority;
- ticket-driven case creation;
- ticket-driven approval or execution dispatch;
- ticket-driven reconciliation or case closure;
- background ticket polling as lifecycle truth; and
- direct promotion of Zammad workflow state into AegisOps-owned records.

## 3. Credential Custody and Rotation

Zammad live-pilot credentials must resolve only from the reviewed managed-secret boundary.

The approved runtime bindings are:

- `AEGISOPS_ZAMMAD_BASE_URL` for the reviewed Zammad endpoint URL;
- `AEGISOPS_ZAMMAD_TOKEN_FILE` for a mounted secret-file token reference; and
- `AEGISOPS_ZAMMAD_OPENBAO_PATH` for a managed-secret reference when OpenBao is the reviewed backend.

At least one reviewed secret reference, either `AEGISOPS_ZAMMAD_TOKEN_FILE` or `AEGISOPS_ZAMMAD_OPENBAO_PATH`, must be present before live Zammad access is enabled. The resolved value must be non-empty, current, and scoped only to the pilot coordination action family.

No Zammad credential, bearer token, API key, session cookie, customer secret, or environment-specific endpoint credential may be committed to Git, copied into issue text, stored in fixtures, or embedded in operator prompts.

Placeholder, sample, fake, TODO, unsigned, empty, stale, or human-mailbox credentials are invalid.

The credential owner is the Platform Administrator role defined in `docs/auth-baseline.md`. Operators may request pilot activation or report degraded status, but they must not substitute a personal Zammad session, mailbox-backed credential, browser state, copied token, or prior cached secret read for the reviewed source.

Rotation must be documented before pilot activation, after suspected exposure, after custodian or scope change, and after any break-glass use.

The rotation record must include the AegisOps release or repository revision, named custodian, secret source reference, affected consumer set, activation time, reload or restart checkpoint, redacted verification evidence, and follow-up owner for any degraded or unavailable outcome.

If the reviewed secret source is unavailable, unreadable, empty, stale, or only placeholder-backed, the pilot remains unavailable and fails closed.

## 4. Endpoint and Proxy Assumptions

Zammad access for the pilot must use the reviewed outbound integration path and the documented endpoint in `AEGISOPS_ZAMMAD_BASE_URL`.

The endpoint must identify one reviewed Zammad tenant or instance. Operators must not infer tenant, customer, queue, or case linkage from hostname shape, ticket number shape, free text, labels, comments, or nearby issue metadata.

Operators must not trust raw `X-Forwarded-*`, `Forwarded`, host, proto, tenant, or user identity hints from Zammad unless a later reviewed proxy boundary has already authenticated and normalized those signals.

The AegisOps backend and operator UI must not expose a direct inbound Zammad webhook authority path for this pilot.

If a future webhook or callback path is reviewed, it must be treated as non-authoritative coordination context until a separate boundary proves authentication, replay protection, tenant binding, and explicit linkage to the authoritative AegisOps record.

Endpoint failures, proxy failures, TLS failures, authorization failures, DNS failures, schema drift, or mismatched ticket identifiers must remain visible as coordination-path health signals. They must not silently downgrade into success, cached truth, or ticket-system authority.

## 5. Unavailable and Degraded Operator Behavior

The pilot has three operator-visible states:

- `available`: the reviewed endpoint and credential source validated for the current bounded operation, and returned coordination context is explicitly bound to the AegisOps record.
- `degraded`: AegisOps authoritative records remain usable, but the Zammad coordination path is stale, partially unavailable, slow, missing optional fields, or returns a non-authoritative mismatch that must be visible.
- `unavailable`: the endpoint, credential source, proxy path, token custody validation, or explicit AegisOps linkage is missing or failed.

When Zammad is unavailable or credentials fail custody validation, operators may continue AegisOps case review, approval, execution, and reconciliation from AegisOps records.

When Zammad is degraded, operators may inspect the last verified coordination reference only if the UI or report labels it as non-authoritative and stale or partial. They must repair the coordination path or keep it degraded; they must not treat degraded Zammad context as approval, execution, reconciliation, or case truth.

Operators must not infer ticket existence, approval, execution, reconciliation, closure, or customer notification from a missing, stale, unreachable, or mismatched Zammad record.

No failed Zammad write, stale read, timeout, proxy failure, auth failure, or degraded ticket payload may create an orphan AegisOps authority record or mark an AegisOps lifecycle step complete.

Unavailable or degraded pilot behavior is testable by verifying that missing credential source, placeholder credential source, unreachable endpoint, stale ticket read, mismatched ticket identifier, and missing explicit AegisOps linkage all preserve AegisOps authority and expose the coordination gap.

## 6. Rehearsal Evidence

The bounded rehearsal fixture is `control-plane/tests/fixtures/zammad/non-authority-coordination-rehearsal.json`.

The rehearsal fixture covers available, degraded, and unavailable Zammad coordination states.

A stale or mismatched ticket identifier must be retained as degraded or unavailable coordination evidence only.

A missing, placeholder, fake, sample, TODO, empty, stale, or unsigned credential must block the live-available posture.

Every rehearsal scenario must keep AegisOps records authoritative and must not create an orphan case, action, approval, execution, or reconciliation record from ticket state.

## 7. Verification Expectations

Before the pilot is treated as ready, run:

- `bash scripts/verify-zammad-live-pilot-boundary.sh`;
- `python3 -m unittest control-plane.tests.test_issue812_zammad_live_pilot_boundary_docs`; and
- a live or rehearsed credential-custody checklist that proves the configured `AEGISOPS_ZAMMAD_TOKEN_FILE` or `AEGISOPS_ZAMMAD_OPENBAO_PATH` resolves through the reviewed managed-secret boundary without exposing the secret value.

The verifier fails closed when this document stops naming Zammad as the single first pilot substrate, weakens credential custody, omits endpoint or proxy assumptions, omits unavailable or degraded behavior, introduces placeholder or fake credential acceptance, introduces workstation-local path guidance, or promotes the external ticket system to case, action, approval, execution, or reconciliation authority.
