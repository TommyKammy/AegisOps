# AegisOps Environment Parameter Catalog Structure

This document defines the approved structure and storage locations for the initial AegisOps environment parameter catalog.

It supplements `docs/requirements-baseline.md` by separating human-readable parameter documentation from machine-readable parameter artifacts.

This document defines structure only. It does not add deployment logic, real environment files, secrets, or production parameter values.

## 1. Purpose

The initial parameter catalog exists to make environment assumptions explicit, reviewable, and reproducible without committing active environment state.

It defines:

- where human-readable parameter references live,
- where machine-readable non-secret parameter files live,
- which parameter categories must be represented in the initial catalog, and
- what must stay out of version control.

## 2. Catalog Locations

Human-readable parameter catalog documents must live under `docs/parameters/`.

Machine-readable non-secret parameter files must live under `config/parameters/`.

Location rules:

- `docs/parameters/` is the authoritative location for narrative parameter references, category explanations, ownership notes, and review guidance.
- `config/parameters/` is reserved for structured non-secret parameter artifacts that tools may parse directly.
- Secrets, active `.env` files, and any environment-specific credential material must remain outside the repository even if a corresponding catalog entry exists.
- New parameter-related files should follow this split rather than mixing descriptive prose and machine-oriented structure in one artifact.

## 3. Required Parameter Categories

The initial parameter catalog must define the following categories:

- `network`
- `compute`
- `storage`
- `platform`
- `security`
- `operations`

Category intent:

- `network` covers hostnames, IP addressing, subnets, DNS dependencies, and approved service endpoints.
- `compute` covers node roles, sizing references, runtime capacity assumptions, and similar infrastructure-level identifiers.
- `storage` covers mount points, data paths, backup targets, and persistence-related parameter names.
- `platform` covers component identifiers, Docker Compose project names, execution modes, retention defaults, and other product-level runtime settings.
- `security` covers TLS material references, secret identifiers, approval-related parameter names, and access-control-related configuration keys.
- `operations` covers backup schedules, monitoring hooks, maintenance metadata, and other operator-facing control parameters.

## 4. Human-Readable and Machine-Readable Split

Human-readable documents describe intent, ownership, and review context.

Machine-readable files define non-secret keys, identifiers, defaults, and schema-oriented structure for tooling.

Split rules:

- Human-readable documents should explain why a parameter category exists, how operators should interpret it, and what review considerations apply before changes are merged.
- Machine-readable files should define stable names, expected field groupings, and placeholder-safe structure that automation can validate without embedding real site-specific values.
- A human-readable document may reference the expected machine-readable artifact path, but it must not duplicate active environment state.
- Machine-readable artifacts must remain non-secret and must not become a backdoor for storing live deployment values.

## 5. Value and Secret Handling Rules

This document must not introduce environment-specific secrets, production values, or deployment-time credentials.

The following repository safety rules apply to all parameter catalog artifacts:

- Example names may be illustrative, but they must remain non-secret and non-production.
- Placeholder values, when later introduced for schema examples, must be obviously fictitious and safe for publication.
- Secret values, tokens, passwords, certificates, and private keys must be managed through approved secret-handling mechanisms rather than committed files.
- Documenting a parameter category or key name does not authorize committing the corresponding live value.
