# Phase 44 Pilot Ingress and Operator Surface Closure Validation

- Validation status: PASS
- Reviewed on: 2026-04-28
- Scope: confirm that the Phase 44 pilot ingress and operator surface closure is documented as a repo-owned contract without changing runtime behavior, operator UI behavior, or authority posture.
- Reviewed sources: `docs/phase-44-pilot-ingress-and-operator-surface-closure-boundary.md`, `control-plane/deployment/first-boot/docker-compose.yml`, `proxy/nginx/conf.d-first-boot/control-plane.conf`, `control-plane/tests/test_phase17_first_boot_runtime_artifacts.py`, `control-plane/tests/test_phase21_runtime_auth_validation.py`, `apps/operator-ui/src/auth/session.ts`, `apps/operator-ui/src/auth/session.test.ts`, `apps/operator-ui/src/app/OperatorRoutes.test.tsx`, `apps/operator-ui/e2e/operator-workflows.spec.ts`, `scripts/run-phase-37-runtime-smoke-gate.sh`, `scripts/test-verify-ci-operator-ui-workflow-coverage.sh`, `.github/workflows/ci.yml`

## Verdict

Phase 44 is closed as a documentation-only pilot ingress and operator surface contract.

The reviewed first-boot proxy remains the only pilot operator ingress surface for the documented route families. Protected identity headers remain normalized at the proxy boundary before backend protected-surface authorization evaluates proxy, provider, subject, identity, role, HTTPS, and trusted-peer signals.

Backend and operator-ui role canonicalization remain aligned around reviewed canonical roles while backend authorization remains the enforcement boundary.

Runtime smoke ingress evidence remains a bounded proof of proxy-reached runtime and operator inspection paths. It does not perform write-capable workflow actions and does not become workflow truth.

The operator-ui CI gate remains the frontend quality gate for the reviewed thin-client surface. It does not move authority from backend records into browser state.

No runtime behavior, operator UI behavior, or authority posture changes are introduced by this validation document.

## Locked Behaviors

- first-boot operator ingress remains anchored to `control-plane/deployment/first-boot/docker-compose.yml` and `proxy/nginx/conf.d-first-boot/control-plane.conf`
- protected identity header normalization strips caller-supplied protected AegisOps identity headers at the reviewed proxy boundary
- backend protected-surface auth fails closed for missing, malformed, placeholder, untrusted, or unauthorized proxy and identity signals
- backend and operator-ui role canonicalization keep `analyst`, `approver`, and `platform_admin` as reviewed canonical role names
- runtime smoke ingress evidence uses the reviewed proxy path and remains read-only for operator inspection
- operator-ui CI proves typecheck, tests, and build for the browser surface without promoting the browser to workflow authority
- AegisOps backend records remain authoritative over operator UI, proxy evidence, external tickets, assistant output, downstream receipts, and optional substrate state

## Evidence

`docs/phase-44-pilot-ingress-and-operator-surface-closure-boundary.md` defines the in-scope and out-of-scope boundary, fail-closed conditions, verifier references, and authority notes for the closed Phase 44 pilot ingress contract.

`control-plane/deployment/first-boot/docker-compose.yml` preserves the repo-owned first-boot control-plane, PostgreSQL, and proxy composition used by the reviewed ingress path.

`proxy/nginx/conf.d-first-boot/control-plane.conf` preserves the first-boot proxy route set and strips protected AegisOps identity headers before traffic reaches the backend.

`control-plane/tests/test_phase17_first_boot_runtime_artifacts.py` locks the first-boot proxy route posture and protected identity header normalization behavior. The test proves caller-supplied protected identity headers are stripped and not passed through as trusted inputs.

`control-plane/tests/test_phase21_runtime_auth_validation.py` locks backend protected-surface authentication behavior. The suite covers reviewed proxy peer, HTTPS, proxy secret, proxy service account, reviewed identity provider, subject, identity, role, allowed-role, and placeholder credential fail-closed behavior.

`apps/operator-ui/src/auth/session.ts` and `apps/operator-ui/src/auth/session.test.ts` lock operator-ui role canonicalization and invalid-session handling. The UI normalizes reviewed role claims into canonical lower-case names and rejects malformed or unreviewed claims instead of treating client state as authority.

`scripts/run-phase-37-runtime-smoke-gate.sh` captures runtime smoke ingress evidence through the reviewed proxy path using `--env-file <runtime-env-file>` and `--evidence-dir <evidence-dir>`. The evidence manifest records protected runtime inspection, readiness, startup status, bounded logs, read-only operator ingress, and first low-risk action preconditions without performing a workflow write.

`scripts/test-verify-ci-operator-ui-workflow-coverage.sh` and `.github/workflows/ci.yml` keep the operator-ui CI gate explicit with `npm run typecheck --workspace @aegisops/operator-ui`, `npm run test --workspace @aegisops/operator-ui`, and `npm run build --workspace @aegisops/operator-ui`.

## Validation Commands

- `python3 -m unittest control-plane.tests.test_phase44_pilot_ingress_operator_surface_docs`
- `python3 -m unittest control-plane.tests.test_phase17_first_boot_runtime_artifacts`
- `python3 -m unittest control-plane.tests.test_phase21_runtime_auth_validation`
- `npm --prefix apps/operator-ui test -- --run src/auth/session.test.ts`
- `bash scripts/verify-architecture-runbook-validation.sh`
- `bash scripts/test-verify-ci-publishable-path-hygiene.sh`
- `node <codex-supervisor-root>/dist/index.js issue-lint 889 --config <supervisor-config-path>`

## Non-Expansion Notes

Phase 44 validation is intentionally retroactive and documentation-only.

It does not add proxy routes, runtime routes, backend authorization behavior, operator UI features, role names, production RBAC behavior, workflow writes, or deployment requirements.

The reviewed command references use repo-relative paths, documented environment placeholders, and explicit `<codex-supervisor-root>` and `<supervisor-config-path>` placeholders instead of workstation-local absolute paths.

Operator UI and proxy evidence do not become workflow truth. Browser state, operator UI state, external tickets, assistant output, downstream receipts, runtime smoke output, and optional substrate state remain subordinate context unless a reviewed AegisOps backend record explicitly binds them into the authoritative record chain.
