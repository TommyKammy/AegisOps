from __future__ import annotations

import contextlib
from datetime import datetime, timezone
import http.client
import io
import json
import pathlib
import sys
import threading
import unittest
from urllib import error, request
from unittest import mock


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

import main
from aegisops_control_plane.config import RuntimeConfig
from aegisops_control_plane.adapters.wazuh import WazuhAlertAdapter
from aegisops_control_plane.models import (
    AlertRecord,
    AnalyticSignalRecord,
    EvidenceRecord,
    RecommendationRecord,
    ReconciliationRecord,
)
from aegisops_control_plane.service import AegisOpsControlPlaneService
from postgres_test_support import make_store


FIXTURES_ROOT = pathlib.Path(__file__).resolve().parent / "fixtures" / "wazuh"


def _load_wazuh_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES_ROOT / name).read_text(encoding="utf-8"))


class ControlPlaneCliInspectionTests(unittest.TestCase):
    def test_runtime_command_uses_runtime_service_builder_when_not_injected(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        stdout = io.StringIO()

        with mock.patch.object(
            main,
            "build_runtime_service",
            return_value=service,
        ) as build_runtime_service:
            main.main(["runtime"], stdout=stdout)

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["persistence_mode"], "postgresql")
        build_runtime_service.assert_called_once_with()

    def test_runtime_command_honors_injected_service_snapshot(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=9411,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                opensearch_url="https://opensearch.internal",
                n8n_base_url="https://n8n.internal",
            ),
            store=store,
        )
        stdout = io.StringIO()

        main.main(["runtime"], stdout=stdout, service=service)

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["bind_host"], "127.0.0.1")
        self.assertEqual(payload["bind_port"], 9411)
        self.assertEqual(payload["postgres_dsn"], "postgresql://control-plane.local/aegisops")
        self.assertEqual(payload["persistence_mode"], "postgresql")

    def test_serve_command_uses_long_running_runtime_surface(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        with mock.patch.object(
            main,
            "build_runtime_service",
            return_value=service,
        ) as build_runtime_service, mock.patch.object(
            main,
            "run_control_plane_service",
            return_value=0,
        ) as run_control_plane_service:
            exit_code = main.main(["serve"])

        self.assertEqual(exit_code, 0)
        build_runtime_service.assert_called_once_with()
        run_control_plane_service.assert_called_once_with(service, stderr=mock.ANY)

    def test_long_running_runtime_surface_starts_http_server(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=8089,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",
            ),
            store=store,
        )

        with mock.patch.object(main, "ThreadingHTTPServer") as server_cls:
            server = server_cls.return_value

            exit_code = main.run_control_plane_service(service)

        self.assertEqual(exit_code, 0)
        server_cls.assert_called_once_with(("127.0.0.1", 8089), mock.ANY)
        server.serve_forever.assert_called_once_with()
        server.server_close.assert_called_once_with()

    def test_long_running_runtime_surface_exposes_runtime_and_inspection_http_views(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",
            ),
            store=store,
        )
        compared_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        service.persist_record(
            AlertRecord(
                alert_id="alert-http-001",
                finding_id="finding-http-001",
                analytic_signal_id="signal-http-001",
                case_id=None,
                lifecycle_state="new",
            )
        )
        service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-http-001",
                subject_linkage={"alert_ids": ("alert-http-001",)},
                alert_id="alert-http-001",
                finding_id="finding-http-001",
                analytic_signal_id="signal-http-001",
                execution_run_id=None,
                linked_execution_run_ids=(),
                correlation_key="claim:host-001:http-runtime",
                first_seen_at=compared_at,
                last_seen_at=compared_at,
                ingest_disposition="created",
                mismatch_summary="created during HTTP inspection test",
                compared_at=compared_at,
                lifecycle_state="matched",
            )
        )

        servers: list[main.ThreadingHTTPServer] = []

        class RecordingServer(main.ThreadingHTTPServer):
            def __init__(self, server_address: tuple[str, int], handler_class: type) -> None:
                super().__init__(server_address, handler_class)
                servers.append(self)

        with mock.patch.object(main, "ThreadingHTTPServer", RecordingServer):
            thread = threading.Thread(
                target=main.run_control_plane_service,
                args=(service,),
                daemon=True,
            )
            thread.start()
            try:
                for _ in range(100):
                    if servers:
                        break
                    thread.join(0.01)
                self.assertTrue(servers, "expected test HTTP server to start")

                base_url = f"http://127.0.0.1:{servers[0].server_port}"
                runtime_payload = json.loads(
                    request.urlopen(f"{base_url}/runtime", timeout=2).read().decode("utf-8")
                )
                records_payload = json.loads(
                    request.urlopen(
                        f"{base_url}/inspect-records?family=alert",
                        timeout=2,
                    ).read().decode("utf-8")
                )
                status_payload = json.loads(
                    request.urlopen(
                        f"{base_url}/inspect-reconciliation-status",
                        timeout=2,
                    ).read().decode("utf-8")
                )

                self.assertEqual(runtime_payload["persistence_mode"], "postgresql")
                self.assertEqual(records_payload["record_family"], "alert")
                self.assertEqual(records_payload["records"][0]["alert_id"], "alert-http-001")
                self.assertEqual(status_payload["by_ingest_disposition"], {"created": 1})
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_long_running_runtime_surface_exposes_analyst_queue_alert_detail_and_case_detail_http_views(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",
            ),
            store=store,
        )
        alert = _load_wazuh_fixture("github-audit-alert.json")
        admitted = service.ingest_wazuh_alert(
            raw_alert=alert,
            authorization_header="Bearer reviewed-shared-secret",
            forwarded_proto="https",
            reverse_proxy_secret_header="reviewed-proxy-secret",
            peer_addr="127.0.0.1",
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)

        servers: list[main.ThreadingHTTPServer] = []

        class RecordingServer(main.ThreadingHTTPServer):
            def __init__(self, server_address: tuple[str, int], handler_class: type) -> None:
                super().__init__(server_address, handler_class)
                servers.append(self)

        with mock.patch.object(main, "ThreadingHTTPServer", RecordingServer):
            thread = threading.Thread(
                target=main.run_control_plane_service,
                args=(service,),
                daemon=True,
            )
            thread.start()
            try:
                for _ in range(100):
                    if servers:
                        break
                    thread.join(0.01)
                self.assertTrue(servers, "expected test HTTP server to start")

                base_url = f"http://127.0.0.1:{servers[0].server_port}"
                queue_payload = json.loads(
                    request.urlopen(
                        f"{base_url}/inspect-analyst-queue",
                        timeout=2,
                    ).read().decode("utf-8")
                )
                detail_payload = json.loads(
                    request.urlopen(
                        (
                            f"{base_url}/inspect-alert-detail"
                            f"?alert_id={admitted.alert.alert_id}"
                        ),
                        timeout=2,
                    ).read().decode("utf-8")
                )
                case_payload = json.loads(
                    request.urlopen(  # noqa: S310 - local in-process test HTTP server
                        (
                            f"{base_url}/inspect-case-detail"
                            f"?case_id={promoted_case.case_id}"
                        ),
                        timeout=2,
                    ).read().decode("utf-8")
                )

                self.assertTrue(queue_payload["read_only"])
                self.assertEqual(queue_payload["queue_name"], "analyst_review")
                self.assertEqual(queue_payload["total_records"], 1)
                self.assertEqual(
                    queue_payload["records"][0]["alert_id"],
                    admitted.alert.alert_id,
                )

                self.assertTrue(detail_payload["read_only"])
                self.assertEqual(detail_payload["alert_id"], admitted.alert.alert_id)
                self.assertEqual(detail_payload["alert"]["alert_id"], admitted.alert.alert_id)
                self.assertEqual(detail_payload["case_record"]["case_id"], promoted_case.case_id)
                self.assertEqual(
                    detail_payload["latest_reconciliation"]["reconciliation_id"],
                    admitted.reconciliation.reconciliation_id,
                )
                self.assertEqual(
                    detail_payload["provenance"],
                    {
                        "admission_kind": "live",
                        "admission_channel": "live_wazuh_webhook",
                    },
                )
                self.assertEqual(
                    detail_payload["lineage"]["substrate_detection_record_ids"],
                    ["wazuh:1731595300.1234567"],
                )
                self.assertEqual(
                    detail_payload["lineage"]["accountable_source_identities"],
                    ["manager:wazuh-manager-github-1"],
                )
                self.assertEqual(
                    detail_payload["reviewed_context"]["source"]["source_family"],
                    "github_audit",
                )
                self.assertTrue(case_payload["read_only"])
                self.assertEqual(case_payload["case_id"], promoted_case.case_id)
                self.assertEqual(
                    case_payload["case_record"]["case_id"],
                    promoted_case.case_id,
                )
                self.assertEqual(
                    case_payload["linked_evidence_ids"],
                    [detail_payload["linked_evidence_records"][0]["evidence_id"]],
                )
                self.assertEqual(
                    case_payload["advisory_output"]["output_kind"],
                    "case_summary",
                )
                self.assertEqual(
                    case_payload["advisory_output"]["status"],
                    "ready",
                )
                self.assertEqual(
                    case_payload["reviewed_context"]["source"]["source_family"],
                    "github_audit",
                )
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_long_running_runtime_surface_rejects_blank_alert_detail_query(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",
            ),
            store=store,
        )
        servers: list[main.ThreadingHTTPServer] = []

        class RecordingServer(main.ThreadingHTTPServer):
            def __init__(self, server_address: tuple[str, int], handler_class: type) -> None:
                super().__init__(server_address, handler_class)
                servers.append(self)

        with mock.patch.object(main, "ThreadingHTTPServer", RecordingServer):
            thread = threading.Thread(
                target=main.run_control_plane_service,
                args=(service,),
                daemon=True,
            )
            thread.start()
            try:
                for _ in range(100):
                    if servers:
                        break
                    thread.join(0.01)
                self.assertTrue(servers, "expected test HTTP server to start")

                with self.assertRaises(error.HTTPError) as exc_info:
                    request.urlopen(
                        (
                            "http://127.0.0.1:"
                            f"{servers[0].server_port}/inspect-alert-detail?alert_id=%20%20"
                        ),
                        timeout=2,
                    )

                self.assertEqual(exc_info.exception.code, 400)
                error_payload = json.loads(exc_info.exception.read().decode("utf-8"))
                self.assertEqual(error_payload["error"], "invalid_request")
                self.assertEqual(
                    error_payload["message"],
                    "alert_id query parameter is required",
                )
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_long_running_runtime_surface_rejects_direct_backend_wazuh_ingest_bypass(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",
            ),
            store=store,
        )
        servers: list[main.ThreadingHTTPServer] = []

        class RecordingServer(main.ThreadingHTTPServer):
            def __init__(self, server_address: tuple[str, int], handler_class: type) -> None:
                super().__init__(server_address, handler_class)
                servers.append(self)

        with mock.patch.object(main, "ThreadingHTTPServer", RecordingServer):
            thread = threading.Thread(
                target=main.run_control_plane_service,
                args=(service,),
                daemon=True,
            )
            thread.start()
            try:
                for _ in range(100):
                    if servers:
                        break
                    thread.join(0.01)
                self.assertTrue(servers, "expected test HTTP server to start")

                alert = _load_wazuh_fixture("github-audit-alert.json")
                request_body = json.dumps(alert).encode("utf-8")
                ingest_request = request.Request(
                    f"http://127.0.0.1:{servers[0].server_port}/intake/wazuh",
                    data=request_body,
                    method="POST",
                    headers={
                        "Authorization": "Bearer reviewed-shared-secret",
                        "Content-Type": "application/json",
                        "X-Forwarded-Proto": "https",
                    },
                )

                with self.assertRaisesRegex(error.HTTPError, "403"):
                    request.urlopen(ingest_request, timeout=2)

                self.assertEqual(store.list(AlertRecord), ())
                self.assertEqual(store.list(AnalyticSignalRecord), ())
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_long_running_runtime_surface_rejects_missing_wazuh_shared_secret(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=8089,
                postgres_dsn="postgresql://control-plane.local/aegisops",
            ),
            store=store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET must be set",
        ):
            main.run_control_plane_service(service)

    def test_long_running_runtime_surface_rejects_missing_wazuh_reverse_proxy_secret(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=8089,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
            ),
            store=store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET must be set",
        ):
            main.run_control_plane_service(service)

    def test_long_running_runtime_surface_rejects_non_loopback_wazuh_ingest_without_trusted_proxies(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="0.0.0.0",
                port=8089,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",
            ),
            store=store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_TRUSTED_PROXY_CIDRS must be set",
        ):
            main.run_control_plane_service(service)

    def test_long_running_runtime_surface_rejects_wazuh_ingest_without_bearer_auth(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",
            ),
            store=store,
        )
        servers: list[main.ThreadingHTTPServer] = []

        class RecordingServer(main.ThreadingHTTPServer):
            def __init__(self, server_address: tuple[str, int], handler_class: type) -> None:
                super().__init__(server_address, handler_class)
                servers.append(self)

        with mock.patch.object(main, "ThreadingHTTPServer", RecordingServer):
            thread = threading.Thread(
                target=main.run_control_plane_service,
                args=(service,),
                daemon=True,
            )
            thread.start()
            try:
                for _ in range(100):
                    if servers:
                        break
                    thread.join(0.01)
                self.assertTrue(servers, "expected test HTTP server to start")

                ingest_request = request.Request(
                    f"http://127.0.0.1:{servers[0].server_port}/intake/wazuh",
                    data=json.dumps(_load_wazuh_fixture("github-audit-alert.json")).encode("utf-8"),
                    method="POST",
                    headers={
                        "Content-Type": "application/json",
                        "X-AegisOps-Proxy-Secret": "reviewed-proxy-secret",
                        "X-Forwarded-Proto": "https",
                    },
                )

                with self.assertRaisesRegex(error.HTTPError, "403"):
                    request.urlopen(ingest_request, timeout=2)

                self.assertEqual(store.list(AlertRecord), ())
                self.assertEqual(store.list(AnalyticSignalRecord), ())
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_long_running_runtime_surface_rejects_wazuh_ingest_with_wrong_bearer_secret(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",
            ),
            store=store,
        )
        servers: list[main.ThreadingHTTPServer] = []

        class RecordingServer(main.ThreadingHTTPServer):
            def __init__(self, server_address: tuple[str, int], handler_class: type) -> None:
                super().__init__(server_address, handler_class)
                servers.append(self)

        with mock.patch.object(main, "ThreadingHTTPServer", RecordingServer):
            thread = threading.Thread(
                target=main.run_control_plane_service,
                args=(service,),
                daemon=True,
            )
            thread.start()
            try:
                for _ in range(100):
                    if servers:
                        break
                    thread.join(0.01)
                self.assertTrue(servers, "expected test HTTP server to start")

                ingest_request = request.Request(
                    f"http://127.0.0.1:{servers[0].server_port}/intake/wazuh",
                    data=json.dumps(_load_wazuh_fixture("github-audit-alert.json")).encode("utf-8"),
                    method="POST",
                    headers={
                        "Authorization": "Bearer wrong-secret",
                        "Content-Type": "application/json",
                        "X-AegisOps-Proxy-Secret": "reviewed-proxy-secret",
                        "X-Forwarded-Proto": "https",
                    },
                )

                with self.assertRaisesRegex(error.HTTPError, "403"):
                    request.urlopen(ingest_request, timeout=2)

                self.assertEqual(store.list(AlertRecord), ())
                self.assertEqual(store.list(AnalyticSignalRecord), ())
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_long_running_runtime_surface_rejects_wazuh_ingest_without_https_forwarding(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",
            ),
            store=store,
        )
        servers: list[main.ThreadingHTTPServer] = []

        class RecordingServer(main.ThreadingHTTPServer):
            def __init__(self, server_address: tuple[str, int], handler_class: type) -> None:
                super().__init__(server_address, handler_class)
                servers.append(self)

        with mock.patch.object(main, "ThreadingHTTPServer", RecordingServer):
            thread = threading.Thread(
                target=main.run_control_plane_service,
                args=(service,),
                daemon=True,
            )
            thread.start()
            try:
                for _ in range(100):
                    if servers:
                        break
                    thread.join(0.01)
                self.assertTrue(servers, "expected test HTTP server to start")

                ingest_request = request.Request(
                    f"http://127.0.0.1:{servers[0].server_port}/intake/wazuh",
                    data=json.dumps(_load_wazuh_fixture("github-audit-alert.json")).encode("utf-8"),
                    method="POST",
                    headers={
                        "Authorization": "Bearer reviewed-shared-secret",
                        "Content-Type": "application/json",
                        "X-AegisOps-Proxy-Secret": "reviewed-proxy-secret",
                    },
                )

                with self.assertRaisesRegex(error.HTTPError, "403"):
                    request.urlopen(ingest_request, timeout=2)

                self.assertEqual(store.list(AlertRecord), ())
                self.assertEqual(store.list(AnalyticSignalRecord), ())
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_long_running_runtime_surface_rejects_non_github_wazuh_family(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",
            ),
            store=store,
        )
        servers: list[main.ThreadingHTTPServer] = []

        class RecordingServer(main.ThreadingHTTPServer):
            def __init__(self, server_address: tuple[str, int], handler_class: type) -> None:
                super().__init__(server_address, handler_class)
                servers.append(self)

        with mock.patch.object(main, "ThreadingHTTPServer", RecordingServer):
            thread = threading.Thread(
                target=main.run_control_plane_service,
                args=(service,),
                daemon=True,
            )
            thread.start()
            try:
                for _ in range(100):
                    if servers:
                        break
                    thread.join(0.01)
                self.assertTrue(servers, "expected test HTTP server to start")

                ingest_request = request.Request(
                    f"http://127.0.0.1:{servers[0].server_port}/intake/wazuh",
                    data=json.dumps(_load_wazuh_fixture("microsoft-365-audit-alert.json")).encode("utf-8"),
                    method="POST",
                    headers={
                        "Authorization": "Bearer reviewed-shared-secret",
                        "Content-Type": "application/json",
                        "X-AegisOps-Proxy-Secret": "reviewed-proxy-secret",
                        "X-Forwarded-Proto": "https",
                    },
                )

                with self.assertRaisesRegex(error.HTTPError, "400"):
                    request.urlopen(ingest_request, timeout=2)

                self.assertEqual(store.list(AlertRecord), ())
                self.assertEqual(store.list(AnalyticSignalRecord), ())
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_service_rejects_non_loopback_wazuh_ingest_from_untrusted_proxy_peer(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="0.0.0.0",
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",
                wazuh_ingest_trusted_proxy_cidrs=("10.10.0.5/32",),
            ),
            store=store,
        )

        with self.assertRaisesRegex(
            PermissionError,
            "reviewed reverse proxy peer boundary",
        ):
            service.ingest_wazuh_alert(
                raw_alert=_load_wazuh_fixture("github-audit-alert.json"),
                authorization_header="Bearer reviewed-shared-secret",
                forwarded_proto="https",
                reverse_proxy_secret_header="reviewed-proxy-secret",
                peer_addr="10.10.0.6",
            )

    def test_service_admits_non_loopback_wazuh_ingest_from_trusted_proxy_peer(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="0.0.0.0",
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",
                wazuh_ingest_trusted_proxy_cidrs=("10.10.0.5/32",),
            ),
            store=store,
        )

        ingest_result = service.ingest_wazuh_alert(
            raw_alert=_load_wazuh_fixture("github-audit-alert.json"),
            authorization_header="Bearer reviewed-shared-secret",
            forwarded_proto="https",
            reverse_proxy_secret_header="reviewed-proxy-secret",
            peer_addr="10.10.0.5",
        )

        self.assertEqual(ingest_result.disposition, "created")
        self.assertEqual(len(store.list(AlertRecord)), 1)
        self.assertEqual(len(store.list(AnalyticSignalRecord)), 1)

    def test_long_running_runtime_surface_rejects_oversized_wazuh_ingest_body(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",
            ),
            store=store,
        )
        servers: list[main.ThreadingHTTPServer] = []

        class RecordingServer(main.ThreadingHTTPServer):
            def __init__(self, server_address: tuple[str, int], handler_class: type) -> None:
                super().__init__(server_address, handler_class)
                servers.append(self)

        with mock.patch.object(main, "ThreadingHTTPServer", RecordingServer):
            thread = threading.Thread(
                target=main.run_control_plane_service,
                args=(service,),
                daemon=True,
            )
            thread.start()
            try:
                for _ in range(100):
                    if servers:
                        break
                    thread.join(0.01)
                self.assertTrue(servers, "expected test HTTP server to start")

                connection = http.client.HTTPConnection(
                    "127.0.0.1",
                    servers[0].server_port,
                    timeout=2,
                )
                connection.putrequest("POST", "/intake/wazuh")
                connection.putheader("Authorization", "Bearer reviewed-shared-secret")
                connection.putheader("Content-Type", "application/json")
                connection.putheader("X-AegisOps-Proxy-Secret", "reviewed-proxy-secret")
                connection.putheader("X-Forwarded-Proto", "https")
                connection.putheader(
                    "Content-Length",
                    str(main.MAX_WAZUH_INGEST_BODY_BYTES + 1),
                )
                connection.endheaders()

                response = connection.getresponse()
                self.assertEqual(response.status, 413)
                response_body = json.loads(response.read().decode("utf-8"))
                connection.close()
                self.assertEqual(response_body["error"], "request_too_large")
                self.assertEqual(store.list(AlertRecord), ())
                self.assertEqual(store.list(AnalyticSignalRecord), ())
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_cli_renders_read_only_record_and_reconciliation_views(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        compared_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        service.persist_record(
            AlertRecord(
                alert_id="alert-001",
                finding_id="finding-001",
                analytic_signal_id="signal-001",
                case_id=None,
                lifecycle_state="new",
            )
        )
        service.persist_record(
            AnalyticSignalRecord(
                analytic_signal_id="signal-001",
                substrate_detection_record_id="substrate-detection-001",
                finding_id="finding-001",
                alert_ids=("alert-001",),
                case_ids=(),
                correlation_key="claim:host-001:privilege-escalation",
                first_seen_at=compared_at,
                last_seen_at=compared_at,
                lifecycle_state="active",
            )
        )
        service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-001",
                subject_linkage={"alert_ids": ("alert-001",)},
                alert_id="alert-001",
                finding_id="finding-001",
                analytic_signal_id="signal-001",
                execution_run_id=None,
                linked_execution_run_ids=(),
                correlation_key="claim:host-001:privilege-escalation",
                first_seen_at=compared_at,
                last_seen_at=compared_at,
                ingest_disposition="created",
                mismatch_summary="created upstream analytic signal into alert lifecycle",
                compared_at=compared_at,
                lifecycle_state="matched",
            )
        )

        records_stdout = io.StringIO()
        analytic_signals_stdout = io.StringIO()
        status_stdout = io.StringIO()

        main.main(
            ["inspect-records", "--family", "alert"],
            stdout=records_stdout,
            service=service,
        )
        main.main(
            ["inspect-records", "--family", "analytic_signal"],
            stdout=analytic_signals_stdout,
            service=service,
        )
        main.main(
            ["inspect-reconciliation-status"],
            stdout=status_stdout,
            service=service,
        )

        records_payload = json.loads(records_stdout.getvalue())
        analytic_signals_payload = json.loads(analytic_signals_stdout.getvalue())
        status_payload = json.loads(status_stdout.getvalue())

        self.assertTrue(records_payload["read_only"])
        self.assertEqual(records_payload["record_family"], "alert")
        self.assertEqual(records_payload["records"][0]["alert_id"], "alert-001")

        self.assertTrue(analytic_signals_payload["read_only"])
        self.assertEqual(analytic_signals_payload["record_family"], "analytic_signal")
        self.assertEqual(
            analytic_signals_payload["records"][0]["analytic_signal_id"],
            "signal-001",
        )
        self.assertEqual(
            analytic_signals_payload["records"][0]["substrate_detection_record_id"],
            "substrate-detection-001",
        )

        self.assertTrue(status_payload["read_only"])
        self.assertEqual(status_payload["total_records"], 1)
        self.assertEqual(status_payload["by_ingest_disposition"], {"created": 1})
        self.assertEqual(
            status_payload["latest_compared_at"],
            "2026-04-05T12:00:00+00:00",
        )

    def test_cli_renders_wazuh_business_hours_analyst_queue_view(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        adapter = WazuhAlertAdapter()
        admitted = service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(
                _load_wazuh_fixture("agent-origin-alert.json")
            ),
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)

        stdout = io.StringIO()
        main.main(["inspect-analyst-queue"], stdout=stdout, service=service)

        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["read_only"])
        self.assertEqual(payload["queue_name"], "analyst_review")
        self.assertEqual(payload["total_records"], 1)
        self.assertEqual(payload["records"][0]["alert_id"], admitted.alert.alert_id)
        self.assertEqual(
            payload["records"][0]["queue_selection"],
            "business_hours_triage",
        )
        self.assertEqual(payload["records"][0]["review_state"], "case_required")
        self.assertEqual(payload["records"][0]["case_id"], promoted_case.case_id)
        self.assertEqual(payload["records"][0]["case_lifecycle_state"], "open")
        self.assertEqual(payload["records"][0]["source_system"], "wazuh")
        self.assertEqual(
            payload["records"][0]["accountable_source_identities"],
            ["agent:007"],
        )
        self.assertEqual(
            payload["records"][0]["reviewed_context"]["location"],
            "/var/log/auth.log",
        )
        self.assertEqual(
            payload["records"][0]["native_rule"]["description"],
            "SSH brute force attempt",
        )
        self.assertEqual(
            payload["records"][0]["substrate_detection_record_ids"],
            ["wazuh:1731594986.4931506"],
        )

    def test_cli_renders_reviewed_wazuh_alert_detail_view(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",
            ),
            store=store,
        )
        admitted = service.ingest_wazuh_alert(
            raw_alert=_load_wazuh_fixture("github-audit-alert.json"),
            authorization_header="Bearer reviewed-shared-secret",
            forwarded_proto="https",
            reverse_proxy_secret_header="reviewed-proxy-secret",
            peer_addr="127.0.0.1",
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)

        stdout = io.StringIO()
        main.main(
            ["inspect-alert-detail", "--alert-id", admitted.alert.alert_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["read_only"])
        self.assertEqual(payload["alert_id"], admitted.alert.alert_id)
        self.assertEqual(payload["alert"]["alert_id"], admitted.alert.alert_id)
        self.assertEqual(payload["case_record"]["case_id"], promoted_case.case_id)
        self.assertEqual(
            payload["latest_reconciliation"]["reconciliation_id"],
            admitted.reconciliation.reconciliation_id,
        )
        self.assertEqual(
            payload["provenance"],
            {
                "admission_channel": "live_wazuh_webhook",
                "admission_kind": "live",
            },
        )
        self.assertEqual(
            payload["lineage"]["substrate_detection_record_ids"],
            ["wazuh:1731595300.1234567"],
        )
        self.assertEqual(
            payload["lineage"]["accountable_source_identities"],
            ["manager:wazuh-manager-github-1"],
        )
        self.assertEqual(
            payload["reviewed_context"]["source"]["source_family"],
            "github_audit",
        )

    def test_cli_renders_analyst_assistant_context_view_for_a_case(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        compared_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        reviewed_context = {
            "asset": {
                "asset_id": "asset-repo-001",
                "criticality": "high",
                "ownership": "platform-security",
            },
            "identity": {
                "identity_id": "principal-001",
                "owner": "identity-operations",
            },
        }
        admitted = service.ingest_finding_alert(
            finding_id="finding-assistant-cli-001",
            analytic_signal_id="signal-assistant-cli-001",
            substrate_detection_record_id="substrate-detection-assistant-cli-001",
            correlation_key="claim:asset-repo-001:assistant-cli-review",
            first_seen_at=compared_at,
            last_seen_at=compared_at,
            reviewed_context=reviewed_context,
        )
        evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-assistant-cli-001",
                source_record_id="substrate-detection-assistant-cli-001",
                alert_id=admitted.alert.alert_id,
                case_id=None,
                source_system="reviewed-source",
                collector_identity="control-plane-test",
                acquired_at=compared_at,
                derivation_relationship="admitted_analytic_signal",
                lifecycle_state="collected",
            )
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-assistant-cli-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=admitted.alert.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome="follow reviewed evidence",
                lifecycle_state="under_review",
                reviewed_context=reviewed_context,
            )
        )

        stdout = io.StringIO()
        main.main(
            [
                "inspect-assistant-context",
                "--family",
                "case",
                "--record-id",
                promoted_case.case_id,
            ],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["read_only"])
        self.assertEqual(payload["record_family"], "case")
        self.assertEqual(payload["record_id"], promoted_case.case_id)
        self.assertEqual(payload["record"]["case_id"], promoted_case.case_id)
        self.assertEqual(payload["advisory_output"]["output_kind"], "case_summary")
        self.assertEqual(payload["advisory_output"]["status"], "ready")
        self.assertIn(evidence.evidence_id, payload["advisory_output"]["citations"])
        self.assertEqual(payload["reviewed_context"], reviewed_context)
        self.assertEqual(payload["linked_evidence_ids"], [evidence.evidence_id])
        self.assertEqual(
            payload["linked_evidence_records"][0]["evidence_id"],
            evidence.evidence_id,
        )
        self.assertIn(admitted.alert.alert_id, payload["linked_alert_ids"])
        self.assertIn(
            recommendation.recommendation_id,
            payload["linked_recommendation_ids"],
        )
        self.assertIn(
            admitted.reconciliation.reconciliation_id,
            payload["linked_reconciliation_ids"],
        )

    def test_cli_renders_cited_advisory_output_view_for_a_case(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        compared_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        reviewed_context = {
            "asset": {
                "asset_id": "asset-repo-advisory-cli-001",
                "criticality": "high",
            },
            "identity": {
                "identity_id": "principal-advisory-cli-001",
            },
        }
        admitted = service.ingest_finding_alert(
            finding_id="finding-advisory-cli-001",
            analytic_signal_id="signal-advisory-cli-001",
            substrate_detection_record_id="substrate-detection-advisory-cli-001",
            correlation_key="claim:asset-repo-advisory-cli-001:assistant-advisory-cli",
            first_seen_at=compared_at,
            last_seen_at=compared_at,
            reviewed_context=reviewed_context,
        )
        evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-advisory-cli-001",
                source_record_id="substrate-detection-advisory-cli-001",
                alert_id=admitted.alert.alert_id,
                case_id=None,
                source_system="reviewed-source",
                collector_identity="control-plane-test",
                acquired_at=compared_at,
                derivation_relationship="admitted_analytic_signal",
                lifecycle_state="collected",
            )
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-advisory-cli-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=admitted.alert.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome="review the cited evidence before any approval",
                lifecycle_state="under_review",
                reviewed_context=reviewed_context,
            )
        )

        stdout = io.StringIO()
        main.main(
            [
                "inspect-advisory-output",
                "--family",
                "case",
                "--record-id",
                promoted_case.case_id,
            ],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["read_only"])
        self.assertEqual(payload["record_family"], "case")
        self.assertEqual(payload["record_id"], promoted_case.case_id)
        self.assertEqual(payload["output_kind"], "case_summary")
        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["reviewed_context"], reviewed_context)
        self.assertIn(evidence.evidence_id, payload["citations"])
        self.assertIn("advisory_only", payload["uncertainty_flags"])
        self.assertEqual(payload["linked_evidence_ids"], [evidence.evidence_id])
        self.assertIn(admitted.alert.alert_id, payload["linked_alert_ids"])
        self.assertIn(recommendation.recommendation_id, payload["linked_recommendation_ids"])
        self.assertIn(
            admitted.reconciliation.reconciliation_id,
            payload["linked_reconciliation_ids"],
        )

    def test_cli_renders_case_detail_with_evidence_provenance_and_cited_advisory_output(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        compared_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        reviewed_context = {
            "asset": {
                "asset_id": "asset-repo-case-detail-cli-001",
                "criticality": "high",
            },
            "identity": {
                "identity_id": "principal-case-detail-cli-001",
            },
        }
        admitted = service.ingest_finding_alert(
            finding_id="finding-case-detail-cli-001",
            analytic_signal_id="signal-case-detail-cli-001",
            substrate_detection_record_id="substrate-detection-case-detail-cli-001",
            correlation_key="claim:asset-repo-case-detail-cli-001:case-detail-cli",
            first_seen_at=compared_at,
            last_seen_at=compared_at,
            reviewed_context=reviewed_context,
        )
        evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-case-detail-cli-001",
                source_record_id="substrate-detection-case-detail-cli-001",
                alert_id=admitted.alert.alert_id,
                case_id=None,
                source_system="reviewed-source",
                collector_identity="collector://wazuh/live",
                acquired_at=compared_at,
                derivation_relationship="admitted_analytic_signal",
                lifecycle_state="collected",
            )
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=compared_at,
            scope_statement="Observed permission change remains within reviewed GitHub audit scope.",
            supporting_evidence_ids=(evidence.evidence_id,),
        )
        lead = service.record_case_lead(
            case_id=promoted_case.case_id,
            observation_id=observation.observation_id,
            triage_owner="analyst-001",
            triage_rationale="Preserve durable case context for next business-hours analyst.",
        )
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-case-detail-cli-001",
                lead_id=lead.lead_id,
                hunt_run_id=None,
                alert_id=admitted.alert.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome="review the cited evidence before any approval",
                lifecycle_state="under_review",
                reviewed_context=reviewed_context,
            )
        )
        service.record_case_handoff(
            case_id=promoted_case.case_id,
            handoff_at=compared_at,
            handoff_owner="analyst-001",
            handoff_note="Resume owner-membership review during the next business-hours cycle.",
            follow_up_evidence_ids=(evidence.evidence_id,),
        )
        service.record_case_disposition(
            case_id=promoted_case.case_id,
            disposition="business_hours_handoff",
            rationale="Tracked case remains open for the next analyst review window.",
            recorded_at=compared_at,
        )

        stdout = io.StringIO()
        main.main(
            [
                "inspect-case-detail",
                "--case-id",
                promoted_case.case_id,
            ],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["read_only"])
        self.assertEqual(payload["case_id"], promoted_case.case_id)
        self.assertEqual(payload["case_record"]["case_id"], promoted_case.case_id)
        self.assertEqual(payload["reviewed_context"]["asset"], reviewed_context["asset"])
        self.assertEqual(
            payload["reviewed_context"]["identity"],
            reviewed_context["identity"],
        )
        self.assertEqual(
            payload["advisory_output"]["output_kind"],
            "case_summary",
        )
        self.assertEqual(payload["advisory_output"]["status"], "ready")
        self.assertEqual(payload["linked_evidence_ids"], [evidence.evidence_id])
        self.assertEqual(
            payload["linked_evidence_records"][0]["collector_identity"],
            "collector://wazuh/live",
        )
        self.assertEqual(
            payload["linked_evidence_records"][0]["derivation_relationship"],
            "admitted_analytic_signal",
        )
        self.assertEqual(payload["linked_observation_ids"], [observation.observation_id])
        self.assertEqual(payload["linked_lead_ids"], [lead.lead_id])
        self.assertEqual(
            payload["case_record"]["reviewed_context"]["triage"]["disposition"],
            "business_hours_handoff",
        )
        self.assertEqual(
            payload["case_record"]["reviewed_context"]["handoff"]["handoff_owner"],
            "analyst-001",
        )
        self.assertIn(
            recommendation.recommendation_id,
            payload["linked_recommendation_ids"],
        )
        self.assertIn(
            admitted.reconciliation.reconciliation_id,
            payload["linked_reconciliation_ids"],
        )

    def test_cli_renders_recommendation_draft_view_for_a_case(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        compared_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        reviewed_context = {
            "asset": {
                "asset_id": "asset-repo-draft-cli-001",
                "criticality": "high",
            },
            "identity": {
                "identity_id": "principal-draft-cli-001",
            },
        }
        admitted = service.ingest_finding_alert(
            finding_id="finding-draft-cli-001",
            analytic_signal_id="signal-draft-cli-001",
            substrate_detection_record_id="substrate-detection-draft-cli-001",
            correlation_key="claim:asset-repo-draft-cli-001:assistant-draft-cli",
            first_seen_at=compared_at,
            last_seen_at=compared_at,
            reviewed_context=reviewed_context,
        )
        evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-draft-cli-001",
                source_record_id="substrate-detection-draft-cli-001",
                alert_id=admitted.alert.alert_id,
                case_id=None,
                source_system="reviewed-source",
                collector_identity="control-plane-test",
                acquired_at=compared_at,
                derivation_relationship="admitted_analytic_signal",
                lifecycle_state="collected",
            )
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-draft-cli-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=admitted.alert.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome="review the cited evidence before escalation",
                lifecycle_state="under_review",
                reviewed_context=reviewed_context,
            )
        )

        stdout = io.StringIO()
        main.main(
            [
                "render-recommendation-draft",
                "--family",
                "case",
                "--record-id",
                promoted_case.case_id,
            ],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["read_only"])
        self.assertEqual(payload["record_family"], "case")
        self.assertEqual(payload["record_id"], promoted_case.case_id)
        self.assertEqual(payload["reviewed_context"], reviewed_context)
        self.assertEqual(
            payload["recommendation_draft"]["source_output_kind"],
            "case_summary",
        )
        self.assertEqual(payload["recommendation_draft"]["status"], "ready")
        self.assertTrue(payload["recommendation_draft"]["candidate_recommendations"])
        self.assertIn(
            evidence.evidence_id,
            payload["recommendation_draft"]["citations"],
        )
        self.assertIn(
            "advisory_only",
            payload["recommendation_draft"]["uncertainty_flags"],
        )
        self.assertEqual(payload["linked_evidence_ids"], [evidence.evidence_id])
        self.assertIn(admitted.alert.alert_id, payload["linked_alert_ids"])
        self.assertIn(recommendation.recommendation_id, payload["linked_recommendation_ids"])
        self.assertIn(
            admitted.reconciliation.reconciliation_id,
            payload["linked_reconciliation_ids"],
        )

    def test_cli_renders_recommendation_draft_with_source_review_outcome(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        compared_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        reviewed_context = {
            "asset": {
                "asset_id": "asset-repo-draft-cli-outcome-001",
                "criticality": "high",
            },
            "identity": {
                "identity_id": "principal-repo-draft-cli-outcome-001",
                "criticality": "elevated",
            },
        }

        admitted = service.ingest_finding_alert(
            finding_id="finding-draft-cli-outcome-001",
            analytic_signal_id="signal-draft-cli-outcome-001",
            substrate_detection_record_id="substrate-detection-draft-cli-outcome-001",
            correlation_key="claim:asset-repo-draft-cli-outcome-001:assistant-draft-cli",
            first_seen_at=compared_at,
            last_seen_at=compared_at,
            reviewed_context=reviewed_context,
        )
        evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-draft-cli-outcome-001",
                source_record_id="substrate-detection-draft-cli-outcome-001",
                alert_id=admitted.alert.alert_id,
                case_id=None,
                source_system="reviewed-source",
                collector_identity="control-plane-test",
                acquired_at=compared_at,
                derivation_relationship="admitted_analytic_signal",
                lifecycle_state="collected",
            )
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-draft-cli-outcome-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=admitted.alert.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome="review the cited evidence before escalation",
                lifecycle_state="accepted",
                reviewed_context=reviewed_context,
            )
        )

        stdout = io.StringIO()
        main.main(
            [
                "render-recommendation-draft",
                "--family",
                "recommendation",
                "--record-id",
                recommendation.recommendation_id,
            ],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["record_family"], "recommendation")
        self.assertEqual(payload["record_id"], recommendation.recommendation_id)
        self.assertEqual(
            payload["recommendation_draft"]["source_output_kind"],
            "recommendation_draft",
        )
        self.assertEqual(
            payload["recommendation_draft"]["review_lifecycle_state"],
            "accepted",
        )
        self.assertIn(
            "has been accepted and is anchored",
            payload["recommendation_draft"]["cited_summary"]["text"],
        )
        self.assertNotIn(
            "remains under review",
            payload["recommendation_draft"]["cited_summary"]["text"],
        )
        self.assertIn(
            evidence.evidence_id,
            payload["recommendation_draft"]["citations"],
        )

    def test_cli_renders_identity_rich_analyst_queue_view_with_reviewed_context(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        adapter = WazuhAlertAdapter()
        admitted = service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(
                _load_wazuh_fixture("microsoft-365-audit-alert.json")
            ),
        )
        service.promote_alert_to_case(admitted.alert.alert_id)

        stdout = io.StringIO()
        main.main(["inspect-analyst-queue"], stdout=stdout, service=service)

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["total_records"], 1)
        self.assertEqual(
            payload["records"][0]["reviewed_context"]["source"]["source_family"],
            "microsoft_365_audit",
        )
        self.assertEqual(
            payload["records"][0]["reviewed_context"]["identity"]["actor"]["identity_id"],
            "alex@contoso.com",
        )

    def test_cli_rejects_unknown_record_family_as_usage_error(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as exc_info:
                main.main(
                    ["inspect-records", "--family", "unknown-family"],
                    service=service,
                )

        self.assertEqual(exc_info.exception.code, 2)
        self.assertIn("Unsupported control-plane record family", stderr.getvalue())

    def test_cli_rejects_blank_alert_detail_identifier_as_usage_error(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as exc_info:
                main.main(
                    ["inspect-alert-detail", "--alert-id", "   "],
                    service=service,
                )

        self.assertEqual(exc_info.exception.code, 2)
        self.assertIn("alert_id must be a non-empty string", stderr.getvalue())

    def test_cli_renders_inspection_views_against_empty_postgresql_store(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        records_stdout = io.StringIO()
        status_stdout = io.StringIO()

        main.main(
            ["inspect-records", "--family", "alert"],
            stdout=records_stdout,
            service=service,
        )
        main.main(
            ["inspect-reconciliation-status"],
            stdout=status_stdout,
            service=service,
        )

        records_payload = json.loads(records_stdout.getvalue())
        status_payload = json.loads(status_stdout.getvalue())

        self.assertTrue(records_payload["read_only"])
        self.assertEqual(records_payload["record_family"], "alert")
        self.assertEqual(records_payload["total_records"], 0)
        self.assertEqual(records_payload["records"], [])

        self.assertTrue(status_payload["read_only"])
        self.assertEqual(status_payload["total_records"], 0)
        self.assertIsNone(status_payload["latest_compared_at"])
        self.assertEqual(status_payload["by_lifecycle_state"], {})
        self.assertEqual(status_payload["by_ingest_disposition"], {})
        self.assertEqual(status_payload["records"], [])


if __name__ == "__main__":
    unittest.main()
