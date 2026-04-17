# Codex Supervisor Repo Hygiene

This directory may contain tracked repository guidance such as this note.

Supervisor-local runtime state must remain untracked, including:

- `.codex-supervisor/issues/*/issue-journal.md`
- `.codex-supervisor/execution-metrics/`
- `.codex-supervisor/pre-merge/`
- `.codex-supervisor/replay/`
- `.codex-supervisor/turn-in-progress.json`

Use `git ls-files .codex-supervisor` to verify only intentionally versioned files remain tracked.
