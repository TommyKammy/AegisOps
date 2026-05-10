# Phase 58.6 Support Bundle And Redaction Contract

## Purpose

Phase 58.6 defines the support bundle contract for customer-safe diagnostic
evidence. A support bundle is redacted diagnostic evidence only. It can help a
bounded support collaborator understand environment class, version posture,
doctor output, backup and restore evidence references, reviewed limitations,
and reproduction context without exposing customer-private operational data.

Support bundles cannot approve, execute, reconcile, release, close, restore, or
replace authoritative AegisOps records. They are not workflow truth, release
truth, gate truth, restore truth, audit truth, closeout truth, customer-support
truth, or operator authority.

## Runtime Surface

No remote upload service, background collector, direct database export,
substrate log scraper, support operator workflow, or support authority path is
introduced by this contract.

Future reviewed bundle output may be retained as Markdown, JSON, or archive
evidence after redaction and scanning. The Phase 58.6 runtime posture is
contract validation only:

- Contract verifier: `bash scripts/verify-phase-58-6-support-bundle-redaction-contract.sh`.
- Focused verifier regression: `bash scripts/test-verify-phase-58-6-support-bundle-redaction-contract.sh`.
- Path hygiene: `bash scripts/verify-publishable-path-hygiene.sh`.
- Issue lint: `node <codex-supervisor-root>/dist/index.js issue-lint 1241 --config <supervisor-config-path>`.

## Allowed Bundle Contents

| Content | Required boundary |
| --- | --- |
| `environment_class` | Reviewed profile, deployment class, or lab class only; no tenant inference from path shape, ticket title, or host name. |
| `component_versions` | AegisOps-owned component and package versions after reviewed redaction; no floating `latest` claims as evidence. |
| `doctor_summary` | Phase 58.1 doctor output or summarized health state after redaction; not authoritative workflow or release truth. |
| `backup_restore_references` | Links to Phase 58.3 backup custody evidence and Phase 58.4 restore dry-run evidence; not raw backup payloads. |
| `upgrade_rollback_references` | Links to Phase 58.5 upgrade and rollback planning evidence; not proof of live upgrade or rollback completion. |
| `known_limitations` | Reviewed limitations, non-goals, unsafe states, retained manual steps, and owner references. |
| `reproduction_steps` | Operator-reviewed reproduction steps with customer names, private payloads, tickets, credentials, and workstation paths removed. |
| `bounded_metadata` | Sanitized timestamps, record counts, schema versions, source families, and evidence identifiers directly linked to authoritative records. |
| `redaction_manifest` | Redaction families applied, scan result, retained limitations, and explicit subordinate-evidence boundary. |

## Forbidden Bundle Contents

| Content | Required behavior |
| --- | --- |
| `secrets` | Reject or redact API keys, shared secrets, passwords, private keys, signing keys, bootstrap tokens, session material, and env-secret values. |
| `workstation_local_paths` | Reject or redact macOS, Linux, and Windows user-profile paths; use repo-relative paths, documented env vars, or placeholders. |
| `customer_private_raw_payloads` | Reject raw alerts, raw logs, raw tickets, raw webhook bodies, raw event payloads, and customer-private source payloads by default. |
| `ticket_private_content` | Reject private ticket comments, customer names, customer screenshots, chat excerpts, support notes, and operator-only escalation text. |
| `tokens_and_headers` | Reject authorization headers, cookies, bearer tokens, forwarded headers, raw host or tenant hints, and client-supplied identity fields. |
| `cert_material` | Reject certificates, private keys, CSRs, keystores, truststores, and inline PEM blocks unless replaced with reviewed fingerprints. |
| `raw_credentials` | Reject usernames paired with passwords, connection strings containing credentials, service-account secrets, and placeholder credentials. |
| `authority_claims` | Reject bundle-as-workflow-truth, support-as-operator, support-as-approver, support-as-release-gate, or support-as-restore-truth claims. |

## Redaction Rules

