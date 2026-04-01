# AegisOps Storage Layout and Mount Policy

This document defines the approved persistent storage layout and mount policy for core AegisOps stateful services.

It supplements the high-level storage rules in `docs/requirements-baseline.md` and is limited to policy, naming, and separation requirements.

No runtime storage implementation, backup job definition, or restore automation is introduced by this document.

## 1. Purpose

The storage policy exists to make persistent data placement explicit, reviewable, and recoverable.

It defines:

- which components require dedicated persistent host paths,
- how those mount points are named,
- what data must remain separated from backup targets, and
- why VM snapshots are insufficient as the primary protection mechanism.

## 2. Mount Point Naming Policy

Persistent host paths must use stable, human-readable names under a product-scoped root.

Approved pattern:

`/srv/aegisops/<component-purpose>`

Approved examples:

- `/srv/aegisops/opensearch-data`
- `/srv/aegisops/postgres-data`
- `/srv/aegisops/n8n-data`

Backup targets must use a separate product-scoped root so operators can distinguish runtime data from backup data without inference.

Approved backup root pattern:

`/srv/aegisops-backup/<component-purpose>`

Approved example:

- `/srv/aegisops-backup/opensearch-snapshots`

Mount point names must remain role-specific and must not be reused across different stateful services.

## 3. Persistent Storage Layout

### 3.1 OpenSearch

OpenSearch persistent data must be mounted only from a dedicated host path.

Approved primary data path example:

- `/srv/aegisops/opensearch-data`

Policy rules:

- The OpenSearch data path is reserved for OpenSearch runtime state only.
- OpenSearch data must not share its primary mount with PostgreSQL, n8n, or backup targets.
- OpenSearch snapshot repositories, when used, must point to backup storage rather than the primary data mount.
- OpenSearch container filesystem layers must not be relied on for any persistent indices, shards, or cluster metadata.

### 3.2 PostgreSQL

PostgreSQL persistent data must be mounted only from a dedicated host path.

Approved primary data path example:

- `/srv/aegisops/postgres-data`

Policy rules:

- The PostgreSQL data path is reserved for database files, transaction state, and database metadata only.
- PostgreSQL data must not share its primary mount with OpenSearch, n8n, or backup targets.
- PostgreSQL backup artifacts must be written to a separate backup mount, not into the active database data path.
- PostgreSQL container filesystem layers must not be relied on for persistent database state.

### 3.3 n8n

n8n persistent state must be mounted only from a dedicated host path.

Approved primary data path example:

- `/srv/aegisops/n8n-data`

Policy rules:

- The n8n data path is reserved for n8n configuration, encryption-related state, local files that n8n persists, and other application state that must survive container replacement.
- n8n state must not share its primary mount with OpenSearch, PostgreSQL, or backup targets.
- n8n workflow exports stored in Git are not a substitute for persistent runtime state.
- n8n container filesystem layers must not be relied on for persistent application state.

## 4. Backup Separation Policy

Backup storage must not share the same filesystem mount as primary runtime data.

Approved backup root example:

- `/srv/aegisops-backup`

Policy rules:

- Primary runtime mounts and backup mounts must remain logically separate so a runtime storage failure does not automatically destroy the backup target.
- Backup retention, scheduling, and restore ownership remain separate operational concerns and are not changed by this document.
- OpenSearch backup artifacts must be stored outside `/srv/aegisops/opensearch-data`.
- PostgreSQL backup artifacts must be stored outside `/srv/aegisops/postgres-data`.
- n8n backup artifacts, if maintained, must be stored outside `/srv/aegisops/n8n-data`.

## 5. VM Snapshot Limitation

Hypervisor VM snapshots are not an application-aware backup for OpenSearch or PostgreSQL.

VM snapshots may support short-lived administrative tasks such as controlled maintenance windows or rapid rollback of a failed infrastructure change, but they have strict limitations:

- they do not replace application-consistent OpenSearch snapshot procedures,
- they do not replace PostgreSQL backup and restore procedures,
- they may capture an inconsistent write state for busy data services,
- and they must not be treated as the sole recovery method for persistent platform data.

Operators must treat VM snapshots as supplemental infrastructure tooling only, not as the primary persistence or backup strategy for AegisOps stateful services.
