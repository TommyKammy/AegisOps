# ADR-0002: Wazuh and Shuffle Control-Plane Product Thesis

- **Status**: Accepted
- **Date**: 2026-04-06
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/requirements-baseline.md`
- **Product**: AegisOps
- **Related Issues**: #205, #204
- **Supersedes**: N/A
- **Superseded By**: N/A

---

## 1. Context

AegisOps already defines a control-plane state model, approval boundary, and reconciliation responsibility, but the repository-level product thesis still reads too much like a blueprint for assembling or replacing a SIEM and SOAR stack around OpenSearch, Sigma, and n8n.

The existing baseline already fixes several constraints:

- AegisOps-owned records must remain distinct from external analytics, workflow, and notebook state.
- approval, action intent, evidence, and reconciliation must stay explicit and auditable.
- AI assistance remains advisory-only and must not become the control plane or the system of record for operator workflow state.
- runtime implementation, datastore rollout, schema migration execution, and substrate adapter design still require separate implementation issues and validation.

What remains ambiguous is the product thesis above those constraints. Without an explicit ADR, future implementation could drift in two unsafe directions:

- treating AegisOps as a self-built SIEM or SOAR replacement instead of a governed decision and execution control plane; or
- allowing whichever upstream or downstream substrate is easiest to integrate first to become the de facto authority for alerts, cases, approvals, or execution truth.

This decision cannot be deferred because the pivot affects how future design and implementation issues frame ownership, interfaces, and out-of-scope work.

## 2. Decision

AegisOps is a governed SecOps decision and execution control plane.

We will position AegisOps above external detection and automation substrates rather than as a self-built SIEM or SOAR replacement.

The initial standard detection substrate will be Wazuh.

The initial standard routine automation substrate will be Shuffle.

Wazuh detection outputs will enter AegisOps as substrate detection records and related analytic signals rather than as downstream case or approval truth.

Shuffle will execute only approved routine automation within the scope delegated by AegisOps and will not become the authority for action intent, approval state, or reconciliation state.

The normative mainline policy-sensitive path is:

`Substrate Detection Record -> Analytic Signal -> Alert or Case -> Action Request -> Approval Decision -> Approved Automation Substrate or Executor -> Reconciliation`

AegisOps owns the authoritative policy and governance records for:

- `Alert`
- `Case`
- `Evidence`
- `Observation`
- `Lead`
- `Recommendation`
- `Approval Decision`
- `Action Request`
- `Hunt`
- `Hunt Run`
- `AI Trace`
- `Reconciliation`

AegisOps owns policy evaluation, approval decisions, evidence linkage, reconciliation, and execution safety controls even when an external substrate performs detection or execution work.

AI remains advisory-only. AI output may summarize, correlate, or recommend, but it must not approve actions, mutate authoritative records as the final actor, or claim execution truth.

External substrates must not become the system of record for case truth, approval truth, or execution truth.

OpenSearch, Sigma, and n8n are no longer the defining product thesis for AegisOps. After this ADR:

- Wazuh and Shuffle are the initial standard substrates for the mainline path.
- OpenSearch may be used only as an optional or transitional analytics substrate.
- Sigma may be used only as an optional or transitional rule-definition format or translation source.
- n8n may be used only as an optional or experimental executor or orchestration substrate.

This ADR does not approve live runtime changes, schema changes, deployment changes, or substrate adapter implementation.

## 3. Decision Drivers

- governance clarity for the post-pivot product thesis
- auditability of alert, case, approval, and execution state
- prevention of substrate-owned shadow control planes
- execution safety and approval-first response handling
- flexibility to swap or add substrates without redefining AegisOps
- alignment with the existing control-plane state and reconciliation model

## 4. Options Considered

### Option A: AegisOps as a governed control plane above Wazuh and Shuffle

#### Description
Treat AegisOps as the policy, approval, evidence, and reconciliation authority while Wazuh provides the initial standard detection substrate and Shuffle provides the initial standard routine automation substrate.

#### Pros
- Makes the product thesis explicit without requiring AegisOps to rebuild commodity SIEM and SOAR features first.
- Preserves the approved distinction between substrate signals, control-plane truth, and execution-plane outcomes.
- Gives future implementation work a stable ownership model even if substrates change later.

#### Cons
- Requires careful terminology so substrate records are not mistaken for AegisOps-owned lifecycle records.
- Leaves some older baseline documents needing later alignment updates where they still reflect the prior OpenSearch/Sigma/n8n-first framing.

### Option B: Continue treating AegisOps as an in-house SIEM and SOAR stack centered on OpenSearch, Sigma, and n8n

#### Description
Keep the previous thesis in which AegisOps is primarily the assembly of OpenSearch detection, Sigma content, and n8n orchestration with a future control-plane layer added around them.

#### Pros
- Fits some existing repository wording without immediate narrative change.
- Keeps the current tool choices at the center of the architecture story.

#### Cons
- Confuses the product boundary by making external products look like the core identity of AegisOps.
- Increases the risk that analytics or orchestration products become the practical system of record for workflow truth.
- Makes future substrate substitution look like a product rewrite rather than an implementation detail.

### Option C: Stay substrate-agnostic and defer naming any standard starting substrates

#### Description
Define AegisOps only as a control plane in abstract terms and leave the initial detection and automation substrates unnamed until later implementation work.

#### Pros
- Maximizes flexibility on paper.
- Avoids coupling the thesis to the first chosen products.

#### Cons
- Leaves the current pivot incomplete and makes near-term design issues less concrete.
- Fails to state the reviewed standard path that downstream work is expected to target first.

## 5. Rationale

Option A best fits the current AegisOps baseline because the repository already defines authoritative control-plane records, approval boundaries, and reconciliation duties that sit above analytics outputs and workflow execution metadata.

Option B was rejected because it keeps the older product narrative alive and makes it too easy for OpenSearch documents, Sigma rule artifacts, or n8n execution history to be treated as if they were the platform's durable truth.

Option C was rejected because the pivot needs a concrete reviewed starting point, not only an abstract statement that substrates may exist someday.

The accepted trade-off is that some existing baseline documents will temporarily describe older standard substrates until follow-up issues align them with this ADR. That documentation lag is preferable to leaving the core thesis ambiguous.

## 6. Consequences

### Positive Consequences
- Future work can design around a stable authority model in which AegisOps owns policy-sensitive truth above external products.
- Wazuh and Shuffle become the explicit mainline starting substrates without turning them into the product identity.
- Reviewers gain a direct basis for rejecting designs that let external analytics or automation tools own case, approval, or reconciliation state.

### Negative Consequences
- Existing repository text that still centers OpenSearch, Sigma, and n8n now requires deliberate follow-up alignment.
- Future implementers must map substrate-native concepts into AegisOps-owned records instead of reusing substrate state directly.

### Neutral / Follow-up Consequences
- Later ADRs may standardize additional or replacement substrates without changing AegisOps-owned authority boundaries.
- Future implementation issues will need explicit contracts for Wazuh intake, Shuffle execution delegation, and reconciliation keys.

## 7. Implementation Impact

If this ADR guides later implementation work, the following impacts apply:

- `docs/` content that still presents OpenSearch, Sigma, and n8n as the default product thesis must be reviewed and aligned in follow-up issues;
- future intake logic must translate Wazuh-owned detection outputs into AegisOps-owned alert or case workflows using explicit identifiers and reconciliation context;
- future execution logic must treat Shuffle or another approved executor as the execution substrate for approved actions rather than as the authority for action intent or approval;
- control-plane APIs, schemas, and UI work must preserve the authoritative record families already defined in the baseline documents; and
- future substrate changes must be reviewed as substrate decisions rather than as redefinitions of the AegisOps product boundary.

This ADR does not implement a live control-plane service, does not add schema migrations, does not provision Wazuh or Shuffle, and does not define substrate adapters.

## 8. Security Impact

This ADR strengthens the security posture by making the approval and execution authority boundary explicit.

Privileges do not expand through this document alone. Wazuh remains a detection substrate, and Shuffle remains an execution substrate acting only within approved scope.

Secrets handling does not change in this ADR. Any future substrate integration must still define credential boundaries and access controls in separate reviewed work.

Attack surface does not expand through this document alone because no live runtime path is introduced.

Approval requirements remain explicit. External substrates must not infer, mint, or overwrite approval state from workflow activity.

Auditability improves because case, approval, evidence, and reconciliation truth are defined as AegisOps-owned records rather than substrate-local artifacts.

## 9. Rollback / Exit Strategy

Rollback is triggered if the Wazuh and Shuffle thesis proves incompatible with the approved control-plane ownership model or if another reviewed substrate pairing becomes the accepted standard path.

The rollback path is to supersede this ADR with a new ADR that retains the control-plane authority boundary while naming different standard substrates or a revised thesis.

Rollback does not require migrating authoritative control-plane truth out of Wazuh or Shuffle because this ADR explicitly forbids them from owning that truth in the first place.

The main constraint is documentation alignment: repository-level docs that adopt this thesis must be updated together with any superseding decision so the product framing does not become split across conflicting documents.

## 10. Validation

This decision will be validated by:

- repository-level verification that the ADR exists under `docs/adr/` and contains the approved thesis language;
- review against `docs/adr/0000-template.md` to confirm the decision, consequences, rollback path, and non-goals are explicit;
- review against `docs/adr/review-path.md` to confirm the ADR records explicit review and approval metadata; and
- focused text verification that the ADR names Wazuh, Shuffle, the mainline path, and the advisory-only AI boundary while prohibiting external substrates from becoming the system of record for case, approval, or execution truth.

## 11. Non-Goals

- This ADR does not implement a live Wazuh integration, Shuffle integration, or any other substrate adapter.
- This ADR does not add or change database schemas, migrations, credentials, or deployment manifests.
- This ADR does not replace the existing control-plane state model, response-action safety model, or AI advisory-only boundary.
- This ADR does not prohibit future use of OpenSearch, Sigma, or n8n in optional, transitional, or experimental roles approved by later work.

## 12. Approval

- **Proposed By**: Codex for Issue #205
- **Reviewed By**: AegisOps maintainers
- **Approved By**: AegisOps maintainers
- **Approval Date**: 2026-04-06
