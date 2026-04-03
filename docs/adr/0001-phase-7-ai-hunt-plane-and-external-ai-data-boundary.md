# ADR-0001: Phase 7 AI Hunt Plane and External AI Data Boundary

- **Status**: Accepted
- **Date**: 2026-04-04
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/requirements-baseline.md`
- **Product**: AegisOps
- **Related Issues**: #144, #143
- **Supersedes**: N/A
- **Superseded By**: N/A

---

## 1. Context

AegisOps already defines separate detection, control, and execution boundaries, but it does not yet define where Phase 7 AI-assisted hunting fits relative to those planes or what data may cross to an external AI provider.

The existing baseline already fixes several constraints:

- OpenSearch owns detection and analytics outputs rather than downstream case or approval state.
- the future AegisOps control plane owns alert, case, approval, and action-request state rather than OpenSearch dashboards or n8n history;
- n8n owns workflow execution runtime state rather than approval or case state; and
- approval, execution, and evidence must remain separate records with explicit auditability.

What remains undecided is whether an AI assistant may become part of the decision path, whether it may store or own operator workflow context, and which AegisOps data classes may be sent to an external AI provider.

This decision cannot be deferred because later implementation work could otherwise create a shadow control plane through chat transcripts, provider-side memory, or direct AI-driven execution shortcuts.

## 2. Decision

The AI hunt plane is an advisory-only analysis surface.

The AI hunt plane must not become a shadow control plane.

We will place the AI hunt plane beside the detection and control planes as an analyst-assistance layer that can summarize, correlate, and suggest investigative follow-up without owning durable platform state.

The AI hunt plane may read approved source material from the detection plane and the control plane, but it does not own alert, case, approval, or execution state.

We will not allow the AI hunt plane to approve actions, open or close cases as the authoritative actor, change approval status, or claim execution success.

The AI hunt plane may recommend hunts, summarize patterns, propose Sigma-style logic, and rank follow-up questions, but a human analyst must decide whether any recommendation changes alert, case, approval, or execution state.

Direct AI-to-n8n execution is prohibited.

External AI output must never be treated as evidence by itself.

If AI-generated text is retained internally, it must be stored only as analyst work product with citations, timestamps, and source references that distinguish model output from underlying evidence.

Every external AI request must use `store=false` or an equivalent provider control that disables provider-side retention and training use.

External AI prompts and responses must be treated as transient advisory material unless a human explicitly copies a bounded excerpt into an internal AegisOps record with citation context and retention that follows the internal record family.

The approved external AI data boundary is:

| Data class | External AI policy | Boundary rule |
| ---- | ---- | ---- |
| Sanitized detection summary | Allowed with reviewable prompt context | External AI may receive analyst-prepared summaries of findings, detections, and hypotheses when direct identifiers, secrets, and raw event payloads are removed. |
| Citation-ready excerpt from already approved internal documentation | Allowed with source reference | The excerpt must remain bounded, attributable, and sufficient for the analyst to verify what the model is reacting to. |
| Synthetic or redacted hunt hypotheses | Allowed | The prompt may contain attack-pattern descriptions, tactic summaries, and proposed search logic that do not expose internal-only identifiers or sensitive payloads. |
| Case narrative, approval state, or action-execution state | Prohibited | External AI must not become the system of record or working memory for operator workflow state. |
| Raw event payloads, full normalized events, evidence artifacts, or chain-of-custody records | Prohibited | These classes remain internal because they are evidence-bearing records whose fidelity and custody must stay inside AegisOps-controlled systems. |
| Secrets, credentials, tokens, private keys, session cookies, or live approval artifacts | Prohibited | These classes remain internal-only because disclosure could directly widen authority or bypass approval boundaries. |
| Direct target identifiers for production systems when not already public and not strictly required for a sanitized summary | Prohibited by default | External AI requests must not expose hostnames, account identifiers, IP inventories, or similar operational identifiers unless a future approved ADR narrows the exception. |

## 3. Decision Drivers

- security and least-privilege handling of sensitive data
- auditability of case, approval, and execution decisions
- prevention of provider-side data retention and shadow state accumulation
- reproducibility and citation-first analyst workflow
- alignment with existing control-plane and response-action baselines
- operational simplicity for future implementation reviews

## 4. Options Considered

### Option A: Advisory-only AI hunt plane with explicit external data boundary

#### Description
Define AI as an analyst-assistance plane that can read only approved prompt material, cannot execute actions, and cannot own durable control or evidence state.

#### Pros
- Preserves existing detection, control, and execution boundaries.
- Allows useful AI-assisted hunting without delegating authority.
- Gives future implementation work a concrete allowlist and denylist for external AI flows.

#### Cons
- Requires analysts to prepare sanitized context instead of sending raw records directly.
- Limits convenience features such as long-lived external chat memory or autonomous execution.

### Option B: External AI as a semi-autonomous case copilot

#### Description
Allow external AI to maintain working case context, draft case state changes, and trigger downstream workflow requests through operator review.

#### Pros
- Reduces analyst copy-and-paste work.
- Could speed triage and workflow assembly.

#### Cons
- Blurs the control-plane boundary and risks a shadow control plane.
- Increases the chance that provider transcripts contain approval or case state.
- Makes audit reconstruction dependent on provider-side context and retention behavior.

### Option C: No external AI use at all

#### Description
Forbid external AI-assisted hunting entirely and require all analysis help to remain manual or future internal-only.

#### Pros
- Eliminates external AI data-transfer risk.
- Keeps all investigative context inside internal systems.

#### Cons
- Discards a useful advisory capability that can improve analyst productivity.
- Forces future work to revisit the same boundary question later.

## 5. Rationale

Option A fits the AegisOps baseline because it preserves the documented separation between detection outputs, control-plane state, approval records, evidence, and execution outcomes.

Option B was rejected because it would let external AI accumulate case memory, implied approval context, or action intent outside the platform's authoritative records, which is exactly the shadow control plane risk this ADR is meant to prevent.

Option C was rejected because the baseline can safely support citation-first, advisory-only use if the data boundary is narrow, provider retention is disabled, and operator authority remains explicit.

The accepted trade-off is lower convenience in exchange for clearer governance. Analysts must sanitize context, preserve citations, and keep authoritative workflow state internal rather than relying on external chat history.

## 6. Consequences

### Positive Consequences
- Future AI features have a clear authority ceiling.
- Later implementation can distinguish allowed summarization from prohibited evidence or approval handling.
- Reviewers can reject any proposal that routes control or execution state through external AI.

### Negative Consequences
- Analysts cannot treat provider chats as durable case notebooks.
- Some potentially useful context will remain unavailable to external AI because it is too sensitive or evidence-bearing.

### Neutral / Follow-up Consequences
- A future ADR may define an internal-only AI path with different storage controls.
- Prompt templates, redaction helpers, and citation formatting may be added later without changing this authority boundary.

## 7. Implementation Impact

If this ADR is implemented in later phases, the following changes will be required:

- prompt-building code and runbooks must classify source material before any external AI submission;
- external AI integrations must set `store=false` or the provider-equivalent retention-disable control and must not rely on provider memory features;
- UI or workflow surfaces must label AI responses as advisory-only and citation-dependent;
- future control-plane or case-management work must ensure AI text cannot overwrite alert, case, approval, or execution records as the authoritative source; and
- documentation for prompts, retention, and approval flows must reference this ADR before enabling any external AI integration.

No live integration, secret provisioning, workflow automation, or provider selection is approved by this ADR.

## 8. Security Impact

This ADR reduces the risk that external AI becomes an unreviewed authority path for approvals or execution.

Privileges do not expand. External AI remains read-only relative to approved prompt material and has no authority to issue commands, mutate state, or hold secrets.

Secrets handling becomes stricter for future AI integrations because prompts must exclude credentials, approval artifacts, and evidence-bearing raw records.

Attack surface changes only in the sense that any future external AI connector must enforce redaction, retention-disable controls, request logging, and internal auditability before it is allowed in scope.

Approval requirements do not weaken. Human approval and bounded machine execution remain mandatory where already required by the response-action baseline.

## 9. Rollback / Exit Strategy

Rollback is triggered if a future implementation cannot honor the advisory-only boundary, cannot disable provider-side retention, or needs broader data access than this ADR allows.

The rollback path is to disable external AI integrations and keep AI-assisted hunting limited to internal-only drafts or manual analyst work until a superseding ADR is approved.

Rollback does not require migrating authoritative platform state because this ADR forbids external AI ownership of that state in the first place.

## 10. Validation

This decision will be validated by:

- repository-level verification that the ADR exists and contains the required boundary language;
- design review confirming that future AI proposals keep alert, case, approval, and execution state internal;
- integration review confirming any provider request uses `store=false` or an equivalent retention-disable control; and
- workflow review confirming there is no direct AI-to-n8n execution path and no implicit promotion of AI output to evidence.

## 11. Non-Goals

- This ADR does not approve a specific external AI provider, SDK, model, or pricing plan.
- This ADR does not define prompt templates, redaction code, or UI implementation details.
- This ADR does not authorize autonomous response behavior, provider-hosted case memory, or AI-authored approval decisions.
- This ADR does not replace the existing control-plane, auth, response-action, or retention baselines.

## 12. Approval

- **Proposed By**: Codex for Issue #144
- **Reviewed By**: AegisOps maintainers
- **Approved By**: AegisOps maintainers
- **Approval Date**: 2026-04-04
