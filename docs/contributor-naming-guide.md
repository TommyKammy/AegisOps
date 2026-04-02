# AegisOps Contributor Naming Guide

## Purpose

This guide gives contributors a short, implementation-friendly reference for the approved AegisOps naming conventions.

Use it when creating documentation, configuration, detectors, workflow assets, or example values in this repository.

## Baseline Source

`docs/requirements-baseline.md` remains the source of truth for naming policy.

This guide restates the approved baseline and does not authorize naming changes on its own.

## Naming Rules

Use the `aegisops` namespace consistently for platform identifiers.

Prefer names that are:

- stable across environments
- descriptive of the component or use case
- easy to parse in automation
- consistent with the baseline before adding new variants

### Hosts

Rules:

- Use lowercase letters, digits, and hyphens only.
- Start hostnames with the `aegisops-` namespace.
- Use a stable role suffix.
- Use a zero-padded ordinal for repeated roles.

Pattern:

`aegisops-<role>-node-<nn>`

Examples:

- `aegisops-opensearch-node-01`
- `aegisops-opensearch-node-02`
- `aegisops-ingest-node-01`
- `aegisops-n8n-node`
- `aegisops-proxy-node`

### Compose Projects

Rules:

- Use the `aegisops-` prefix.
- Use lowercase letters, digits, and hyphens only.
- Keep project names aligned to the platform component they represent.

Examples:

- `aegisops-opensearch`
- `aegisops-n8n`
- `aegisops-postgres`
- `aegisops-ingest`
- `aegisops-proxy`

### OpenSearch Indexes

Rules:

- Use lowercase letters, digits, and hyphens only.
- Start index names with the `aegisops-` namespace.
- Group the data type before the source where practical.

Examples:

- `aegisops-logs-windows-*`
- `aegisops-logs-linux-*`
- `aegisops-logs-network-*`
- `aegisops-alerts-*`
- `aegisops-findings-*`

### Detectors

Rules:

- Use descriptive, stable names.
- Keep the `aegisops-` namespace prefix.
- Use lowercase letters, digits, and hyphens only.

Pattern:

`aegisops-<source>-<use-case>-<severity>`

Examples:

- `aegisops-windows-suspicious-powershell-high`
- `aegisops-linux-privilege-escalation-medium`

### n8n Workflows

Rules:

- Use the `aegisops_` namespace.
- Use lowercase letters, digits, and underscores only.
- Start with a functional prefix so exported assets remain easy to sort and map.

Recommended prefixes:

- `aegisops_alert_ingest_`
- `aegisops_enrich_`
- `aegisops_approve_`
- `aegisops_notify_`
- `aegisops_response_`

Examples:

- `aegisops_alert_ingest_opensearch_findings`
- `aegisops_enrich_ip_reputation`
- `aegisops_approve_host_isolation`

### Environment Variables and Secrets

Rules:

- Use uppercase, underscore-delimited names.
- Scope names by component or function.
- Keep naming aligned between environment variables and secret identifiers where practical.

Examples:

- `AEGISOPS_OPENSEARCH_ADMIN_PASSWORD`
- `AEGISOPS_N8N_ENCRYPTION_KEY`
- `AEGISOPS_POSTGRES_PASSWORD`
- `AEGISOPS_PROXY_TLS_CERT_PATH`

## Contributor Checklist

Before committing a new identifier, confirm that it:

- uses the `aegisops` namespace expected for its asset type
- matches the separator style for that category
- stays consistent with the examples in `docs/requirements-baseline.md`
- does not introduce a competing alias for the same component
