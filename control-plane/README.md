# AegisOps Control-Plane Service Home

This directory is the approved repository home for live AegisOps control-plane application code.

It is separate from `postgres/control-plane/`, which remains the reviewed persistence contract home for PostgreSQL schema and migration assets.

The first live control-plane service belongs here so the runtime boundary stays distinct from:

- OpenSearch analytics and detection assets under `opensearch/`;
- n8n workflow assets and execution-plane configuration under `n8n/`; and
- PostgreSQL persistence-contract assets under `postgres/control-plane/`.

Future implementation may add service source code, adapters, tests, and service-local documentation here, but it must preserve the approved ownership split defined in `docs/control-plane-runtime-service-boundary.md` and `docs/control-plane-state-model.md`.
