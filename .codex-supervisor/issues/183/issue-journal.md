# Issue #183: implementation: materialize control-plane schema v1 from the reviewed placeholders

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/183
- Branch: codex/issue-183
- Workspace: .
- Journal: .codex-supervisor/issues/183/issue-journal.md
- Current phase: addressing_review
- Attempt count: 5 (implementation=2, repair=2)
- Last head SHA: 5efa8bd1b4ec4dd8b4a7a7c261f0d2bf2cc827dd
- Blocked reason: none
- Last failure signature: PRRT_kwDOR2iDUc543jHq|PRRT_kwDOR2iDUc543jHu|PRRT_kwDOR2iDUc543jHw|PRRT_kwDOR2iDUc543jHx|PRRT_kwDOR2iDUc543jHz|PRRT_kwDOR2iDUc543jH1
- Repeated failure signature count: 1
- Updated at: 2026-04-04T21:46:46.943Z

## Latest Codex Summary
I did not change repository code. I moved PR [#195](https://github.com/TommyKammy/AegisOps/pull/195) out of draft with `gh pr ready 195`, then verified the live PR state directly. The PR is now open for review, `draft: false`, and the existing `CI / verify` check is still successful.

The only live follow-up is external: CodeRabbit restarted after the draft transition and is pending a fresh pass. I updated the issue journal handoff to reflect that state and the unchanged local verification gap that `psql` is not installed.

Summary: Marked PR #195 ready for review, verified it is no longer draft, and updated the issue journal handoff.
State hint: pr_open
Blocked reason: none
Tests: `gh pr view 195 --json number,title,state,isDraft,url,reviewDecision,statusCheckRollup,comments,reviews`; `gh pr ready 195`; `gh pr view 195 --json number,isDraft,url,reviewDecision,statusCheckRollup`; `gh api repos/TommyKammy/AegisOps/pulls/195 --jq '{number: .number, draft: .draft, state: .state, url: .html_url}'`; `psql` unavailable
Next action: watch PR #195 for the fresh CodeRabbit result and any human review feedback
Failure signature: PRRT_kwDOR2iDUc543jHq|PRRT_kwDOR2iDUc543jHu|PRRT_kwDOR2iDUc543jHw|PRRT_kwDOR2iDUc543jHx|PRRT_kwDOR2iDUc543jHz|PRRT_kwDOR2iDUc543jH1

## Active Failure Context
- Category: review
- Summary: 6 unresolved automated review thread(s) remain.
- Reference: https://github.com/TommyKammy/AegisOps/pull/195#discussion_r3036085479
- Details:
  - postgres/control-plane/migrations/0001_control_plane_schema_skeleton.sql:27 summary=_⚠️ Potential issue_ | _🟠 Major_ **Cardinality constraint conflicts with default empty array.** `evidence_ids` has `default '{}'::text[]` but `check (cardinality(evidence_ids) ... url=https://github.com/TommyKammy/AegisOps/pull/195#discussion_r3036085479
  - postgres/control-plane/migrations/0001_control_plane_schema_skeleton.sql:61 summary=_⚠️ Potential issue_ | _🟠 Major_ **Same cardinality vs. url=https://github.com/TommyKammy/AegisOps/pull/195#discussion_r3036085484
  - postgres/control-plane/migrations/0001_control_plane_schema_skeleton.sql:107 summary=_⚠️ Potential issue_ | _🟠 Major_ **Same cardinality vs. url=https://github.com/TommyKammy/AegisOps/pull/195#discussion_r3036085486
  - postgres/control-plane/schema.sql:27 summary=_⚠️ Potential issue_ | _🟠 Major_ **Array cardinality constraint conflicts with empty default for `evidence_ids`.** Line 22 sets `evidence_ids text[] not null default '{}'::text... url=https://github.com/TommyKammy/AegisOps/pull/195#discussion_r3036085487
  - postgres/control-plane/schema.sql:61 summary=_⚠️ Potential issue_ | _🟠 Major_ **Same cardinality/default conflict for `supporting_evidence_ids`.** Line 53 defaults to empty array while Line 61 requires `cardinality(suppor... url=https://github.com/TommyKammy/AegisOps/pull/195#discussion_r3036085490

## Codex Working Notes
### Current Handoff
- Hypothesis: Issue #183 is satisfied by replacing the placeholder-only control-plane SQL contract with a repository-validated v1 baseline that preserves the n8n ownership split and explicit reconciliation state.
- What changed: Validated the six CodeRabbit review findings as real and removed the contradictory empty-array defaults from `case_records.evidence_ids`, `observation_records.supporting_evidence_ids`, and `approval_decision_records.approver_identities` in both `postgres/control-plane/schema.sql` and `postgres/control-plane/migrations/0001_control_plane_schema_skeleton.sql`; aligned `scripts/test-verify-control-plane-schema-skeleton.sh` so the verifier fixture matches the runtime contract.
- Current blocker: None.
- Next exact step: Watch PR #195 for the refreshed `verify` run and CodeRabbit status after commit `8c492ed`, then handle any follow-up review only if new feedback appears.
- Verification gap: `psql` is not installed in this workspace, so SQL was validated through repository verifiers and shell tests rather than an actual PostgreSQL parser/runtime.
- Files touched: postgres/control-plane/schema.sql; postgres/control-plane/migrations/0001_control_plane_schema_skeleton.sql; scripts/test-verify-control-plane-schema-skeleton.sh
- Rollback concern: The main risk is contract drift for downstream work that still assumes placeholder-only SQL assets; the aligned verification/docs updates were included specifically to avoid that split-brain state.
- Last focused command: gh pr view 195 --json number,isDraft,reviewDecision,statusCheckRollup,url
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
- Commands run this turn: `git status --short`; `sed -n '1,220p' postgres/control-plane/schema.sql`; `sed -n '1,220p' postgres/control-plane/migrations/0001_control_plane_schema_skeleton.sql`; `rg -n "default '\\{\\}'::text\\[]|cardinality\\(" postgres/control-plane/schema.sql postgres/control-plane/migrations/0001_control_plane_schema_skeleton.sql`; `sed -n '1,220p' scripts/verify-control-plane-schema-skeleton.sh`; `sed -n '1,260p' scripts/test-verify-control-plane-schema-skeleton.sh`; `rg -n "create schema|create table|reconciliation" postgres/control-plane`; `bash scripts/verify-control-plane-schema-skeleton.sh`; `bash scripts/test-verify-control-plane-schema-skeleton.sh`; `git diff --check`
- Review-fix scope: keep the non-empty array checks and remove only the conflicting empty defaults so inserts must supply values for those three record families.
- Publish status: committed `8c492ed` (`Fix control-plane non-empty array defaults`) and pushed `codex/issue-183`; immediate PR status after push shows `verify` in progress and `CodeRabbit` pending.
