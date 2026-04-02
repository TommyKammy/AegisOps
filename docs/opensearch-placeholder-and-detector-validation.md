# OpenSearch Placeholder and Detector Validation

- Validation date: 2026-04-02
- Baseline references: `docs/contributor-naming-guide.md`, `docs/requirements-baseline.md`, `docs/repository-structure-baseline.md`, `opensearch/index-templates/README.md`, `opensearch/detectors/README.md`
- Verification commands: `bash scripts/verify-opensearch-index-template-placeholders.sh`, `bash scripts/verify-opensearch-detector-metadata-template.sh`, `bash scripts/verify-opensearch-placeholder-and-detector-validation.sh`
- Validation status: PASS

## Reviewed Artifacts

- `opensearch/index-templates/README.md`
- `opensearch/index-templates/aegisops-logs-linux-template.json`
- `opensearch/index-templates/aegisops-logs-network-template.json`
- `opensearch/index-templates/aegisops-logs-saas-template.json`
- `opensearch/index-templates/aegisops-logs-windows-template.json`
- `opensearch/detectors/README.md`
- `opensearch/detectors/aegisops-detector-metadata-template.yaml`

## Index Template Naming Review Result

The placeholder assets under `opensearch/index-templates/` use the approved `aegisops-logs-<family>-*` naming baseline for the current Windows, Linux, network, and SaaS log families.

Each reviewed placeholder declares its approved index pattern, stays descriptive-only, and avoids production mappings or lifecycle behavior.

## Detector Metadata Review Result

The detector metadata template remains placeholder-only and includes the required detector name pattern, owner, purpose, severity, expected behavior, MITRE ATT&CK technique tags, source prerequisites, and false-positive considerations.

The tracked governance references keep the template aligned to the naming guide, requirements baseline, and repository structure baseline without introducing runnable detector configuration.

## Deviations

No deviations found.
