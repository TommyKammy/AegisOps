# Issue #302: implementation: onboard GitHub audit signals through Wazuh-backed source profiles

## Supervisor Snapshot
- Issue URL: https://github.com/TommyKammy/AegisOps/issues/302
- Branch: codex/issue-302
- Workspace: .
- Journal: .codex-supervisor/issues/302/issue-journal.md
- Current phase: addressing_review
- Attempt count: 6 (implementation=1, repair=5)
- Last head SHA: 1dc0beeaa53b0204244403dea63c0f44961b6c4e
- Blocked reason: none
- Last failure signature: PRRT_kwDOR2iDUc55nYGB|PRRT_kwDOR2iDUc55nYGK
- Repeated failure signature count: 1
- Updated at: 2026-04-08T16:08:44.902Z

## Latest Codex Summary
Summary: Added the missing GitHub-audit correlation fields, stopped serializing absent provenance keys as None, updated the Wazuh contract docs/tests, and reran focused verification.
State hint: local_review_fix
Blocked reason: none
Tests: `python3 -m unittest control-plane.tests.test_wazuh_adapter control-plane.tests.test_service_persistence control-plane.tests.test_wazuh_alert_ingest_contract_docs`; `bash scripts/test-verify-source-onboarding-contract-doc.sh`
Next action: await the next local review pass on the updated Wazuh adapter head
Failure signature: none

## Active Failure Context
- Category: review
- Summary: 2 unresolved automated review thread(s) remain.
- Reference: https://github.com/TommyKammy/AegisOps/pull/309#discussion_r3052633832
- Details:
  - control-plane/aegisops_control_plane/adapters/wazuh.py:56 summary=_⚠️ Potential issue_ | _🟠 Major_ **Include `data.source_family`, `data.privilege.permission`, and `data.privilege.role` in the correlation key.** Line 257 makes `source_family`... url=https://github.com/TommyKammy/AegisOps/pull/309#discussion_r3052633832
  - control-plane/aegisops_control_plane/adapters/wazuh.py:289 summary=_⚠️ Potential issue_ | _🟠 Major_ **Don’t serialize absent provenance fields as `None`.** Lines 245-263 in `control-plane/aegisops_control_plane/service.py` merge nested `review... url=https://github.com/TommyKammy/AegisOps/pull/309#discussion_r3052633844

## Codex Working Notes
### Current Handoff
- Hypothesis: the reviewed GitHub audit path must carry `data.source_family`, `data.privilege.permission`, and `data.privilege.role` into the correlation key so sparse or privilege-differing GitHub audit alerts do not collapse into the same analytic signal.
- What changed: `WazuhAlertAdapter` now includes those reviewed fields in `reviewed_correlation_fields`, omits absent provenance keys from the reviewed source profile, and the adapter/service/doc tests cover the GitHub audit fixture and sparse-profile case.
- Current blocker: None.
- Next exact step: wait for the next local review pass on the updated Wazuh adapter head.
- Verification gap: None for the focused slice; the Wazuh adapter/service/doc tests and the source-onboarding-contract verifier both passed again in this turn.
- Files touched: `control-plane/aegisops_control_plane/adapters/wazuh.py`, `control-plane/tests/test_service_persistence.py`, `control-plane/tests/test_wazuh_adapter.py`, `control-plane/tests/test_wazuh_alert_ingest_contract_docs.py`, `docs/wazuh-alert-ingest-contract.md`, `.codex-supervisor/issues/302/issue-journal.md`
- Rollback concern: Sparse GitHub audit admissions still preserve the reviewed family marker, and the added tests cover the low-signal and privilege-variation cases.
- Last focused command: `python3 -m unittest control-plane.tests.test_wazuh_adapter control-plane.tests.test_service_persistence control-plane.tests.test_wazuh_alert_ingest_contract_docs`
- Last focused commands: `python3 -m unittest control-plane.tests.test_wazuh_adapter control-plane.tests.test_service_persistence control-plane.tests.test_wazuh_alert_ingest_contract_docs`; `bash scripts/test-verify-source-onboarding-contract-doc.sh`
### Scratchpad
- Keep this section short. The supervisor may compact older notes automatically.
