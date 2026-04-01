# Forbidden Shortcuts Lint Checklist

This checklist exists to detect implementation shortcuts that violate the AegisOps Platform Requirements Baseline.

## 1. Image and Version Hygiene

- [ ] No Docker image uses the `latest` tag
- [ ] Image versions are pinned explicitly
- [ ] Digest pinning is used where required or practical
- [ ] New runtime dependencies are declared explicitly

## 2. Secret Handling

- [ ] No real secrets are committed to Git
- [ ] No credentials are hardcoded in source files
- [ ] No real `.env` files are committed
- [ ] Secret placeholders remain clearly non-production
- [ ] Secret-loading behavior is documented

## 3. Repository and Directory Discipline

- [ ] No ad-hoc top-level directory was added
- [ ] No undeclared storage path was introduced
- [ ] No hidden state directory was added outside approved AegisOps structure
- [ ] File placement follows repository conventions
- [ ] New folders are justified and documented if added

## 4. Architecture Drift

- [ ] No architecture boundary changed without ADR
- [ ] No component silently absorbed another component’s responsibility
- [ ] No direct execution path bypasses the defined approval model
- [ ] No direct production access path bypasses the reverse proxy model
- [ ] No cross-cutting behavior change is hidden inside a local implementation issue

## 5. Detection Content Safety

- [ ] No Sigma or detector content is enabled in production without validation
- [ ] Required metadata exists for new detection content
- [ ] Suppression logic is documented
- [ ] Detection assumptions are explicit
- [ ] Production activation path is controlled

## 6. SOAR Safety

- [ ] No write-capable workflow step is mislabeled as read-only
- [ ] No hard-write action is added without approval controls
- [ ] No inbound raw alert directly triggers destructive action
- [ ] Conditional soft-write logic is documented
- [ ] Execution logging exists for state-changing actions

## 7. Networking and Access

- [ ] No new public-facing port was exposed without review
- [ ] No webhook endpoint is left unauthenticated without explicit approval
- [ ] No undocumented outbound dependency was introduced
- [ ] Access paths remain consistent with the baseline
- [ ] TLS posture is not weakened without approval

## 8. Operational Shortcuts

- [ ] No undocumented manual step is required for normal operation
- [ ] No backup responsibility is implicitly broken
- [ ] No restore path is made harder without documentation
- [ ] No operationally fragile workaround is treated as final design
- [ ] No environment-specific hack is left unexplained

## 9. Documentation Honesty

- [ ] Docs match actual implementation
- [ ] Comments do not describe behavior that does not exist
- [ ] README and runbook changes are included where needed
- [ ] Known limitations are stated honestly
- [ ] TODOs are not used to hide required baseline behavior

## 10. Final Shortcut Gate

If any item above cannot be checked, the change MUST NOT be considered complete unless:
- the exception is documented,
- the risk is explained,
- and the exception is approved through the correct process.

- [ ] Passed
