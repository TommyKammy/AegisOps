# Pull Request Review Checklist

This checklist is for human reviewers validating whether an AegisOps pull request is acceptable against the platform baseline.

Review this checklist together with `docs/requirements-baseline.md`, the issue scope, and any related ADRs.

## 1. Review Framing

- [ ] The pull request clearly states what changed and why
- [ ] The linked issue or problem statement is specific enough to review against
- [ ] The reviewer understands the intended behavior delta before evaluating details

## 2. Scope Discipline

- [ ] The change stays within the issue's declared scope
- [ ] No unrelated cleanup, refactor, or side quest is bundled into the pull request
- [ ] Out-of-scope files or behaviors were not changed without explicit justification
- [ ] The pull request is small enough for a reviewer to evaluate safely

## 3. Baseline Compliance

- [ ] The change is consistent with `docs/requirements-baseline.md`
- [ ] No architecture boundary changes appear without an approved ADR
- [ ] Component responsibilities remain separated as defined by the baseline
- [ ] Reproducibility, auditability, and rollback posture are preserved
- [ ] Repository structure, naming, storage, and network rules still align with the baseline

## 4. Security and Safety

- [ ] No plaintext secret, credential, or production-sensitive value appears in the pull request
- [ ] Approval gates were preserved for write-capable or destructive workflows
- [ ] Access paths, webhook exposure, and authentication posture were not weakened silently
- [ ] The change does not introduce an unreviewed write path, bypass, or privilege expansion
- [ ] Security impact is understandable from the pull request content and referenced docs

## 5. Forbidden Shortcut Detection

- [ ] No `latest` image tag, hidden dependency, or environment-specific hack is introduced
- [ ] No manual-only operational workaround is presented as the final design
- [ ] No architecture drift or responsibility bleed is hidden inside a local implementation change
- [ ] No baseline-required behavior is deferred behind TODOs or placeholder wording
- [ ] The pull request does not normalize a shortcut already forbidden by AegisOps policy

## 6. Verification and Evidence

- [ ] The pull request explains how the change was validated
- [ ] The reported verification is relevant to the actual behavior delta
- [ ] Claimed results are believable from the evidence shown in the pull request
- [ ] Failure modes, limits, or follow-up risks are stated when they matter for review

## 7. Documentation and Reviewer Usability

- [ ] Relevant docs, runbooks, templates, or parameter references were updated if needed
- [ ] The pull request description gives the reviewer enough context without hidden assumptions
- [ ] Naming, comments, and documentation match the implemented behavior
- [ ] A future reviewer or operator could understand the change without tribal knowledge

## 8. Final Review Gate

The reviewer should not approve the pull request if any applicable item above cannot be checked without a documented exception and correct approval path.

- [ ] Reviewed and acceptable
