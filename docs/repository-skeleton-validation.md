# Repository Skeleton Validation

- Validation date: 2026-04-01
- Baseline reference: `docs/repository-structure-baseline.md`
- Verification command: `bash scripts/verify-repository-skeleton.sh`
- Validation status: PASS

## Approved Baseline Entries

The approved top-level repository baseline allows these tracked entries:

- `.codex-supervisor/`
- `.env.sample`
- `.github/`
- `.gitignore`
- `LICENSE.txt`
- `README.md`
- `config/`
- `control-plane/`
- `docs/`
- `ingest/`
- `n8n/`
- `opensearch/`
- `postgres/`
- `proxy/`
- `scripts/`
- `sigma/`

## Current Tracked Top-Level Entries

The repository currently tracks these top-level entries in the verified pull request merge checkout:

- `.codex-supervisor/`
- `.env.sample`
- `.github/`
- `.gitignore`
- `LICENSE.txt`
- `README.md`
- `config/`
- `control-plane/`
- `docs/`
- `ingest/`
- `n8n/`
- `opensearch/`
- `postgres/`
- `proxy/`
- `scripts/`
- `sigma/`

## Result

The current repository skeleton matches the approved baseline, including the dedicated `control-plane/` runtime home.

Disposition decisions:

- `.codex-supervisor/` is an approved tracked top-level directory for reviewable supervisor metadata such as issue journals; transient execution state under that path must remain untracked.
- `.gitignore` is an approved tracked top-level metadata file because the repository baseline depends on committed ignore rules for transient local and supervisor artifacts.
- `LICENSE.txt` and `README.md` are approved tracked top-level files and are part of the documented baseline.

No approved baseline top-level entries are missing.
