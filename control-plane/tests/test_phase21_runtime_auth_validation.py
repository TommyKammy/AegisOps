from __future__ import annotations

from datetime import datetime, timedelta, timezone
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
from aegisops_control_plane.service import AegisOpsControlPlaneService
from postgres_test_support import make_store


REVIEWED_SHARED_SECRET = "reviewed-shared-secret"  # noqa: S105
REVIEWED_WAZUH_PROXY_SECRET = "reviewed-wazuh-proxy-secret"  # noqa: S105
REVIEWED_SURFACE_PROXY_SECRET = "reviewed-surface-proxy-secret"  # noqa: S105
REVIEWED_PROXY_SERVICE_ACCOUNT = "svc-aegisops-proxy-control-plane"  # noqa: S105
REVIEWED_ADMIN_BOOTSTRAP_TOKEN = "reviewed-admin-bootstrap-token"  # noqa: S105
REVIEWED_BREAK_GLASS_TOKEN = "reviewed-break-glass-token"  # noqa: S105


def _build_service(*, host: str = "127.0.0.1") -> AegisOpsControlPlaneService:
    store, _ = make_store()
    return AegisOpsControlPlaneService(
        RuntimeConfig(
            host=host,
            port=0,
            postgres_dsn="postgresql://control-plane.local/aegisops",
            wazuh_ingest_shared_secret=REVIEWED_SHARED_SECRET,
            wazuh_ingest_reverse_proxy_secret=REVIEWED_WAZUH_PROXY_SECRET,
            wazuh_ingest_trusted_proxy_cidrs=("10.10.0.5/32",),
            protected_surface_reverse_proxy_secret=REVIEWED_SURFACE_PROXY_SECRET,
            protected_surface_trusted_proxy_cidrs=("10.10.0.5/32",),
            protected_surface_proxy_service_account=REVIEWED_PROXY_SERVICE_ACCOUNT,
            admin_bootstrap_token=REVIEWED_ADMIN_BOOTSTRAP_TOKEN,
            break_glass_token=REVIEWED_BREAK_GLASS_TOKEN,
        ),
        store=store,
    )


class Phase21RuntimeAuthValidationTests(unittest.TestCase):
    def test_protected_surface_runtime_fails_closed_without_trusted_proxy_bindings(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="0.0.0.0",
                port=8080,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret=REVIEWED_SHARED_SECRET,
                wazuh_ingest_reverse_proxy_secret=REVIEWED_WAZUH_PROXY_SECRET,
            ),
            store=store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_TRUSTED_PROXY_CIDRS must be set",
        ):
            service.validate_protected_surface_runtime()

    def test_protected_surface_request_rejects_missing_authenticated_identity_header(
        self,
    ) -> None:
        service = _build_service(host="0.0.0.0")

        with self.assertRaisesRegex(
            PermissionError,
            "protected control-plane surfaces require an attributed authenticated identity header",
        ):
            service.authenticate_protected_surface_request(
                peer_addr="10.10.0.5",
                forwarded_proto="https",
                reverse_proxy_secret_header=REVIEWED_SURFACE_PROXY_SECRET,
                proxy_service_account_header=REVIEWED_PROXY_SERVICE_ACCOUNT,
                authenticated_identity_header=None,
                authenticated_role_header="analyst",
                allowed_roles=("analyst", "approver", "platform_admin"),
            )

    def test_protected_surface_request_accepts_reviewed_reverse_proxy_identity_headers(
        self,
    ) -> None:
        service = _build_service(host="0.0.0.0")

        principal = service.authenticate_protected_surface_request(
            peer_addr="10.10.0.5",
            forwarded_proto="https",
            reverse_proxy_secret_header=REVIEWED_SURFACE_PROXY_SECRET,
            proxy_service_account_header=REVIEWED_PROXY_SERVICE_ACCOUNT,
            authenticated_identity_header="analyst-001",
            authenticated_role_header="analyst",
            allowed_roles=("analyst", "approver", "platform_admin"),
        )

        self.assertEqual(principal.identity, "analyst-001")
        self.assertEqual(principal.role, "analyst")
        self.assertEqual(principal.access_path, "reviewed_reverse_proxy")
        self.assertEqual(
            principal.proxy_service_account,
            REVIEWED_PROXY_SERVICE_ACCOUNT,
        )

    def test_admin_bootstrap_contract_rejects_wrong_token(self) -> None:
        service = _build_service()
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

                bootstrap_request = request.Request(  # noqa: S310
                    f"http://127.0.0.1:{servers[0].server_port}/admin/bootstrap/claim",
                    data=json.dumps(
                        {
                            "admin_identity": "platform-admin-001",
                            "bootstrap_token": "wrong-token",
                            "bootstrap_reason": "Initial reviewed admin setup",
                            "service_account_name": "svc-aegisops-admin-bootstrap",
                        }
                    ).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )

                with self.assertRaisesRegex(error.HTTPError, "403"):
                    request.urlopen(bootstrap_request, timeout=2)  # noqa: S310
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_break_glass_contract_rejects_expiry_outside_reviewed_window(self) -> None:
        service = _build_service()
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

                break_glass_request = request.Request(  # noqa: S310
                    f"http://127.0.0.1:{servers[0].server_port}/admin/break-glass/activate",
                    data=json.dumps(
                        {
                            "admin_identity": "platform-admin-001",
                            "break_glass_token": REVIEWED_BREAK_GLASS_TOKEN,
                            "reason": "Reviewed recovery test",
                            "ticket_id": "CHG-435",
                            "expires_at": (
                                datetime.now(timezone.utc) + timedelta(minutes=61)
                            ).isoformat(),
                        }
                    ).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )

                with self.assertRaises(error.HTTPError) as exc_info:
                    request.urlopen(break_glass_request, timeout=2)  # noqa: S310

                self.assertEqual(exc_info.exception.code, 400)
                error_payload = json.loads(exc_info.exception.read().decode("utf-8"))
                self.assertEqual(error_payload["error"], "invalid_request")
                self.assertEqual(
                    error_payload["message"],
                    "break-glass expiry must be within the reviewed 60 minute window",
                )
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
