# AegisOps OpenSearch Index Template Placeholders

This document explains the purpose and current limits of the tracked OpenSearch index template placeholders.

## 1. Purpose

These files exist to reserve the approved OpenSearch log index-template names and directory ownership for AegisOps contributors.

They are placeholders only and are not production-ready index templates.

## 2. Placeholder Scope

- Keep the approved `aegisops-logs-<family>-*` naming pattern visible in version control.
- Reserve a stable location for future index-template work under the approved `opensearch/` repository boundary.
- Make it clear that the current JSON files are scaffolding for contributors and reviewers, not finished OpenSearch content.

## 3. What Remains Out of Scope

Do not treat the current files as approved mappings, settings, shard plans, lifecycle policies, or ingestion contracts.

- Production field mappings and analyzers.
- Index lifecycle management, rollover, and retention behavior.
- Environment-specific shard counts, replica counts, or performance tuning.
- Template priorities, aliases, or pipeline attachments beyond the current placeholder state.

## 4. Contributor Guidance

Leave runtime behavior unchanged unless a separately approved issue or ADR expands the baseline.

When updating these placeholders, keep them descriptive-only and aligned to the approved naming baseline until production template requirements are formally documented.

## 5. Reference Documents

- `docs/requirements-baseline.md`
- `docs/contributor-naming-guide.md`
- `docs/repository-structure-baseline.md`
