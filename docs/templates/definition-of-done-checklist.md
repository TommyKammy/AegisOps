# Definition of Done Checklist

This checklist applies to all AegisOps issues unless an approved ADR explicitly states otherwise.

## 1. Scope Integrity

- [ ] Exactly one behavior delta is implemented
- [ ] No unrelated change is bundled
- [ ] The issue stayed within its declared scope
- [ ] Out-of-scope items were not modified

## 2. Baseline Compliance

- [ ] The change complies with `docs/requirements-baseline.md`
- [ ] No architecture change was introduced without ADR
- [ ] AegisOps naming conventions were followed
- [ ] Repository structure was respected
- [ ] Storage and network rules were respected

## 3. Implementation Quality

- [ ] The implementation is reproducible
- [ ] The implementation uses version-controlled artifacts
- [ ] No manual-only operational dependency was introduced
- [ ] Configuration changes are explicit and reviewable
- [ ] Runtime behavior is understandable and supportable

## 4. Security and Safety

- [ ] No plaintext secret was committed
- [ ] No unapproved write-capable behavior was introduced
- [ ] Security impact was reviewed
- [ ] Auditability was preserved or improved
- [ ] Approval controls were preserved where required

## 5. Validation

- [ ] Validation steps are documented
- [ ] Validation was executed
- [ ] Expected results were confirmed
- [ ] Failure conditions are understood
- [ ] Logs or evidence of validation are available if needed

## 6. Operations Readiness

- [ ] Deployment impact is documented
- [ ] Monitoring impact is documented
- [ ] Backup impact is documented if applicable
- [ ] Restore impact is documented if applicable
- [ ] Rollback steps are documented

## 7. Documentation

- [ ] Relevant docs were updated
- [ ] Runbook impact was reviewed
- [ ] Parameter docs were updated if applicable
- [ ] Comments and documentation reflect actual behavior
- [ ] No stale placeholder text remains

## 8. Review Readiness

- [ ] The change is small enough for safe review
- [ ] Acceptance criteria are testable and satisfied
- [ ] The reviewer can understand what changed and why
- [ ] No forbidden shortcut was introduced

## 9. Final Confirmation

The issue is considered done only if all applicable items above are checked.

- [ ] Done
