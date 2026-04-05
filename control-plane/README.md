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
- The in-memory authoritative path fails closed against the reviewed v1 schema invariants in `postgres/control-plane/schema.sql` for lifecycle-state enums, required linkage fields, non-empty required tuple sets, and reconciliation timestamp ordering before records become inspectable runtime state.
- The approved reviewed local runtime path is the shipped CLI entrypoint: `python3 control-plane/main.py runtime`, `python3 control-plane/main.py inspect-records --family alert`, and `python3 control-plane/main.py inspect-reconciliation-status`.
- Those inspection commands are explicitly read-only and run against the same process-local `persistence_mode="in_memory"` runtime used by the current local entrypoint, so they can render empty or locally-seeded inspection views without touching raw PostgreSQL tables directly.
- The runtime snapshot reports `persistence_mode="in_memory"` to make clear that the current branch does not imply live PostgreSQL-backed storage, write-capable runtime authority, or production deployment readiness.
- Live PostgreSQL persistence remains follow-up work and depends on adding explicit PostgreSQL client tooling to the runtime environment.

This scaffold is intentionally minimal. It does not introduce real credentials, production deployment, analyst UI, or live detector execution.
