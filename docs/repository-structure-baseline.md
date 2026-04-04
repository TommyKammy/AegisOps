# AegisOps Repository Structure Baseline

This document intentionally defines the approved top-level repository layout and the purpose of each entry.

It translates the repository structure guidance from `docs/requirements-baseline.md` into a standalone baseline reference for future issues and reviews.

## Approved Top-Level Structure

| Path | Purpose |
| ---- | ------- |
| `docs/` | Architecture, ADRs, parameters, runbooks, and other human-readable project documentation. |
| `opensearch/` | OpenSearch configuration assets such as compose definitions, detectors, templates, ILM policies, and snapshot-related configuration. |
| `sigma/` | Sigma detection content, including reviewed rules, curated subsets, suppressions, field mappings, and placeholder markers that keep approved onboarding paths explicit before real rule content is added. |
| `n8n/` | n8n workflow assets, approval patterns, credential templates, and webhook contract definitions. |
| `ingest/` | Log ingestion assets such as pipelines, parsers, and source definitions. |
| `postgres/` | PostgreSQL deployment assets such as compose definitions for the n8n metadata and execution-state store, plus placeholder schema and migration assets for the future AegisOps-owned control-plane boundary. |
| `proxy/` | Reverse proxy configuration for controlled access and TLS termination. |
| `scripts/` | Repository maintenance, validation, and operator helper scripts that support reproducible execution. |
| `config/` | Shared non-secret configuration artifacts and parameter files referenced by the platform components. |
| `.codex-supervisor/` | Tracked supervisor coordination metadata such as issue journals that document branch-local execution history; ephemeral run state under this path must remain untracked. |
| `.github/` | Repository automation definitions such as GitHub Actions workflows used for baseline verification. |
| `.env.sample` | Sample environment variables for documentation and structure only; never real secrets or active environment state. |
| `LICENSE.txt` | Repository license text tracked as a stable project-level metadata file. |
| `README.md` | Project overview and contributor-facing orientation for the current approved baseline. |

## Repository Rules

- Secrets must not be committed anywhere in the repository.
- Real environment files are not approved repository assets.
- New top-level directories require explicit approval because they change the repository baseline.
- Only reviewable supervisor metadata such as tracked issue journals are approved under `.codex-supervisor/`; transient execution files in that directory must remain untracked.
- This document defines structure only and does not authorize runtime, deployment, or workflow implementation.

Within `sigma/`, placeholder marker files may reserve approved homes such as `curated/` and `suppressed/` before any real detection or suppression content is admitted.

Within `postgres/`, placeholder files may reserve approved homes such as `control-plane/schema.sql` and `control-plane/migrations/` before any live control-plane service, credentials, or runtime migration execution is approved.
