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
- `main.py` also exposes read-only analyst-assistant context inspection for control-plane records, reviewed context, and linked evidence.
- `aegisops_control_plane/` contains the initial service module, boundary-aware adapters, and environment-backed runtime config.
- `tests/` contains focused service-root tests for the local runtime skeleton.
- `config/local.env.sample` defines non-secret local placeholders for PostgreSQL, OpenSearch, and n8n integration boundaries.

Current persistence status:

- The reviewed record families now have typed control-plane models plus PostgreSQL-backed runtime `save()`, `get()`, and `list()` behavior rooted under `control-plane/`.
- The runtime adapter validates records against the reviewed v1 schema invariants in `postgres/control-plane/schema.sql` before writing them into the `aegisops_control` PostgreSQL boundary.
- The approved reviewed local runtime path is the shipped CLI entrypoint: `python3 control-plane/main.py runtime`, `python3 control-plane/main.py inspect-records --family alert`, `python3 control-plane/main.py inspect-reconciliation-status`, and `python3 control-plane/main.py inspect-assistant-context --family case --record-id <id>`.
- Those runtime and inspection commands now construct the same reviewed control-plane service path, so PostgreSQL-backed runtime configuration remains the authoritative local operator flow while injected in-memory stores stay limited to tests and local doubles.
- The runtime snapshot now reports `persistence_mode="postgresql"` so the reviewed control-plane runtime makes its authoritative store explicit.
- Live read/write access still depends on PostgreSQL client tooling in the runtime environment, but the control-plane adapter no longer models the reviewed authority path as process-local in-memory state.

This scaffold is intentionally minimal. It does not introduce real credentials, production deployment, analyst UI, or live detector execution.
