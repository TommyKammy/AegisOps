from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import importlib.util
import json
import os
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
from aegisops.control_plane.reviewed_slice_policy import (
    REVIEWED_WAZUH_DETECTION_FIXED_PROVENANCE,
)
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
        for field_name, expected_value in (
            REVIEWED_WAZUH_DETECTION_FIXED_PROVENANCE.items()
        ):
            with self.subTest(field_name=field_name):
                self.assertEqual(mapped["data"][field_name], expected_value)

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
                ca_file=Path(
                    "/var/ossec/integrations/aegisops-lab-ca.crt"
                ),
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

    def test_receipt_journal_completes_short_writes_and_syncs(self) -> None:
        receipt = {
            "schema_version": "phase67-wazuh-receipt-v1",
            "native_wazuh_alert_id": "phase67-short-write",
            "disposition": "created",
        }
        real_write = os.write
        write_sizes: list[int] = []

        def short_write(descriptor: int, payload: bytes) -> int:
            write_size = max(1, len(payload) // 2)
            write_sizes.append(write_size)
            return real_write(descriptor, payload[:write_size])

        with tempfile.TemporaryDirectory() as directory:
            receipt_path = Path(directory) / "receipts.jsonl"
            with (
                mock.patch.object(
                    integrator.os,
                    "write",
                    side_effect=short_write,
                ),
                mock.patch.object(
                    integrator.os,
                    "fsync",
                    wraps=os.fsync,
                ) as fsync,
            ):
                integrator.append_receipt(receipt_path, receipt)

            lines = receipt_path.read_text(encoding="utf-8").splitlines()

        self.assertGreater(len(write_sizes), 1)
        self.assertEqual([json.loads(line) for line in lines], [receipt])
        fsync.assert_called_once()

    def test_receipt_journal_rejects_a_write_that_makes_no_progress(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            receipt_path = Path(directory) / "receipts.jsonl"
            with mock.patch.object(integrator.os, "write", return_value=0):
                with self.assertRaisesRegex(
                    integrator.IntegrationError,
                    "receipt append made no forward progress",
                ):
                    integrator.append_receipt(
                        receipt_path,
                        {"native_wazuh_alert_id": "phase67-zero-write"},
                    )

    def test_receipt_journal_rolls_back_a_partial_failed_append(self) -> None:
        existing_receipt = {
            "native_wazuh_alert_id": "phase67-existing",
            "disposition": "created",
        }
        failed_receipt = {
            "native_wazuh_alert_id": "phase67-partial-failure",
            "disposition": "created",
        }
        real_write = os.write
        write_attempt = 0

        def fail_after_partial_write(descriptor: int, payload: bytes) -> int:
            nonlocal write_attempt
            write_attempt += 1
            if write_attempt == 1:
                write_size = max(1, len(payload) // 2)
                return real_write(descriptor, payload[:write_size])
            raise OSError("simulated full receipt volume")

        with tempfile.TemporaryDirectory() as directory:
            receipt_path = Path(directory) / "receipts.jsonl"
            integrator.append_receipt(receipt_path, existing_receipt)
            with mock.patch.object(
                integrator.os,
                "write",
                side_effect=fail_after_partial_write,
            ):
                with self.assertRaisesRegex(
                    integrator.IntegrationError,
                    "simulated full receipt volume",
                ):
                    integrator.append_receipt(receipt_path, failed_receipt)

            lines = receipt_path.read_text(encoding="utf-8").splitlines()

        self.assertEqual([json.loads(line) for line in lines], [existing_receipt])

    def test_receipt_journal_keeps_concurrent_appends_as_complete_lines(self) -> None:
        receipts = [
            {
                "native_wazuh_alert_id": f"phase67-concurrent-{index}",
                "disposition": "created",
            }
            for index in range(32)
        ]

        with tempfile.TemporaryDirectory() as directory:
            receipt_path = Path(directory) / "receipts.jsonl"
            with ThreadPoolExecutor(max_workers=8) as executor:
                list(
                    executor.map(
                        lambda receipt: integrator.append_receipt(
                            receipt_path,
                            receipt,
                        ),
                        receipts,
                    )
                )

            parsed = [
                json.loads(line)
                for line in receipt_path.read_text(
                    encoding="utf-8"
                ).splitlines()
            ]

        self.assertCountEqual(parsed, receipts)

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
            source_family_header="wazuh_detection",
        )
        duplicate = service.ingest_wazuh_alert(
            raw_alert=deepcopy(mapped_alert),
            authorization_header="Bearer reviewed-shared-secret",
            forwarded_proto="https",
            reverse_proxy_secret_header="reviewed-proxy-secret",
            peer_addr="172.31.67.10",
            source_family_header="wazuh_detection",
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

    def test_control_plane_rejects_unreviewed_or_inconsistent_wazuh_rules(self) -> None:
        mapped_alert = integrator.map_native_alert(
            self.native_alert,
            allowed_rule_id="5710",
        )
        mutations = {
            "matching but unreviewed rule": ("9999", "9999"),
            "inconsistent provenance": ("5710", "9999"),
        }

        for label, (native_rule_id, provenance_rule_id) in mutations.items():
            with self.subTest(label=label):
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
                candidate = deepcopy(mapped_alert)
                candidate["rule"]["id"] = native_rule_id
                candidate["data"]["wazuh_rule_id"] = provenance_rule_id

                with self.assertRaisesRegex(
                    ValueError,
                    "requires matching reviewed rule id '5710'",
                ):
                    service.ingest_wazuh_alert(
                        raw_alert=candidate,
                        authorization_header="Bearer reviewed-shared-secret",
                        forwarded_proto="https",
                        reverse_proxy_secret_header="reviewed-proxy-secret",
                        peer_addr="172.31.67.10",
                        source_family_header="wazuh_detection",
                    )

                self.assertEqual(store.list(AlertRecord), ())
                self.assertEqual(store.list(CaseRecord), ())
                self.assertEqual(service.inspect_analyst_queue().total_records, 0)

    def test_control_plane_rejects_proxy_attested_family_relabeling(self) -> None:
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
        candidate = integrator.map_native_alert(
            self.native_alert,
            allowed_rule_id="5710",
        )
        candidate["rule"]["id"] = "9999"
        candidate["data"]["wazuh_rule_id"] = "9999"
        candidate["data"]["source_family"] = "github_audit"

        with self.assertRaisesRegex(
            ValueError,
            "data.source_family must match the source family attested by "
            "the reviewed reverse proxy",
        ):
            service.ingest_wazuh_alert(
                raw_alert=candidate,
                authorization_header="Bearer reviewed-shared-secret",
                forwarded_proto="https",
                reverse_proxy_secret_header="reviewed-proxy-secret",
                peer_addr="172.31.67.10",
                source_family_header="wazuh_detection",
            )

        self.assertEqual(store.list(AlertRecord), ())
        self.assertEqual(store.list(CaseRecord), ())
        self.assertEqual(service.inspect_analyst_queue().total_records, 0)

    def test_control_plane_rejects_inconsistent_native_wazuh_provenance(self) -> None:
        mapped_alert = integrator.map_native_alert(
            self.native_alert,
            allowed_rule_id="5710",
        )
        mutations = {
            "event_id": "tampered-event-id",
            "event_timestamp": "2026-07-28T00:00:00+00:00",
            "source_id": "tampered-manager",
            "wazuh_manager_id": "tampered-manager",
            "wazuh_rule_level": "99",
        }

        for field_name, tampered_value in mutations.items():
            with self.subTest(field_name=field_name):
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
                candidate = deepcopy(mapped_alert)
                candidate["data"][field_name] = tampered_value

                with self.assertRaisesRegex(
                    ValueError,
                    rf"data\.{field_name} must match its native Wazuh alert value",
                ):
                    service.ingest_wazuh_alert(
                        raw_alert=candidate,
                        authorization_header="Bearer reviewed-shared-secret",
                        forwarded_proto="https",
                        reverse_proxy_secret_header="reviewed-proxy-secret",
                        peer_addr="172.31.67.10",
                        source_family_header="wazuh_detection",
                    )

                self.assertEqual(store.list(AlertRecord), ())
                self.assertEqual(store.list(CaseRecord), ())
                self.assertEqual(service.inspect_analyst_queue().total_records, 0)

    def test_control_plane_rejects_forged_fixed_wazuh_provenance(self) -> None:
        mapped_alert = integrator.map_native_alert(
            self.native_alert,
            allowed_rule_id="5710",
        )

        for field_name in REVIEWED_WAZUH_DETECTION_FIXED_PROVENANCE:
            with self.subTest(field_name=field_name):
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
                candidate = deepcopy(mapped_alert)
                candidate["data"][field_name] = "forged-phase67-provenance"

                with self.assertRaisesRegex(
                    ValueError,
                    rf"data\.{field_name} must match its reviewed Phase 67 "
                    "Wazuh mapping value",
                ):
                    service.ingest_wazuh_alert(
                        raw_alert=candidate,
                        authorization_header="Bearer reviewed-shared-secret",
                        forwarded_proto="https",
                        reverse_proxy_secret_header="reviewed-proxy-secret",
                        peer_addr="172.31.67.10",
                        source_family_header="wazuh_detection",
                    )

                self.assertEqual(store.list(AlertRecord), ())
                self.assertEqual(store.list(CaseRecord), ())
                self.assertEqual(service.inspect_analyst_queue().total_records, 0)

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
        self.assertIn(
            'proxy_set_header X-AegisOps-Source-Family "";',
            proxy_config,
        )
        self.assertNotIn('"8080:8080"', compose)
        self.assertIn(
            "AEGISOPS_WAZUH_INGEST_SHARED_SECRET_FILE: "
            "/run/secrets/wazuh-ingest-shared-secret",
            compose,
        )
        self.assertIn(
            "AEGISOPS_WAZUH_INGEST_CA_FILE: "
            "/var/ossec/integrations/aegisops-lab-ca.crt",
            compose,
        )
        self.assertIn("proxy_set_header X-Forwarded-For \\$remote_addr;", init_script)
        self.assertIn(
            'proxy_set_header X-AegisOps-Proxy-Secret "${wazuh_ingest_proxy_secret}";',
            init_script,
        )
        self.assertIn(
            'proxy_set_header X-AegisOps-Source-Family "wazuh_detection";',
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
        self.assertIn("worktree_artifact_digest", schema["required"])
        self.assertIn("runtime_artifact_digest", schema["required"])
        self.assertEqual(
            schema["properties"]["runtime_artifact_digest"]["pattern"],
            "^[0-9a-f]{64}$",
        )
        self.assertIn("aegisops_alert_id", schema["required"])
        self.assertEqual(
            schema["$defs"]["first_delivery"]["properties"]["disposition"][
                "const"
            ],
            "created",
        )
        self.assertEqual(
            schema["$defs"]["duplicate_delivery"]["properties"]["disposition"][
                "const"
            ],
            "deduplicated",
        )
        self.assertNotIn(
            "aegisops_alert_id",
            schema["$defs"]["first_delivery"]["properties"],
        )
        self.assertNotIn(
            "aegisops_alert_id",
            schema["$defs"]["duplicate_delivery"]["properties"],
        )
        self.assertNotIn(
            "alert_id",
            schema["properties"]["analyst_queue"]["properties"],
        )

    def test_trial_has_one_native_event_and_protects_runtime_attribution(self) -> None:
        trial = (LAB_DIR / "test-wazuh-intake.sh").read_text(encoding="utf-8")
        up_script = (LAB_DIR / "up.sh").read_text(encoding="utf-8")

        self.assertEqual(
            trial.count("Failed password for invalid user %s"),
            1,
        )
        self.assertNotIn(
            "aegisops-phase67-invalid",
            trial,
        )
        self.assertIn("secrets.token_hex(8)", trial)
        self.assertIn(
            'trial_username="aegisops-phase67-${trial_nonce}"',
            trial,
        )
        self.assertIn('--header "@${authenticated_header_file}"', trial)
        self.assertNotIn(
            '--header "Authorization: Bearer ${shared_secret}"',
            trial,
        )
        self.assertIn(
            "running Phase 67 artifacts do not match the worktree",
            trial,
        )
        self.assertIn(
            "unreviewed Wazuh rule must return HTTP 400",
            trial,
        )
        self.assertIn(
            "forged fixed Wazuh provenance must return HTTP 400",
            trial,
        )
        self.assertIn(
            "relabeled Wazuh source family must return HTTP 400",
            trial,
        )
        self.assertIn(
            'mktemp "${AEGISOPS_LAB_EVIDENCE_DIR}/.wazuh-intake-',
            trial,
        )
        self.assertIn(
            """jq -e 'type == "object"' "${evidence_staging_file}" >/dev/null""",
            trial,
        )
        self.assertIn('rm -f "${evidence_staging_file}"', trial)
        self.assertIn(
            'mv "${evidence_staging_file}" "${evidence_file}"',
            trial,
        )
        self.assertIn("integrator.map_native_alert(", trial)
        self.assertIn(
            "runtime_artifact_digest: $runtime_artifact_digest",
            trial,
        )
        self.assertIn(
            'file_digest "${AEGISOPS_LAB_WAZUH_MANAGER_CONFIG}"',
            trial,
        )
        self.assertIn(
            "runtime_file_digest wazuh-manager /var/ossec/etc/ossec.conf",
            trial,
        )
        self.assertIn(
            '"wazuh-manager-config=${worktree_manager_config}"',
            trial,
        )
        self.assertIn(
            '"wazuh-manager-config=${runtime_manager_config}"',
            trial,
        )
        self.assertIn(
            '"wazuh-proxy-ca=${worktree_proxy_ca}"',
            trial,
        )
        self.assertIn(
            '"wazuh-proxy-ca=${runtime_proxy_ca}"',
            trial,
        )
        manager_entrypoint = (
            LAB_DIR / "wazuh" / "manager-entrypoint.sh"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "/run/aegisops-bootstrap/lab.crt",
            manager_entrypoint,
        )
        self.assertIn(
            "/var/ossec/integrations/aegisops-lab-ca.crt",
            manager_entrypoint,
        )
        self.assertIn("  0644 \\", manager_entrypoint)
        self.assertIn("LC_ALL=C date -u '+%b %e %H:%M:%S'", trial)
        self.assertIn("wazuh-integration-artifacts.sha256", up_script)
        self.assertIn(
            '[[ "$(<"${wazuh_integration_state}")" != '
            '"${wazuh_integration_digest}" ]]',
            up_script,
        )
        self.assertIn(
            'cmp -s "${expected_manager_config}" '
            '"${AEGISOPS_LAB_WAZUH_MANAGER_CONFIG}"',
            up_script,
        )
        for artifact in (
            "manager-entrypoint.sh",
            "custom-aegisops",
            "aegisops_wazuh_integrator.py",
            "ossec-integration.xml",
            "proxy-ca.crt",
        ):
            self.assertIn(artifact, up_script)


if __name__ == "__main__":
    unittest.main()
