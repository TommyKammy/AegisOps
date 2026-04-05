# AegisOps Control-Plane Service Home

This directory is the approved repository home for live AegisOps control-plane application code.

It is separate from `postgres/control-plane/`, which remains the reviewed persistence contract home for PostgreSQL schema and migration assets.

The first live control-plane service belongs here so the runtime boundary stays distinct from:

- OpenSearch analytics and detection assets under `opensearch/`;
- n8n workflow assets and execution-plane configuration under `n8n/`; and
- PostgreSQL persistence-contract assets under `postgres/control-plane/`.

Future implementation may add service source code, adapters, tests, and service-local documentation here, but it must preserve the approved ownership split defined in `docs/control-plane-runtime-service-boundary.md` and `docs/control-plane-state-model.md`.

Current scaffold:

- `main.py` is the local entrypoint for rendering read-only runtime, record-family, and reconciliation inspection views without assuming deployment tooling.
- `aegisops_control_plane/` contains the initial service module, boundary-aware adapters, and environment-backed runtime config.
- `tests/` contains focused service-root tests for the local runtime skeleton.
- `config/local.env.sample` defines non-secret local placeholders for PostgreSQL, OpenSearch, and n8n integration boundaries.

Current persistence status:

- The reviewed record families now have typed control-plane models plus runtime `save()` and `get()` behavior rooted under `control-plane/`.
- The local CLI now exposes read-only `inspect-records` and `inspect-reconciliation-status` views so operators and reviewers can inspect control-plane state without touching raw PostgreSQL tables directly.
- The runtime snapshot reports `persistence_mode="in_memory"` so the current branch does not imply live PostgreSQL-backed storage.
- Live PostgreSQL persistence remains follow-up work and depends on adding explicit PostgreSQL client tooling to the runtime environment.

This scaffold is intentionally minimal. It does not introduce real credentials, production deployment, analyst UI, or live detector execution.
