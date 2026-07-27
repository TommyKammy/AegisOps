from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


CONTROL_PLANE_ROOT = Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))
TESTS_ROOT = Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

from aegisops.control_plane.config import RuntimeConfig
from aegisops.control_plane.models import AlertRecord, CaseRecord
from aegisops.control_plane.service import AegisOpsControlPlaneService
from postgres_test_support import make_store
from support.fixtures import load_wazuh_fixture


REPO_ROOT = CONTROL_PLANE_ROOT.parent
LAB_DIR = CONTROL_PLANE_ROOT / "deployment" / "phase-67-integration-lab"
INTEGRATOR_PATH = LAB_DIR / "wazuh" / "aegisops_wazuh_integrator.py"

spec = importlib.util.spec_from_file_location(
    "phase67_aegisops_wazuh_integrator",
    INTEGRATOR_PATH,
)
if spec is None or spec.loader is None:
    raise RuntimeError("could not load Phase 67.2 Wazuh Integrator module")
integrator = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = integrator
spec.loader.exec_module(integrator)


class _FakeResponse:
    def __init__(self, status: int, payload: dict[str, object]) -> None:
        self.status = status
        self._payload = json.dumps(payload).encode("utf-8")

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self, limit: int) -> bytes:
        return self._payload[:limit]


class Phase672RealWazuhIntakeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.native_alert = load_wazuh_fixture(
            "phase67-real-wazuh-ssh-auth-failure-alert.json"
        )

    def test_mapper_preserves_native_identity_and_adds_reviewed_provenance(self) -> None:
        native_alert = deepcopy(self.native_alert)
        native_alert["data"] = {
            "srcip": "192.0.2.67",
            "srcuser": "aegisops-phase67-invalid",
        }

        mapped = integrator.map_native_alert(
            native_alert,
            allowed_rule_id="5710",
        )

        self.assertEqual(mapped["id"], native_alert["id"])
        self.assertEqual(mapped["timestamp"], native_alert["timestamp"])
        self.assertEqual(mapped["manager"], native_alert["manager"])
        self.assertEqual(mapped["rule"], native_alert["rule"])
        self.assertEqual(mapped["data"]["event_id"], native_alert["id"])
        self.assertEqual(
            mapped["data"]["event_timestamp"],
            native_alert["timestamp"],
        )
        self.assertEqual(mapped["data"]["source_family"], "wazuh_detection")
        self.assertEqual(mapped["data"]["source_system"], "wazuh")
        self.assertEqual(
            mapped["data"]["source_id"],
            native_alert["manager"]["name"],
        )
        self.assertEqual(mapped["data"]["srcip"], "192.0.2.67")
        self.assertEqual(
            mapped["data"]["secret_custody_reference"],
            "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_FILE",
        )
        self.assertNotIn("shared_secret", mapped["data"])

    def test_mapper_rejects_rules_outside_the_bounded_filter(self) -> None:
        native_alert = deepcopy(self.native_alert)
        native_alert["rule"]["id"] = "5712"

        with self.assertRaisesRegex(
            integrator.IntegrationError,
            "outside the reviewed '5710' filter",
        ):
            integrator.map_native_alert(
                native_alert,
                allowed_rule_id="5710",
            )

    def test_mapper_requires_real_manager_identity_and_timezone(self) -> None:
        without_manager = deepcopy(self.native_alert)
        without_manager.pop("manager")
        with self.assertRaisesRegex(
            integrator.IntegrationError,
            "manager must be a JSON object",
        ):
            integrator.map_native_alert(
                without_manager,
                allowed_rule_id="5710",
            )

        naive_timestamp = deepcopy(self.native_alert)
        naive_timestamp["timestamp"] = "2026-07-28T10:00:00"
        with self.assertRaisesRegex(
            integrator.IntegrationError,
            "timestamp must include a timezone",
        ):
            integrator.map_native_alert(
                naive_timestamp,
                allowed_rule_id="5710",
            )

    def test_mapper_accepts_native_wazuh_basic_timezone_offset(self) -> None:
        native_alert = deepcopy(self.native_alert)
        native_alert["timestamp"] = "2026-07-27T23:22:35.873+0000"

        mapped = integrator.map_native_alert(
            native_alert,
            allowed_rule_id="5710",
        )

        self.assertEqual(mapped["timestamp"], native_alert["timestamp"])
        self.assertEqual(
            mapped["data"]["event_timestamp"],
            native_alert["timestamp"],
        )

    def test_native_alert_loader_rejects_oversized_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            alert_path = Path(directory) / "alert.json"
            alert_path.write_bytes(b"x" * (integrator.MAX_ALERT_BYTES + 1))

            with self.assertRaisesRegex(
                integrator.IntegrationError,
                "exceeds the 262144-byte intake limit",
            ):
                integrator.load_native_alert(alert_path)

    def test_hook_url_requires_exact_https_intake_path(self) -> None:
        invalid_urls = (
            "http://proxy:8443/intake/wazuh",
            "https://proxy:8443/intake/wazuh?secret=value",
            "https://proxy:8443/runtime",
            "https://user:password@proxy:8443/intake/wazuh",
        )
        for invalid_url in invalid_urls:
            with self.subTest(invalid_url=invalid_url):
                with self.assertRaises(integrator.IntegrationError):
                    integrator.validate_https_url(invalid_url)

        self.assertEqual(
            integrator.validate_https_url(
                "https://proxy:8443/intake/wazuh"
            ),
            "https://proxy:8443/intake/wazuh",
        )

    def test_post_uses_bearer_secret_and_records_only_sanitized_response(self) -> None:
        captured_request: dict[str, object] = {}

        def fake_urlopen(
            http_request: object,
            *,
            context: object,
            timeout: int,
        ) -> _FakeResponse:
            captured_request["request"] = http_request
            captured_request["context"] = context
            captured_request["timeout"] = timeout
            return _FakeResponse(
                202,
                {
                    "disposition": "created",
                    "finding_id": "finding:wazuh:5710:one",
                    "alert": {"alert_id": "alert-001"},
                    "reconciliation": {
                        "reconciliation_id": "reconciliation-001"
                    },
                },
            )

        with mock.patch.object(
            integrator.ssl,
            "create_default_context",
            return_value=object(),
        ):
            status, response = integrator.post_mapped_alert(
                hook_url="https://proxy:8443/intake/wazuh",
                shared_secret="fixture-shared-secret",
                ca_file=Path("/run/aegisops-certs/lab.crt"),
                mapped_alert=self.native_alert,
                timeout_seconds=10,
                urlopen=fake_urlopen,
            )

        http_request = captured_request["request"]
        self.assertEqual(status, 202)
        self.assertEqual(captured_request["timeout"], 10)
        self.assertEqual(
            http_request.headers["Authorization"],
            "Bearer fixture-shared-secret",
        )
        receipt = integrator.build_receipt(
            native_alert_id=str(self.native_alert["id"]),
            status=status,
            response_payload=response,
        )
        self.assertEqual(receipt["disposition"], "created")
        self.assertEqual(receipt["aegisops_alert_id"], "alert-001")
        self.assertNotIn("secret", json.dumps(receipt).casefold())

    def test_runtime_requires_non_secret_file_bound_api_key_marker(self) -> None:
        with self.assertRaisesRegex(
            integrator.IntegrationError,
            "non-secret file-bound custody marker",
        ):
            integrator.run(
                [
                    "custom-aegisops",
                    "/tmp/alert.json",
                    "committed-secret",
                    "https://proxy:8443/intake/wazuh",
                ],
                {},
            )

    def test_control_plane_admits_and_deduplicates_native_wazuh_detection(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="0.0.0.0",
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",
                wazuh_ingest_trusted_proxy_cidrs=("172.31.67.10/32",),
            ),
            store=store,
        )
        mapped_alert = integrator.map_native_alert(
            self.native_alert,
            allowed_rule_id="5710",
        )

        created = service.ingest_wazuh_alert(
            raw_alert=mapped_alert,
            authorization_header="Bearer reviewed-shared-secret",
            forwarded_proto="https",
            reverse_proxy_secret_header="reviewed-proxy-secret",
            peer_addr="172.31.67.10",
        )
        duplicate = service.ingest_wazuh_alert(
            raw_alert=deepcopy(mapped_alert),
            authorization_header="Bearer reviewed-shared-secret",
            forwarded_proto="https",
            reverse_proxy_secret_header="reviewed-proxy-secret",
            peer_addr="172.31.67.10",
        )

        self.assertEqual(created.disposition, "created")
        self.assertEqual(duplicate.disposition, "deduplicated")
        self.assertEqual(duplicate.alert.alert_id, created.alert.alert_id)
        self.assertEqual(len(store.list(AlertRecord)), 1)
        self.assertEqual(len(store.list(CaseRecord)), 0)

        queue = service.inspect_analyst_queue()
        self.assertEqual(queue.total_records, 1)
        self.assertEqual(queue.records[0]["alert_id"], created.alert.alert_id)
        self.assertEqual(queue.records[0]["source_system"], "wazuh")
        self.assertIsNone(queue.records[0]["case_id"])
        self.assertEqual(
            queue.records[0]["reviewed_context"]["source"]["source_family"],
            "wazuh_detection",
        )

    def test_lab_configuration_keeps_intake_on_the_reviewed_proxy_boundary(self) -> None:
        proxy_config = (LAB_DIR / "config" / "control-plane.conf").read_text(
            encoding="utf-8"
        )
        compose = (LAB_DIR / "docker-compose.yml").read_text(encoding="utf-8")
        init_script = (LAB_DIR / "init.sh").read_text(encoding="utf-8")
        integration = (LAB_DIR / "wazuh" / "ossec-integration.xml").read_text(
            encoding="utf-8"
        )

        self.assertIn("location = /intake/wazuh {", proxy_config)
        self.assertIn("client_max_body_size 256k;", proxy_config)
        self.assertIn(
            "include /etc/nginx/certs/wazuh-intake-auth.conf;",
            proxy_config,
        )
        self.assertNotIn('"8080:8080"', compose)
        self.assertIn(
            "AEGISOPS_WAZUH_INGEST_SHARED_SECRET_FILE: "
            "/run/secrets/wazuh-ingest-shared-secret",
            compose,
        )
        self.assertIn(
            "AEGISOPS_WAZUH_INGEST_CA_FILE: /run/aegisops-certs/lab.crt",
            compose,
        )
        self.assertIn("proxy_set_header X-Forwarded-For \\$remote_addr;", init_script)
        self.assertIn(
            'proxy_set_header X-AegisOps-Proxy-Secret "${wazuh_ingest_proxy_secret}";',
            init_script,
        )
        self.assertIn("<name>custom-aegisops</name>", integration)
        self.assertIn("<rule_id>5710</rule_id>", integration)
        self.assertIn("<api_key>file-bound</api_key>", integration)
        self.assertNotIn("Bearer ", integration)

    def test_evidence_schema_distinguishes_real_capture_from_synthetic_fixture(self) -> None:
        schema = json.loads(
            (LAB_DIR / "wazuh" / "evidence-manifest.schema.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(schema["properties"]["source_mode"]["const"], "real_wazuh")
        self.assertIn(
            "live_capture_sanitized",
            schema["properties"]["fixture_provenance"]["enum"],
        )
        self.assertEqual(
            schema["properties"]["native_wazuh_rule_id"]["const"],
            "5710",
        )
        self.assertEqual(
            schema["properties"]["analyst_queue"]["properties"]["case_id"]["type"],
            "null",
        )
        self.assertEqual(
            schema["properties"]["negative_boundary"]["properties"][
                "authoritative_alert_delta"
            ]["const"],
            0,
        )


if __name__ == "__main__":
    unittest.main()
