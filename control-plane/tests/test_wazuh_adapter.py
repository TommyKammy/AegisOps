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


if __name__ == "__main__":
    unittest.main()
