from __future__ import annotations

from datetime import datetime, timezone
import pathlib
import sys
import unittest


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))
TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

from aegisops.control_plane.adapters.wazuh import WazuhAlertAdapter
from support.fixtures import load_wazuh_fixture


_load_fixture = load_wazuh_fixture


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
            ":data.source_family=github_audit"
            ":data.audit_action=member.added"
            ":data.actor.id=octocat"
            ":data.actor.name=octocat"
            ":data.target.id=security-reviews"
            ":data.target.name=security-reviews"
            ":data.organization.id=org-001"
            ":data.organization.name=TommyKammy"
            ":data.repository.id=repo-001"
            ":data.repository.full_name=TommyKammy%2FAegisOps"
            ":data.privilege.change_type=membership_change"
            ":data.privilege.scope=repository_admin"
            ":data.privilege.permission=admin"
            ":data.privilege.role=maintainer"
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

    def test_adapter_distinguishes_github_repository_identity_when_alias_fields_match(
        self,
    ) -> None:
        adapter = WazuhAlertAdapter()
        first_alert = _load_fixture("github-audit-alert.json")
        second_alert = _load_fixture("github-audit-alert.json")
        second_alert["data"]["organization"]["id"] = "org-999"
        second_alert["data"]["repository"]["id"] = "repo-999"

        first_record = adapter.build_native_detection_record(first_alert)
        second_record = adapter.build_native_detection_record(second_alert)

        self.assertNotEqual(first_record.correlation_key, second_record.correlation_key)

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

    def test_adapter_builds_reviewed_source_profile_for_microsoft_365_audit_fixture(
        self,
    ) -> None:
        adapter = WazuhAlertAdapter()

        record = adapter.build_native_detection_record(
            _load_fixture("microsoft-365-audit-alert.json")
        )

        expected_profile = {
            "source": {
                "source_system": "wazuh",
                "source_family": "microsoft_365_audit",
                "accountable_source_identity": "manager:wazuh-manager-m365-1",
                "delivery_path": "microsoft365/contoso/exchange",
            },
            "identity": {
                "actor": {
                    "identity_type": "user",
                    "identity_id": "alex@contoso.com",
                    "display_name": "Alex Rivera",
                },
                "target": {
                    "identity_type": "mailbox",
                    "identity_id": "shared-mailbox-finance",
                    "display_name": "shared-mailbox-finance",
                },
            },
            "asset": {
                "tenant": {
                    "tenant_id": "tenant-001",
                    "tenant_name": "Contoso",
                },
                "app": {
                    "app_id": "app-365-exchange",
                    "app_name": "Exchange Online",
                    "app_type": "workload",
                },
            },
            "authentication": {
                "method": "oauth2",
                "client_app": "Outlook",
                "result": "success",
            },
            "privilege": {
                "change_type": "permission_grant",
                "scope": "mailbox",
                "permission": "full_access",
            },
            "provenance": {
                "audit_action": "Add-MailboxPermission",
                "request_id": "M365-REQ-0001",
                "workload": "exchange",
                "operation": "Add-MailboxPermission",
                "record_type": "Microsoft 365 audit",
                "rule_id": "microsoft-365-audit-privilege-change",
                "rule_level": 7,
                "rule_description": "Microsoft 365 audit mailbox permission change",
                "decoder_name": "microsoft_365_audit",
                "location": "microsoft365/contoso/exchange",
            },
        }

        self.assertEqual(
            record.metadata["reviewed_source_profile"],
            expected_profile,
        )
        self.assertEqual(
            adapter.build_analytic_signal_admission(record).reviewed_context,
            expected_profile,
        )

    def test_adapter_builds_reviewed_source_profile_for_entra_id_fixture(self) -> None:
        adapter = WazuhAlertAdapter()

        record = adapter.build_native_detection_record(
            _load_fixture("entra-id-alert.json")
        )

        expected_profile = {
            "source": {
                "source_system": "wazuh",
                "source_family": "entra_id",
                "accountable_source_identity": "manager:wazuh-manager-entra-1",
                "delivery_path": "entra/contoso/directory",
            },
            "identity": {
                "actor": {
                    "identity_type": "service_principal",
                    "identity_id": "spn-operations",
                    "display_name": "Operations Automation",
                },
                "target": {
                    "identity_type": "role",
                    "identity_id": "role-global-admin",
                    "display_name": "Global Administrator",
                },
            },
            "asset": {
                "tenant": {
                    "tenant_id": "tenant-001",
                    "tenant_name": "Contoso",
                },
                "app": {
                    "app_id": "app-entra-admin",
                    "app_name": "Azure Portal",
                    "app_type": "service",
                },
            },
            "authentication": {
                "method": "mfa",
                "client_app": "Azure Portal",
                "result": "success",
            },
            "privilege": {
                "change_type": "role_assignment",
                "scope": "directory_role",
                "permission": "Global Administrator",
                "role": "Privileged Role Administrator",
            },
            "provenance": {
                "audit_action": "Add member to role",
                "request_id": "ENTRA-REQ-0001",
                "correlation_id": "entra-corr-0001",
                "operation": "Add member to role",
                "record_type": "Entra ID audit",
                "rule_id": "entra-id-role-assignment",
                "rule_level": 8,
                "rule_description": "Entra ID privileged role assignment",
                "decoder_name": "entra_id",
                "location": "entra/contoso/directory",
            },
        }

        self.assertEqual(
            record.metadata["reviewed_source_profile"],
            expected_profile,
        )
        self.assertEqual(
            adapter.build_analytic_signal_admission(record).reviewed_context,
            expected_profile,
        )

    def test_adapter_maps_phase53_sample_detection_fixture_to_expected_signal_shape(
        self,
    ) -> None:
        adapter = WazuhAlertAdapter()

        record = adapter.build_native_detection_record(
            _load_fixture("phase53-smb-single-node-ssh-auth-failure-alert.json")
        )
        expected_mapping = _load_fixture(
            "phase53-smb-single-node-ssh-auth-failure-analytic-signal.json"
        )

        self.assertEqual(record.native_record_id, "1731595600.1112223")
        self.assertEqual(record.metadata["reviewed_source_profile"], expected_mapping)
        self.assertEqual(
            adapter.build_analytic_signal_admission(record).reviewed_context,
            expected_mapping,
        )

    def test_adapter_rejects_phase53_detection_fixture_missing_required_provenance(
        self,
    ) -> None:
        adapter = WazuhAlertAdapter()
        alert = _load_fixture("phase53-smb-single-node-ssh-auth-failure-alert.json")
        alert["data"].pop("secret_custody_reference")

        with self.assertRaisesRegex(
            ValueError,
            "data.secret_custody_reference must be a non-empty string",
        ):
            adapter.build_native_detection_record(alert)

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
                ":data.source_family=github_audit"
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
                "data.source_family": "github_audit",
                "data.audit_action": "member.added",
                "data.actor.id": "octocat",
                "data.actor.login": "octocat",
                "data.target.id": "security-reviews",
                "data.target.login": "security-reviews",
            },
        )

    def test_adapter_distinguishes_github_audit_privilege_metadata_in_correlation_key(
        self,
    ) -> None:
        adapter = WazuhAlertAdapter()
        first_alert = _load_fixture("github-audit-alert.json")
        second_alert = _load_fixture("github-audit-alert.json")
        second_alert["data"]["privilege"]["permission"] = "read"
        second_alert["data"]["privilege"]["role"] = "observer"

        first_record = adapter.build_native_detection_record(first_alert)
        second_record = adapter.build_native_detection_record(second_alert)

        self.assertNotEqual(first_record.correlation_key, second_record.correlation_key)


if __name__ == "__main__":
    unittest.main()
