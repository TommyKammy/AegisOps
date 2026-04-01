# Repository Skeleton Validation

- Validation date: 2026-04-01
- Baseline reference: `docs/repository-structure-baseline.md`
- Verification command: `bash scripts/verify-repository-skeleton.sh`
- Validation status: FAIL

## Approved Baseline Entries

The approved top-level repository baseline allows these tracked entries:

- `.env.sample`
- `config/`
- `docs/`
- `ingest/`
- `n8n/`
- `opensearch/`
- `proxy/`
- `scripts/`
- `sigma/`

## Current Tracked Top-Level Entries

The repository currently tracks these top-level entries at `HEAD`:

- `.codex-supervisor/`
- `.env.sample`
- `LICENSE.txt`
- `config/`
- `docs/`
- `ingest/`
- `n8n/`
- `opensearch/`
- `proxy/`
- `scripts/`
- `sigma/`

## Result

The current repository skeleton does not match the approved baseline.

Documented deviations:

- Unexpected tracked top-level directory: `.codex-supervisor/`
- Unexpected tracked top-level file: `LICENSE.txt`

No required baseline top-level entries are missing.
