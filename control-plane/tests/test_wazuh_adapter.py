from __future__ import annotations

from datetime import datetime, timezone
import json
import pathlib
import sys
import unittest


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from aegisops_control_plane.adapters.wazuh import WazuhAlertAdapter


FIXTURES_ROOT = pathlib.Path(__file__).resolve().parent / "fixtures" / "wazuh"


def _load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES_ROOT / name).read_text(encoding="utf-8"))


class WazuhAlertAdapterTests(unittest.TestCase):
    def test_adapter_builds_native_detection_record_from_agent_origin_fixture(self) -> None:
        adapter = WazuhAlertAdapter()

        record = adapter.build_native_detection_record(
            _load_fixture("agent-origin-alert.json")
        )

        self.assertEqual(record.substrate_key, "wazuh")
        self.assertEqual(record.native_record_id, "1731594986.4931506")
        self.assertEqual(record.record_kind, "alert")
        self.assertEqual(
            record.correlation_key,
            (
                "wazuh:rule:5710:source:agent:007"
                ":location=%2Fvar%2Flog%2Fauth.log"
                ":data.srcip=198.51.100.24"
                ":data.srcuser=invalid-user"
            ),
        )
        self.assertEqual(
            record.first_seen_at,
            datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(record.last_seen_at, record.first_seen_at)
        self.assertEqual(record.metadata["source_system"], "wazuh")
        self.assertEqual(record.metadata["native_rule"]["level"], 10)
        self.assertEqual(record.metadata["native_rule"]["description"], "SSH brute force attempt")
        self.assertEqual(
            record.metadata["source_provenance"]["accountable_source_identity"],
            "agent:007",
        )
        self.assertEqual(
            record.metadata["source_provenance"]["decoder_name"],
            "sshd",
        )
        self.assertEqual(
            record.metadata["source_provenance"]["location"],
            "/var/log/auth.log",
        )
        self.assertEqual(
            record.metadata["reviewed_correlation_context"],
            {
                "location": "/var/log/auth.log",
                "data.srcip": "198.51.100.24",
                "data.srcuser": "invalid-user",
            },
        )
        self.assertEqual(
            adapter.build_analytic_signal_admission(record).reviewed_context,
            {
                "location": "/var/log/auth.log",
                "data.srcip": "198.51.100.24",
                "data.srcuser": "invalid-user",
            },
        )

    def test_adapter_accepts_manager_origin_fixture_when_agent_identity_is_absent(self) -> None:
        adapter = WazuhAlertAdapter()

        record = adapter.build_native_detection_record(
            _load_fixture("manager-origin-alert.json")
        )
        admission = adapter.build_analytic_signal_admission(record)

        self.assertEqual(
            record.correlation_key,
            (
                "wazuh:rule:100001:source:manager:wazuh-manager-2"
                ":location=manager%2Fintegrations"
                ":data.integration=virustotal"
                ":data.event_type=warning"
            ),
        )
        self.assertEqual(
            record.metadata["source_provenance"]["accountable_source_identity"],
            "manager:wazuh-manager-2",
        )
        self.assertEqual(
            admission.finding_id,
            "finding:wazuh:rule:100001:source:manager:wazuh-manager-2:alert:1731594999.4931507",
        )
        self.assertIsNone(admission.analytic_signal_id)

    def test_adapter_distinguishes_same_rule_and_source_when_reviewed_context_changes(
        self,
    ) -> None:
        adapter = WazuhAlertAdapter()
        first_alert = _load_fixture("agent-origin-alert.json")
        second_alert = _load_fixture("agent-origin-alert.json")
        second_alert["location"] = "/var/log/secure"
        second_alert["data"] = {
            "srcip": "203.0.113.77",
            "srcuser": "invalid-user",
        }

        first_record = adapter.build_native_detection_record(first_alert)
        second_record = adapter.build_native_detection_record(second_alert)

        self.assertNotEqual(first_record.correlation_key, second_record.correlation_key)

    def test_adapter_builds_reviewed_source_profile_for_github_audit_fixture(self) -> None:
        adapter = WazuhAlertAdapter()

        record = adapter.build_native_detection_record(
            _load_fixture("github-audit-alert.json")
        )

        expected_profile = {
            "source": {
                "source_system": "wazuh",
                "source_family": "github_audit",
                "accountable_source_identity": "manager:wazuh-manager-github-1",
                "delivery_path": "github/orgs/TommyKammy/repos/AegisOps/audit",
            },
            "identity": {
                "actor": {
                    "identity_type": "user",
                    "identity_id": "octocat",
                    "display_name": "octocat",
                },
                "target": {
                    "identity_type": "team",
                    "identity_id": "security-reviews",
                    "display_name": "security-reviews",
                },
            },
            "asset": {
                "organization": {
                    "organization_id": "org-001",
                    "organization_name": "TommyKammy",
                },
                "repository": {
                    "repository_id": "repo-001",
                    "repository_name": "AegisOps",
                    "repository_full_name": "TommyKammy/AegisOps",
                },
            },
            "privilege": {
                "change_type": "membership_change",
                "scope": "repository_admin",
                "permission": "admin",
                "role": "maintainer",
            },
            "provenance": {
                "audit_action": "member.added",
                "request_id": "GH-REQ-0001",
                "rule_id": "github-audit-privilege-change",
                "rule_level": 8,
                "rule_description": "GitHub audit repository privilege change",
                "decoder_name": "github_audit",
                "location": "github/orgs/TommyKammy/repos/AegisOps/audit",
            },
        }

        self.assertEqual(record.correlation_key, (
            "wazuh:rule:github-audit-privilege-change:source:manager:wazuh-manager-github-1"
            ":location=github%2Forgs%2FTommyKammy%2Frepos%2FAegisOps%2Faudit"
            ":data.audit_action=member.added"
            ":data.actor.id=octocat"
            ":data.actor.name=octocat"
            ":data.target.id=security-reviews"
            ":data.target.name=security-reviews"
            ":data.organization.name=TommyKammy"
            ":data.repository.full_name=TommyKammy%2FAegisOps"
            ":data.privilege.change_type=membership_change"
            ":data.privilege.scope=repository_admin"
        ))
        self.assertEqual(
            record.metadata["source_provenance"]["accountable_source_identity"],
            "manager:wazuh-manager-github-1",
        )
        self.assertEqual(record.metadata["reviewed_source_profile"], expected_profile)
        self.assertEqual(
            adapter.build_analytic_signal_admission(record).reviewed_context,
            expected_profile,
        )

    def test_adapter_builds_reviewed_source_profile_when_only_source_family_is_present(
        self,
    ) -> None:
        adapter = WazuhAlertAdapter()
        sparse_alert = _load_fixture("github-audit-alert.json")
        sparse_alert["data"] = {"source_family": "github_audit"}

        record = adapter.build_native_detection_record(sparse_alert)

        expected_profile = {
            "source": {
                "source_system": "wazuh",
                "source_family": "github_audit",
                "accountable_source_identity": "manager:wazuh-manager-github-1",
                "delivery_path": "github/orgs/TommyKammy/repos/AegisOps/audit",
            },
            "provenance": {
                "audit_action": None,
                "request_id": None,
                "rule_id": "github-audit-privilege-change",
                "rule_level": 8,
                "rule_description": "GitHub audit repository privilege change",
                "decoder_name": "github_audit",
                "location": "github/orgs/TommyKammy/repos/AegisOps/audit",
            },
        }

        self.assertEqual(record.metadata["reviewed_source_profile"], expected_profile)
        self.assertEqual(
            adapter.build_analytic_signal_admission(record).reviewed_context,
            expected_profile,
        )

    def test_adapter_does_not_apply_github_profile_defaults_to_non_github_family(
        self,
    ) -> None:
        adapter = WazuhAlertAdapter()
        foreign_alert = _load_fixture("github-audit-alert.json")
        foreign_alert["data"]["source_family"] = "okta_audit"

        record = adapter.build_native_detection_record(foreign_alert)

        self.assertNotIn("reviewed_source_profile", record.metadata)
        self.assertEqual(
            adapter.build_analytic_signal_admission(record).reviewed_context,
            record.metadata["reviewed_correlation_context"],
        )

    def test_adapter_does_not_promote_github_shaped_payload_without_family_marker(
        self,
    ) -> None:
        adapter = WazuhAlertAdapter()
        ambiguous_alert = _load_fixture("github-audit-alert.json")
        ambiguous_alert["data"].pop("source_family")

        record = adapter.build_native_detection_record(ambiguous_alert)

        self.assertNotIn("reviewed_source_profile", record.metadata)
        self.assertEqual(
            adapter.build_analytic_signal_admission(record).reviewed_context,
            record.metadata["reviewed_correlation_context"],
        )

    def test_adapter_uses_login_fields_when_reviewed_identity_names_are_absent(
        self,
    ) -> None:
        adapter = WazuhAlertAdapter()
        login_only_alert = _load_fixture("github-audit-alert.json")
        login_only_alert["data"] = {
            "source_family": "github_audit",
            "audit_action": "member.added",
            "actor": {
                "type": "user",
                "id": "octocat",
                "login": "octocat",
            },
            "target": {
                "type": "team",
                "id": "security-reviews",
                "login": "security-reviews",
            },
        }

        record = adapter.build_native_detection_record(login_only_alert)

        self.assertEqual(
            record.correlation_key,
            (
                "wazuh:rule:github-audit-privilege-change:source:manager:wazuh-manager-github-1"
                ":location=github%2Forgs%2FTommyKammy%2Frepos%2FAegisOps%2Faudit"
                ":data.audit_action=member.added"
                ":data.actor.id=octocat"
                ":data.actor.login=octocat"
                ":data.target.id=security-reviews"
                ":data.target.login=security-reviews"
            ),
        )
        self.assertEqual(
            record.metadata["reviewed_correlation_context"],
            {
                "location": "github/orgs/TommyKammy/repos/AegisOps/audit",
                "data.audit_action": "member.added",
                "data.actor.id": "octocat",
                "data.actor.login": "octocat",
                "data.target.id": "security-reviews",
                "data.target.login": "security-reviews",
            },
        )


if __name__ == "__main__":
    unittest.main()
