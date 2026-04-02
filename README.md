# AegisOps

**AegisOps** is an internal SOC + SOAR platform blueprint designed for flexible deployment across on-premise infrastructure and cloud environments, including AWS and other providers.

- **OpenSearch** — SIEM analytics and detection
- **Sigma** — curated, reviewable detection logic
- **n8n** — approval-gated orchestration, enrichment, and response

AegisOps is built to support **human-controlled security operations** — delivering a platform that is explainable, auditable, and designed to scale safely across deployment environments.

---

## Status

> This repository is currently in the foundation-building phase. It is **not yet a production-ready SOC platform**.

Current scope:

- Platform baseline definition
- Architecture design and operating guidance
- Repository scaffolding
- Parameter catalog structure
- Implementation guardrails for AI-assisted development

---

## Core Principles

- **Detection and execution are separated** — OpenSearch detects; n8n orchestrates
- **Human approval is required by default for write or destructive actions**
- **Secrets are never committed to Git**
- **Platform behavior must be reproducible from version-controlled artifacts**
- **Architecture changes require explicit review**
- **One issue represents one behavior delta**

These principles ensure the platform remains governable, auditable, and safe to evolve — regardless of the underlying infrastructure.

---

## Architecture Overview

```text
Log Sources
  -> Ingest
  -> OpenSearch
  -> Detection Content
  -> Findings / Alerts
  -> n8n
  -> Enrichment / Approval / Routing
  -> Controlled Downstream Actions
```

Supporting services:

- **PostgreSQL** — n8n metadata and execution state
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

Within `sigma/`, the `curated/` directory is reserved for reviewed Sigma rules that are approved for future onboarding, and the `suppressed/` directory is reserved for future documented suppression decisions. Placeholder markers may exist there before any actual rule or suppression content is admitted.

---

## Documentation

Key documents that serve as the source of truth for implementation decisions:

- `docs/requirements-baseline.md`
- `docs/architecture.md`
- `docs/canonical-telemetry-schema-baseline.md`
- `docs/source-onboarding-contract.md`
- `docs/sigma-to-opensearch-translation-strategy.md`
- `docs/detection-lifecycle-and-rule-qa-framework.md`
- `docs/secops-domain-model.md`
- `docs/auth-baseline.md`
- `docs/response-action-safety-model.md`
- `docs/control-plane-state-model.md`
- `docs/runbook.md`
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
