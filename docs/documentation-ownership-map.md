# AegisOps Documentation Ownership Map

This document records the default ownership map for major AegisOps documentation areas in one place.

It supplements existing document-control metadata and does not replace per-document owner fields where those fields already exist.

## 1. Purpose

This map makes documentation accountability explicit for the baseline artifacts that govern implementation and operations.

It exists so reviewers can determine, without ambiguity, which team owns each major documentation area before related changes are merged.

This document defines ownership only. It does not change implementation behavior, runtime approval paths, or repository tooling.

## 2. Ownership Terms

Document owner means the team accountable for keeping the document area current, reviewable, and aligned with the approved baseline and accepted ADRs.

For this map, ownership includes maintaining document-control metadata where applicable, reviewing proposed updates for the area, and resolving ambiguity when related artifacts drift out of sync.

If a document inside one of these areas has its own `Owner` or `Owners` field, that field must remain consistent with this map unless an approved update changes the ownership map itself.

## 3. Ownership Map

| Documentation area path | Area | Owner |
| ---- | ---- | ---- |
| `docs/requirements-baseline.md` | Requirements baseline | IT Operations, Information Systems Department |
| `docs/adr/` | Architecture Decision Records (ADRs) | IT Operations, Information Systems Department |
| `docs/parameters/` | Parameter documentation | IT Operations, Information Systems Department |
| `docs/runbook.md` | Runbooks | IT Operations, Information Systems Department |

The requirements baseline owner recorded in `docs/requirements-baseline.md` remains authoritative for that document and is unchanged by this map.

ADR records under `docs/adr/` may identify specific document proposers or reviewers, but repository-level ownership for the ADR area remains assigned to IT Operations, Information Systems Department unless this map is updated explicitly.

Parameter documents under `docs/parameters/` remain the authoritative human-readable home for parameter references, category explanations, ownership notes, and review guidance.

Runbooks remain owned as controlled operator documentation and must stay consistent with the approved operating model, approval constraints, and validation expectations defined elsewhere in the repository.
