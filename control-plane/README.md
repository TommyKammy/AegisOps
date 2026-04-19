# AegisOps Control-Plane Service Home

This directory is the approved repository home for live AegisOps control-plane application code.

It is separate from `postgres/control-plane/`, which remains the reviewed persistence contract home for PostgreSQL schema and migration assets.

The first live control-plane service belongs here so the runtime boundary stays distinct from:

- OpenSearch analytics and detection assets under `opensearch/`;
- n8n workflow assets and execution-plane configuration under `n8n/`; and
- PostgreSQL persistence-contract assets under `postgres/control-plane/`.

Future implementation may add service source code, adapters, tests, and service-local documentation here, but it must preserve the approved ownership split defined in `docs/control-plane-runtime-service-boundary.md` and `docs/control-plane-state-model.md`.

Current scaffold:

- `main.py` is the local entrypoint for the reviewed long-running control-plane runtime service plus read-only runtime, record-family, and reconciliation inspection views without assuming deployment tooling.
- `main.py` also exposes read-only analyst-assistant context inspection for control-plane records, reviewed context, and linked evidence.
- `aegisops_control_plane/` contains the initial service module, boundary-aware adapters, and environment-backed runtime config.
- `tests/` contains focused service-root tests for the local runtime skeleton.
- `config/local.env.sample` defines non-secret local placeholders for PostgreSQL, OpenSearch, and n8n integration boundaries.
- `deployment/first-boot/` contains reviewed Phase 16 bootstrap and entrypoint skeletons for the narrow first-boot control-plane, PostgreSQL, and reverse-proxy contract.

Current persistence status:

- The reviewed record families now have typed control-plane models plus PostgreSQL-backed runtime `save()`, `get()`, and `list()` behavior rooted under `control-plane/`.
- The runtime adapter validates records against the reviewed v1 schema invariants in `postgres/control-plane/schema.sql` before writing them into the `aegisops_control` PostgreSQL boundary.
- The approved reviewed local runtime path is the shipped CLI entrypoint: `python3 control-plane/main.py serve`, `python3 control-plane/main.py runtime`, `python3 control-plane/main.py inspect-records --family alert`, `python3 control-plane/main.py inspect-reconciliation-status`, `python3 control-plane/main.py inspect-case-detail --case-id <id>`, and `python3 control-plane/main.py inspect-assistant-context --family case --record-id <id>`.
- `python3 control-plane/main.py serve` is the reviewed long-running runtime surface for first boot; `python3 control-plane/main.py runtime` remains the read-only snapshot renderer for inspection and verification.
- Those runtime and inspection commands now construct the same reviewed control-plane service path, so PostgreSQL-backed runtime configuration remains the authoritative local operator flow while injected in-memory stores stay limited to tests and local doubles.
- The runtime snapshot now reports `persistence_mode="postgresql"` so the reviewed control-plane runtime makes its authoritative store explicit.
- Live read/write access still depends on PostgreSQL client tooling in the runtime environment, but the control-plane adapter no longer models the reviewed authority path as process-local in-memory state.

Phase 21 runtime hardening adds these reviewed contracts to the local service boundary:

- PostgreSQL DSNs, Wazuh ingress secrets, protected-surface proxy secrets, admin bootstrap tokens, and break-glass tokens may be loaded from explicit `*_FILE` bindings so runtime secrets can come from mounted secret files instead of tracked worktree env values.
- The same reviewed runtime bindings may also resolve from OpenBao through explicit `*_OPENBAO_PATH` references plus `AEGISOPS_OPENBAO_ADDRESS`, `AEGISOPS_OPENBAO_TOKEN` or `AEGISOPS_OPENBAO_TOKEN_FILE`, and the optional `AEGISOPS_OPENBAO_KV_MOUNT`. OpenBao references fail closed when the backend is unavailable, the secret path is unreadable, or the resolved value is empty.
- Operator-facing read and write routes now accept either direct loopback access for local reviewed testing or reviewed reverse-proxy access with `X-Forwarded-Proto: https`, `X-AegisOps-Proxy-Secret`, `X-AegisOps-Proxy-Service-Account`, `X-AegisOps-Authenticated-Identity`, and `X-AegisOps-Authenticated-Role`.
- Administrative runtime routes live under `/admin/` and require the protected-surface contract plus an explicit bootstrap or break-glass token in the request body.
- The break-glass contract is time-bounded: `/admin/break-glass/activate` rejects expiry windows longer than 60 minutes and requires a ticket identifier and reason.

The reviewed secret-delivery boundary for issue `#565` now covers the live control-plane bindings listed above and also defines the only approved delivery contract for Shuffle, assistant-provider, and reviewed coordination integration credentials. When those credential-bearing integrations gain concrete runtime bindings, they must use the same explicit file-backed or OpenBao-backed pattern rather than ad hoc `.env` sprawl or plaintext Git-tracked values, and until then they remain blocked from live credential use instead of silently falling back to weaker local secret handling.

This scaffold is intentionally minimal. It does not introduce real credentials, production deployment, analyst UI, or live detector execution.
