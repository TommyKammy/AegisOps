# AegisOps OpenSearch Detector Guidance

This document explains the intended role and current limits of the tracked detector content under `opensearch/detectors/`.

## 1. Purpose

This directory reserves the approved repository location for OpenSearch detector metadata and future detector-related content in AegisOps.

The current tracked content is documentation and metadata scaffolding only. It does not introduce an active production detector.

## 2. Current Directory Role

- Keep detector ownership and repository placement explicit under the approved `opensearch/` boundary.
- Provide a stable home for detector metadata that reviewers can evaluate before active detector content is proposed.
- Make it clear that production-ready detector definitions and activation steps require separate validation and review work.

## 3. Required Metadata Expectations

Detector proposals and related metadata should align with the AegisOps detection baseline. At minimum, tracked detector metadata should document:

- detector or rule title
- owner
- purpose
- expected behavior
- severity
- MITRE ATT&CK technique tags
- source or log prerequisites

Supporting notes should also capture any known false-positive considerations and the source fields or index prerequisites needed for reliable evaluation.

## 4. Production Activation Limits

Do not treat content in this directory as direct authorization to enable a detector in production.

Before any detector or related rule is enabled in production, the baseline requires all of the following:

- required source fields are available
- expected behavior is documented
- validation has been performed in staging or a test index
- false-positive considerations are noted
- ownership is assigned

Until those conditions are met through separately approved work, detector artifacts here remain metadata, review, or placeholder content only.

## 5. Future Content Expectations

Future issues may expand this directory with detector definitions, validation notes, or other supporting assets once those artifacts are approved by the baseline and backed by reviewable validation evidence.

Any future addition here must keep runtime behavior unchanged unless the change explicitly includes approved activation and validation scope.

The current Phase 6 slice adds staging-only detector artifacts for the selected Windows use cases under `opensearch/detectors/windows-security-and-endpoint/`.

Those tracked artifacts preserve Sigma traceability and test-index scope only. They are reviewable detector materialization inputs, not production activation instructions.

## 6. Reference Documents

- `docs/requirements-baseline.md`
- `docs/repository-structure-baseline.md`
- `opensearch/detectors/aegisops-detector-metadata-template.yaml`
- `docs/phase-6-opensearch-detector-artifact-validation.md`
