# AegisOps Repository Structure Baseline

This document intentionally defines the approved top-level repository layout and the purpose of each entry.

It translates the repository structure guidance from `docs/requirements-baseline.md` into a standalone baseline reference for future issues and reviews.

The current top-level structure remains transitional because it still reflects earlier repository phases and substrate-specific directory ownership.

Until a later ADR approves a repository rebaseline, contributors must treat the existing top-level tree as the reviewed baseline even where it does not yet match the long-term control-plane thesis.

## Approved Top-Level Structure

| Path | Purpose |
| ---- | ------- |
| `docs/` | Architecture, ADRs, parameters, runbooks, and other human-readable project documentation. |
| `opensearch/` | Transitional or optional OpenSearch repository assets such as compose definitions, detectors, templates, ILM policies, and snapshot-related configuration. Their presence does not make OpenSearch the product core. |
| `sigma/` | Transitional or optional Sigma repository assets, including reviewed rules, curated subsets, suppressions, field mappings, and placeholder markers that keep approved onboarding paths explicit before real rule content is added. Their presence does not make Sigma the product core. |
| `n8n/` | Transitional, optional, or experimental n8n workflow assets, approval patterns, credential templates, and webhook contract definitions. Their presence does not make n8n the product core or authority surface. |
| `ingest/` | Log ingestion assets such as pipelines, parsers, and source definitions. |
| `control-plane/` | Live AegisOps control-plane application code, service bootstrapping, adapters, tests, and service-local documentation for the approved runtime boundary. |
| `postgres/` | PostgreSQL deployment assets such as compose definitions for the n8n metadata and execution-state store, plus the reviewed schema and migration baseline for the AegisOps-owned control-plane boundary. |
| `proxy/` | Reverse proxy configuration for controlled access and TLS termination. |
| `scripts/` | Repository maintenance, validation, and operator helper scripts that support reproducible execution. |
| `config/` | Shared non-secret configuration artifacts and parameter files referenced by the platform components. |
| `.codex-supervisor/` | Tracked repository hygiene guidance for codex-supervisor; supervisor-local runtime state under this path must remain untracked. |
| `.github/` | Repository automation definitions such as GitHub Actions workflows used for baseline verification. |
| `.gitignore` | Repository-level ignore rules that keep transient local and supervisor execution artifacts out of the tracked baseline. |
| `.env.sample` | Sample environment variables for documentation and structure only; never real secrets or active environment state. |
| `LICENSE.txt` | Repository license text tracked as a stable project-level metadata file. |
| `README.md` | Project overview and contributor-facing orientation for the current approved baseline. |

## Repository Rules

- Secrets must not be committed anywhere in the repository.
- Real environment files are not approved repository assets.
- New top-level directories require explicit approval because they change the repository baseline.
- The reviewed top-level tree remains transitional relative to the control-plane thesis until a later ADR explicitly approves a different repository rebaseline.
- Only intentionally versioned repository guidance is approved under `.codex-supervisor/`; supervisor-local journals and other transient execution files in that directory must remain untracked.
- This document defines structure only and does not authorize runtime, deployment, or workflow implementation.

Within `sigma/`, placeholder marker files may reserve approved homes such as `curated/` and `suppressed/` before any real detection or suppression content is admitted.

Within `control-plane/`, live control-plane application code must stay separate from `postgres/control-plane/` so the runtime boundary does not dissolve into persistence-contract assets.

Within `postgres/`, `control-plane/schema.sql` and `control-plane/migrations/` define the reviewed control-plane schema baseline while staying separate from runtime application code, live deployment approval, credentials, and production migration execution.
