# AegisOps Compose Skeleton Overview

This document explains the purpose and limits of the tracked Docker Compose skeletons in this repository.

It consolidates the approved scaffolding intent for contributors and reviewers before runtime implementation work expands.

## 1. Purpose

The compose skeletons exist to provide placeholder-safe scaffolding for approved AegisOps component boundaries.

They are not production-ready deployment definitions.

They do not introduce new architecture, deployment behavior, or runtime defaults.

## 2. What The Skeletons Are For

- Reserving the expected component directories and Compose project names for AegisOps assets.
- Showing placeholder-safe service boundaries for OpenSearch, n8n, PostgreSQL, proxy, and ingest roles.
- Keeping contributor examples aligned to the approved documentation baseline before implementation details are finalized.

Treat the skeletons as contributor scaffolding, not as a complete deployment design.

The current skeletons help contributors see where runtime artifacts will eventually live without implying that the placeholder comments, tags, mounts, or profiles are ready for deployment.

## 3. What Remains Out of Scope

- Live secrets, active environment files, and production credential material.
- Final host paths, certificate rollout, ingress publication, and production exposure decisions beyond documented policy.
- Complete service hardening, scaling, clustering, backup automation, restore automation, or environment-specific deployment tuning.
- Any change that would expand the approved architecture or operational model without a separately reviewed baseline or ADR update.

Do not treat placeholder paths, placeholder environment values, or placeholder profiles as approved production settings.

## 4. Contributor Guidance

When updating a compose skeleton, preserve the current placeholder-safe posture unless a separately approved issue or ADR changes the baseline.

Use the skeletons to keep names, roles, and directory ownership aligned while deferring runtime-specific implementation details to the approved baseline and policy documents.

If a proposed edit would add direct backend exposure, live credential handling, production mount paths, or environment-specific automation, stop and update the governing baseline documents first instead of treating the skeleton itself as the source of truth.

## 5. Reference Documents

- `docs/requirements-baseline.md`
- `docs/contributor-naming-guide.md`
- `docs/network-exposure-and-access-path-policy.md`
- `docs/storage-layout-and-mount-policy.md`
- `docs/repository-structure-baseline.md`
