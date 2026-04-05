# Issue #202: implementation: make the read-only control-plane inspection CLI usable in the local runtime path

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/202
- Branch: codex/issue-202
- Workspace: .
- Journal: .codex-supervisor/issues/202/issue-journal.md
- Current phase: reproducing
- Attempt count: 1 (implementation=1, repair=0)
- Last head SHA: 463fbbedc6be337e4a97695ef40806e1952af35d
- Blocked reason: none
- Last failure signature: none
- Repeated failure signature count: 0
- Updated at: 2026-04-05T14:48:34.903Z

## Latest Codex Summary
- Reproduced that `python3 control-plane/main.py inspect-records --family alert` failed in the default local runtime because `main.py` rejected all inspection commands when `persistence_mode='in_memory'`, even though the service already supported read-only inspection snapshots and the README documented them as locally available.
- Replaced the rejection test with a focused regression proving the shipped entrypoint renders empty read-only inspection views against the default in-memory runtime, removed the CLI-only persistence guard, and documented the approved local runtime path as explicitly non-persistent and read-only.
- Focused verification passed for the updated CLI test module plus the shipped `runtime`, `inspect-records`, and `inspect-reconciliation-status` commands.

## Active Failure Context
- None recorded.

## Codex Working Notes
### Current Handoff
- Hypothesis: The local runtime path was already capable of rendering read-only inspection snapshots through the service layer, but `control-plane/main.py` incorrectly treated non-persistent local state as a hard blocker instead of allowing empty or locally-seeded read-only views.
- What changed: Removed the in-memory persistence rejection from the CLI entrypoint, tightened `control-plane/tests/test_cli_inspection.py` to require standalone read-only inspection rendering against the default local runtime, and updated `control-plane/README.md` to document the approved local path and its non-production scope.
- Current blocker: none
- Next exact step: Review git status, commit the focused issue-202 slice, and leave the branch ready for the next supervisor phase.
- Verification gap: Focused issue verification is complete; broader unittest coverage outside `control-plane/tests/test_cli_inspection.py` was not rerun this turn.
- Files touched: control-plane/main.py; control-plane/tests/test_cli_inspection.py; control-plane/README.md; .codex-supervisor/issues/202/issue-journal.md
- Rollback concern: Low; the change only removes a CLI-only guard that contradicted existing service behavior, while tests now pin the read-only in-memory inspection contract.
- Last focused command: python3 -m unittest control-plane/tests/test_cli_inspection.py
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
