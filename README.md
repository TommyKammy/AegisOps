# AegisOps

**AegisOps** is a governed SecOps control plane above external detection and automation substrates.

- **OpenSearch** — optional or transitional analytics substrate, not the product core
- **Sigma** — optional or transitional rule-definition format or translation source, not the product core
- **n8n** — optional, transitional, or experimental orchestration substrate, not the product core
- **Control Plane Runtime** — future authoritative AegisOps service boundary for platform state and reconciliation

AegisOps is built to support **human-controlled security operations** with an explicit authority boundary for approvals, evidence, action intent, and reconciliation.

OpenSearch, Sigma, and n8n remain repository-tracked assets, but they are subordinate to the approved control-plane thesis and must not redefine the product narrative around themselves.

---

## Status

> The control-plane thesis is approved, but the AegisOps-owned control-plane runtime is **not yet live**.

Current scope:

- Platform baseline definition
- Architecture design and operating guidance
- Repository scaffolding
- Parameter catalog structure
- Implementation guardrails for AI-assisted development

Within that scope, Wazuh is the initial standard detection substrate, Shuffle is the initial standard routine automation substrate, and the AegisOps-owned control-plane runtime remains not yet live.

---

## Core Principles

- **Detection, control, automation, and execution are explicitly separated**
- **AegisOps is the authority for policy-sensitive workflow truth** — alerts, cases, evidence, approval decisions, action requests, and reconciliation remain AegisOps-owned records
- **Detection substrates produce upstream analytic signals** — Wazuh is the initial standard detection substrate, while OpenSearch and Sigma remain optional or transitional support choices
- **Automation substrates execute only approved delegated work** — Shuffle is the initial standard routine automation substrate, while n8n remains optional, transitional, or experimental
- **Human approval is required by default for write or destructive actions**
- **Secrets are never committed to Git**
- **Platform behavior must be reproducible from version-controlled artifacts**
- **Architecture changes require explicit review**
- **One issue represents one behavior delta**

These principles ensure the platform remains governable, auditable, and safe to evolve across changing substrate choices.

---

## Architecture Overview

```text
Substrate Detection Record
  -> Analytic Signal
  -> Alert or Case
  -> Action Request
  -> Approval Decision
  -> Approved Automation Substrate or Executor
  -> Reconciliation
```

Supporting services:

- **PostgreSQL** — reviewed control-plane schema baseline and any separately governed substrate-local metadata stores
- **Redis** — optional future component for queue-based scaling
- **Reverse Proxy** — controlled user-facing access and TLS termination

---

## Repository Structure

```text
aegisops/
├── docs/
├── opensearch/
├── sigma/
├── n8n/
├── control-plane/
├── postgres/
├── ingest/
├── proxy/
├── scripts/
├── config/
└── .env.sample
```

For the detailed approved structure, see:

- `docs/repository-structure-baseline.md`
- `docs/requirements-baseline.md`

The current top-level tree still includes older substrate-specific directories and should be treated as transitional until a later ADR approves any substrate-specific repository rebaseline.

Within `sigma/`, the `curated/` directory is reserved for reviewed Sigma rules that are approved for future onboarding, and the `suppressed/` directory is reserved for future documented suppression decisions. Placeholder markers may exist there before any actual rule or suppression content is admitted.

Within `control-plane/`, the first live AegisOps-owned control-plane runtime will live as application code and service-local tests.

Within `postgres/`, the `control-plane/` directory is the repository home for the reviewed AegisOps-owned control-plane schema baseline and migration assets. It does not authorize live deployment, production data migration, or credentials.

That schema boundary remains separate from n8n-owned PostgreSQL metadata and execution-state tables, and future rollout, access-control, and index-tuning work stays explicit.

---

## Documentation

Key documents that serve as the source of truth for implementation decisions:

- `docs/requirements-baseline.md`
- `docs/architecture.md`
- `docs/canonical-telemetry-schema-baseline.md`
- `docs/source-onboarding-contract.md`
- `docs/sigma-to-opensearch-translation-strategy.md`
- `docs/detection-lifecycle-and-rule-qa-framework.md`
- `docs/phase-6-initial-telemetry-slice.md`
- `docs/secops-domain-model.md`
- `docs/secops-business-hours-operating-model.md`
- `docs/auth-baseline.md`
- `docs/asset-identity-privilege-context-baseline.md`
- `docs/response-action-safety-model.md`
- `docs/control-plane-state-model.md`
- `docs/control-plane-runtime-service-boundary.md`
- `docs/retention-evidence-and-replay-readiness-baseline.md`
- `docs/runbook.md`
- `docs/source-families/`
- `docs/repository-structure-baseline.md`
- `docs/network-exposure-and-access-path-policy.md`
- `docs/storage-layout-and-mount-policy.md`
- `docs/parameters/`
- `docs/adr/`

These documents define the current baseline and take precedence over implementation assumptions unless superseded by an approved ADR.

---

## Development Approach

- Small, reviewable changes
- Explicit scope boundaries
- Baseline compliance
- Documentation-first design
- AI-assisted implementation with guardrails

The repository is structured so that implementation can proceed safely through tightly scoped issues and validated pull requests.

---

## Non-Goals for the Current Phase

The following are intentionally out of scope at this stage:

- Full autonomous response
- Full log source coverage
- Full HA / DR production architecture
- Multi-tenant SOC operations
- Unrestricted destructive automation

These may be addressed in later phases only if explicitly designed, reviewed, and approved.

---

## Contributing

- Follow the approved naming conventions
- Keep changes small and reviewable
- Do not introduce architecture drift silently
- Do not commit secrets or active environment files
- Do not bypass approval and validation expectations

Before implementing cross-cutting changes, create or reference an ADR.

Useful references:

- `docs/templates/issue-template.md`
- `docs/templates/definition-of-done-checklist.md`
- `docs/templates/forbidden-shortcuts-lint-checklist.md`
- `docs/contributor-naming-guide.md`

---

## License

This project is licensed under the [MIT License](LICENSE).
