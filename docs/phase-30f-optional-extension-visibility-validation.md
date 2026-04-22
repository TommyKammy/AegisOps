# Phase 30F Optional-Extension Visibility Validation

- Validation status: PASS
- Scope: confirm the reviewed Phase 30F optional-extension visibility contract keeps enabled, disabled-by-default, unavailable, and degraded posture distinct while preserving subordinate optional-context semantics in the operator console.
- Reviewed sources: `README.md`, `docs/phase-30f-optional-extension-visibility-boundary.md`, `docs/phase-30-react-admin-foundation-and-read-only-operator-console-boundary.md`, `docs/phase-30e-assistant-advisory-integration-boundary.md`, `docs/phase-28-optional-endpoint-evidence-pack-boundary.md`, `docs/phase-29-reviewed-ml-shadow-mode-boundary.md`, `docs/phase-29-optional-suricata-evidence-pack-boundary.md`, `docs/runbook.md`, `apps/operator-ui/src/app/optionalExtensionVisibility.tsx`, `apps/operator-ui/src/app/optionalExtensionVisibility.test.tsx`, `apps/operator-ui/src/app/OperatorRoutes.test.tsx`, `control-plane/tests/test_phase30f_operator_ui_validation.py`

## Verdict

Phase 30F validation is now locked at the narrow boundary required by issue `#699`.

The shared taxonomy distinguishes `enabled`, `disabled-by-default`, `unavailable`, and `degraded` without collapsing disabled-by-default posture into generic unavailability.

Enabled posture still fails closed unless backend-owned availability is explicit, so client-local enablement hints do not become trusted status on their own.

Optional-extension visibility remains subordinate context rather than authoritative lifecycle truth, and mainline expectation messaging remains explicit when optional paths are absent.

## Locked Behaviors

- disabled-by-default posture remains distinct from unavailable posture for optional endpoint evidence, optional network evidence, and ML shadow surfaces
- enabled posture still fails closed unless backend-owned availability is explicit
- degraded posture remains visible without being normalized into generic missing data
- optional-extension visibility remains subordinate context rather than authoritative lifecycle truth
- mainline expectation messaging remains explicit when optional paths are absent

## Evidence

`apps/operator-ui/src/app/optionalExtensionVisibility.test.tsx` locks the mapper contract so disabled-by-default optional families stay visible as intentional mainline posture, enabled status requires backend-reported availability, and degraded state keeps precedence over weaker optional signals.

`apps/operator-ui/src/app/OperatorRoutes.test.tsx` locks overview and readiness rendering so the operator console shows subordinate optional-extension badges and mainline expectation text without overstating optional-path trouble as workflow failure.

`control-plane/tests/test_phase30f_operator_ui_validation.py` locks the validation document, the operator-ui regression coverage, and the control-plane readiness defaults that keep optional families non-blocking and subordinate by authority mode.

## Verification

- `python3 -m unittest control-plane.tests.test_phase30f_operator_ui_validation`
- `npm --prefix apps/operator-ui test -- --run src/app/optionalExtensionVisibility.test.tsx src/app/OperatorRoutes.test.tsx`
- `npm --prefix apps/operator-ui run build`