| Family | Redaction rule |
| --- | --- |
| `secret_values` | Replace secret-looking values with `[REDACTED:secret]` and fail closed when the value remains recoverable in output. |
| `workstation_paths` | Replace user-home absolute paths with `[REDACTED:workstation-path]`; retain only repo-relative paths or placeholders. |
| `private_payloads` | Summarize payload type, source family, authoritative record link, and bounded counts; do not retain raw payload bodies by default. |
| `ticket_private_content` | Replace private ticket text with `[REDACTED:ticket-private-content]` and retain only public ticket identifiers or reviewed references. |
| `tokens_and_headers` | Remove authorization, cookie, forwarded, tenant, host, proto, and user-id headers unless a trusted boundary normalized them first. |
| `certs_and_keys` | Replace cert and key material with reviewed fingerprints, expiry metadata, issuer class, or custody references. |
| `credentials` | Remove usernames paired with passwords, credential-bearing URLs, DSNs, and placeholder credentials from retained output. |
| `customer_identifiers` | Replace customer names, tenant names, account names, private host names, email addresses, and screenshots with reviewed placeholders. |

## Failure States

| State | Rejected condition | Required behavior |
| --- | --- | --- |
| `secret_leakage` | Bundle output contains secret-looking values, tokens, auth headers, cookies, private keys, cert material, credential-bearing DSNs, or placeholder credentials. | Reject the bundle before retention or sharing. |
| `workstation_path_leakage` | Bundle output contains macOS, Linux, or Windows workstation-local user-profile paths. | Reject the bundle and require repo-relative paths, env vars, or placeholders. |
| `private_payload_leakage` | Bundle output contains raw customer payloads, raw logs, raw tickets, raw webhook bodies, screenshots, or private support notes. | Reject the bundle and retain bounded summaries only. |
| `authority_expansion` | Bundle output is presented as workflow, release, gate, restore, audit, closeout, approval, execution, reconciliation, or operator truth. | Reject the bundle and preserve authoritative AegisOps record-chain truth. |
| `support_operator_expansion` | Support collaborator access is treated as operator, approver, administrator, substrate operator, or direct backend authority. | Reject the bundle and require a reviewed authority contract. |
| `missing_redaction_manifest` | Redaction families, scan result, subordinate boundary, or retained limitations are absent. | Reject the bundle until the manifest is complete. |
| `mixed_snapshot_bundle` | Bundle assembles records from different committed snapshots without detecting or rejecting mixed-state evidence. | Reject the bundle before retention or sharing. |

## Authority Boundary

Support bundles are subordinate diagnostic evidence. AegisOps control-plane
records remain authoritative for alert, case, evidence, approval, action
request, execution receipt, reconciliation, audit, limitation, release, gate,
restore, workflow, and closeout truth.

Support bundle validation cannot approve remediation, execute actions, reconcile
actions, close cases, satisfy Pilot, Beta, RC, or GA gates, prove backup or
restore success, prove upgrade or rollback success, mutate substrate state,
grant support operator authority, or replace customer-owned decisions.

When provenance, record linkage, snapshot consistency, redaction status,
secret-scan status, support scope, or authority-boundary signals are missing,
malformed, placeholder-like, or only partially trusted, validation fails closed.

## Retention Boundary

A retained support bundle must include a redaction manifest, scan result,
creation timestamp, environment class, reviewed owner, evidence links, retained
limitations, and explicit subordinate-evidence boundary. Retention is allowed
only after secret-looking value scanning, workstation-local path scanning,
private-payload review, ticket-private-content review, token and header review,
cert material review, credential review, and authority-boundary review pass.

## Negative Tests

The verifier must reject:

- secret leakage;
- workstation-local path leakage;
- customer-private raw payload leakage;
- ticket-private content leakage;
- token and header leakage;
- cert material leakage;
- raw credential leakage;
- missing redaction manifest;
- support bundle as workflow, release, gate, restore, audit, or closeout truth;
- support operator authority expansion;
- mixed-snapshot bundle claims.

## Non-Goals

Phase 58.6 does not implement remote support upload, support portal workflow,
customer-private raw log inclusion by default, support operator authority, live
backend access for support collaborators, substrate operation, action approval,
action execution, reconciliation, release-gate automation, restore execution,
backup execution, upgrade execution, rollback execution, audit export, or
support bundle output as authoritative workflow truth.

## Validation

Run:

- `bash scripts/verify-phase-58-6-support-bundle-redaction-contract.sh`
- `bash scripts/test-verify-phase-58-6-support-bundle-redaction-contract.sh`
- `bash scripts/verify-publishable-path-hygiene.sh`
- `node <codex-supervisor-root>/dist/index.js issue-lint 1241 --config <supervisor-config-path>`
