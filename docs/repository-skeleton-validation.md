# Repository Skeleton Validation

- Validation date: 2026-04-20
- Validation timezone: Asia/Tokyo (UTC+09:00)
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
- `apps/`
- `config/`
- `control-plane/`
- `docs/`
- `ingest/`
- `n8n/`
- `opensearch/`
- `package-lock.json`
- `package.json`
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
- `apps/`
- `config/`
- `control-plane/`
- `docs/`
- `ingest/`
- `n8n/`
- `opensearch/`
- `package-lock.json`
- `package.json`
- `postgres/`
- `proxy/`
- `scripts/`
- `sigma/`

## Result

The current repository skeleton matches the approved baseline, including the dedicated `control-plane/` runtime home.

Disposition decisions:

- `.codex-supervisor/` is an approved tracked top-level directory for intentionally versioned repository hygiene guidance; supervisor-local journals and transient execution state under that path must remain untracked.
- `.gitignore` is an approved tracked top-level metadata file because the repository baseline depends on committed ignore rules for transient local and supervisor artifacts.
- `LICENSE.txt` and `README.md` are approved tracked top-level files and are part of the documented baseline.
- `apps/`, `package.json`, and `package-lock.json` are approved Phase 30 operator-console baseline entries that support the dedicated frontend workspace while preserving backend authority.

No approved baseline top-level entries are missing.
