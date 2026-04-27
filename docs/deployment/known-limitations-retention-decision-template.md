# Known Limitations and Retention Decision Template

## 1. Purpose and Boundary

This template is the reviewed decision record for a bounded single-customer pilot go/no-go review.

Use it before pilot launch to record accepted limitations, blocking limitations, rollback or disable decisions, follow-up owners, revisit dates, and bounded retention expectations for the same reviewed release identifier.

This template does not change AegisOps authority, approval, execution, reconciliation, readiness, runtime behavior, detector activation, ticket authority, assistant authority, or subordinate evidence posture.

A completed template must distinguish no known blocking limitation from not reviewed.

## 2. Decision Header

| Field | Value |
| --- | --- |
| Release identifier | `<aegisops-single-customer-repository-revision-or-reviewed-tag>` |
| Pilot customer scope | `<single-customer-scope-reference>` |
| Pilot owner | `<named-owner>` |
| Review date | `<YYYY-MM-DD>` |
| Next revisit date | `<YYYY-MM-DD>` |
| Decision status | `<go|no-go|go-with-explicit-limitations|not-reviewed>` |
| Limitation review state | `<reviewed-no-known-blocking-limitation|reviewed-with-limitations|not-reviewed>` |
| Retention decision owner | `<named-owner>` |

## 3. Limitation Decision Register

Disposition values: blocking, accepted-with-owner, rollback, disable, follow-up, not-reviewed.

| Limitation ID | Affected surface | Disposition | Owner | Expected operator-visible behavior | Retention decision | Revisit date | Evidence reference |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `<LIM-001>` | `<release|runtime-smoke|detector|coordination|assistant|evidence-handoff|support|rollback>` | `<blocking|accepted-with-owner|rollback|disable|follow-up|not-reviewed>` | `<named-owner>` | `<operator-visible-effect-or-no-visible-effect>` | `<bounded-evidence-reference-and-retention-expectation>` | `<YYYY-MM-DD>` | `<repo-relative-or-record-reference>` |

Every accepted-with-owner limitation must name the owner, expected operator-visible behavior, revisit date, affected surface, and retention decision.

Use blocking when the pilot must not start until the limitation is repaired or explicitly refused. Use rollback when the limitation invalidates launch or upgrade acceptance unless the reviewed rollback path succeeds. Use disable when the safe pilot state requires a detector, integration, optional extension, or workflow path to remain disabled. Use follow-up only when pilot start remains acceptable and the owner, operator-visible behavior, revisit date, and retention decision are explicit. Use not-reviewed only to block the entry decision until review is complete.

## 4. Retention Decision

Retention decisions must be bounded to reviewed pilot evidence, not unlimited raw-log retention.

Record the retained entry decision, release handoff record, runtime smoke manifest, detector activation evidence handoff, Zammad coordination status, assistant limitation statement, known-limitation review, handoff owner, next health review expectation, and any clean-state or refusal evidence required for failed paths.

Do not promise to retain every raw log line, external ticket field, detector event, assistant prompt, substrate receipt, browser session, customer-private payload, or historical smoke sample forever.

If a future review requires raw customer evidence that is not retained in this packet, keep the request refused or blocked until an approved redacted evidence source is available. Do not infer success from a missing artifact.

## 5. Redaction and Subordinate Context

Do not include secrets, live credentials, customer-private raw logs, raw forwarded-header values, unsigned identity hints, workstation-local paths, or customer-private ticket content.

Subordinate systems, optional extensions, external tickets, detector substrates, assistant output, and bounded logs are context only; they do not own AegisOps approval, execution, reconciliation, readiness, release, or pilot-entry truth.

Do not infer customer, tenant, repository, account, issue, or environment linkage from names, path shape, comments, or nearby metadata. Use only the reviewed release identifier and authoritative AegisOps record references.

## 6. Review Outcome

| Outcome field | Value |
| --- | --- |
| Blocking limitations remain | `<yes|no|not-reviewed>` |
| Accepted limitations have owners and revisit dates | `<yes|no|not-reviewed>` |
| Rollback or disable decisions recorded | `<yes|no|not-applicable|not-reviewed>` |
| Bounded retention decision recorded | `<yes|no|not-reviewed>` |
| Customer-facing summary redaction checked | `<yes|no|not-reviewed>` |
| Pilot readiness effect | `<go|no-go|go-with-explicit-limitations|not-reviewed>` |

## 7. Out of Scope

Unsupported compliance certification, SLA commitments, 24x7 support promises, public launch approval, multi-customer rollout, multi-tenant expansion, legal hold automation, and runtime retention enforcement are out of scope.

This template also does not approve unlimited archives, customer-specific support terms, direct backend access, optional-extension launch gates, external ticket authority, assistant-owned workflow action, source-side mutation, or production write behavior.
