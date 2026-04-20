# <Type>: <Short imperative title>

## 0. Mandatory Reference

This issue MUST comply with:
- `docs/requirements-baseline.md`
- `docs/maintainability-decomposition-thresholds.md` when the issue extends an existing hotspot instead of a clearly bounded module

This baseline is the governing implementation contract for **AegisOps**.

If this issue changes architecture, boundaries, naming, storage, security posture, approval model, or operating model, it MUST be handled through a separate ADR issue first.

No silent design drift is allowed.

---

## 1. Issue Type

Select one:
- Design
- Implementation
- Validation
- Documentation
- Refactor
- Operations

---

## 2. Behavior Delta

Describe exactly one behavior change introduced by this issue.

Format:
- Before:
- After:

Rules:
- MUST describe a single behavior delta
- MUST NOT bundle multiple unrelated changes
- MUST be testable
- MUST be scoped narrowly enough for safe review

---

## 3. Why This Change Exists

Describe why this issue is needed.

Include:
- problem being solved,
- risk being reduced,
- or capability being enabled.

---

## 4. In Scope

List only what this issue is allowed to change.

- <item>
- <item>
- <item>

---

## 5. Out of Scope

List what this issue MUST NOT change.

- <item>
- <item>
- <item>

This section is mandatory.
Anything not explicitly in scope is out of scope.

---

## 6. Fixed Preconditions

List baseline assumptions and existing constraints this issue depends on.

Examples:
- AegisOps runs on Ubuntu 24.04 LTS
- Docker deployment model is fixed
- reverse proxy access path is fixed
- approval model remains unchanged
- no secrets in Git
- naming must follow the AegisOps baseline

---

## 7. Affected Components

List all touched components.

Examples:
- opensearch
- sigma
- n8n
- postgres
- redis
- proxy
- docs
- scripts
- config

---

## 8. Implementation Notes

Provide concrete implementation constraints.

Examples:
- use existing repository structure only
- do not add new top-level directories
- use AegisOps naming conventions
- use `aegisops-*` compose project naming where applicable
- do not introduce write-capable workflow steps unless explicitly in scope
- use version-pinned images only

---

## 9. Security Impact

State one:
- None
- Low
- Medium
- High

Then explain why.

Also specify:
- Does this issue touch secrets handling? Yes / No
- Does this issue change approval requirements? Yes / No
- Does this issue expand network exposure? Yes / No
- Does this issue add write-capable behavior? Yes / No

If any answer is Yes, explain.

---

## 10. Operational Impact

Describe expected operational impact.

Include:
- deployment changes,
- runtime changes,
- backup implications,
- restore implications,
- monitoring implications.

---

## 11. Acceptance Criteria

Use testable statements only.

- [ ] <criterion>
- [ ] <criterion>
- [ ] <criterion>

Examples:
- [ ] The AegisOps service or configuration starts successfully through the approved Docker Compose entrypoint
- [ ] The change does not require plaintext secrets in Git
- [ ] Documentation is updated
- [ ] Validation steps are included
- [ ] No new forbidden shortcut is introduced

---

## 12. Validation Plan

Describe how the issue will be validated.

Examples:
- smoke test
- workflow execution test
- detector validation
- config lint
- restore dry run
- access control test

---

## 13. Rollback Plan

Describe how this issue can be rolled back safely.

Include:
- what to revert,
- whether data migration is involved,
- whether rollback is destructive or non-destructive.

---

## 14. Definition of Done

This issue is done only when:
- implementation matches the scoped behavior delta,
- acceptance criteria pass,
- docs are updated,
- security impact is reviewed,
- rollback steps are documented,
- and no forbidden shortcut is introduced.

---

## 15. Forbidden Shortcuts Check

The implementer MUST confirm all of the following:

- [ ] No `latest` image tag introduced
- [ ] No plaintext secret committed
- [ ] No ad-hoc directory added outside approved AegisOps structure
- [ ] No hidden architecture change embedded in implementation
- [ ] No production write-action introduced without policy treatment
- [ ] No undocumented manual step made mandatory
- [ ] No staging-validation bypass for detection content

---

## 16. Links

- Related ADR:
- Related issue(s):
- Related PR:
- Related runbook/doc:
