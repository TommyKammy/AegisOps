# AegisOps Repository Structure Baseline

This document intentionally defines the approved top-level repository layout and the purpose of each entry.

It translates the repository structure guidance from `docs/requirements-baseline.md` into a standalone baseline reference for future issues and reviews.

## Approved Top-Level Structure

| Path | Purpose |
| ---- | ------- |
| `docs/` | Architecture, ADRs, parameters, runbooks, and other human-readable project documentation. |
| `opensearch/` | OpenSearch configuration assets such as compose definitions, detectors, templates, ILM policies, and snapshot-related configuration. |
| `sigma/` | Sigma detection content, including reviewed rules, curated subsets, suppressions, and field mappings. |
| `n8n/` | n8n workflow assets, approval patterns, credential templates, and webhook contract definitions. |
| `ingest/` | Log ingestion assets such as pipelines, parsers, and source definitions. |
| `proxy/` | Reverse proxy configuration for controlled access and TLS termination. |
| `scripts/` | Repository maintenance, validation, and operator helper scripts that support reproducible execution. |
| `config/` | Shared non-secret configuration artifacts and parameter files referenced by the platform components. |
| `.env.sample` | Sample environment variables for documentation and structure only; never real secrets or active environment state. |

## Repository Rules

- Secrets must not be committed anywhere in the repository.
- Real environment files are not approved repository assets.
- New top-level directories require explicit approval because they change the repository baseline.
- This document defines structure only and does not authorize runtime, deployment, or workflow implementation.
