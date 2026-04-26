from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler
from unittest import mock
from urllib import error, request


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from aegisops_control_plane import AlertRecord, ControlPlaneRecord
from aegisops_control_plane.config import RuntimeConfig
from aegisops_control_plane.service import (
    AegisOpsControlPlaneService,
    build_runtime_snapshot,
)


class RuntimeSkeletonTests(unittest.TestCase):
    def test_package_root_exports_control_plane_record_models(self) -> None:
        self.assertTrue(issubclass(AlertRecord, ControlPlaneRecord))

    def test_runtime_snapshot_uses_non_secret_local_defaults(self) -> None:
        snapshot = build_runtime_snapshot({})

        self.assertEqual(snapshot.bind_host, "127.0.0.1")
        self.assertEqual(snapshot.bind_port, 8080)
        self.assertEqual(snapshot.postgres_dsn, "<set-me>")
        self.assertEqual(snapshot.persistence_mode, "postgresql")
        self.assertEqual(snapshot.opensearch_url, "<set-me>")
        self.assertEqual(snapshot.n8n_base_url, "<set-me>")
        self.assertEqual(snapshot.shuffle_base_url, "<set-me>")
        self.assertEqual(snapshot.isolated_executor_base_url, "<set-me>")

    def test_runtime_snapshot_uses_default_port_when_env_is_empty(self) -> None:
        snapshot = build_runtime_snapshot({"AEGISOPS_CONTROL_PLANE_PORT": ""})

        self.assertEqual(snapshot.bind_port, 8080)

    def test_runtime_snapshot_preserves_boundary_split(self) -> None:
        snapshot = build_runtime_snapshot(
            {
                "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN": "postgresql://control-plane.local",
                "AEGISOPS_CONTROL_PLANE_OPENSEARCH_URL": "https://opensearch.internal",
                "AEGISOPS_CONTROL_PLANE_N8N_BASE_URL": "https://n8n.internal",
                "AEGISOPS_CONTROL_PLANE_SHUFFLE_BASE_URL": "https://shuffle.internal",
                "AEGISOPS_CONTROL_PLANE_ISOLATED_EXECUTOR_BASE_URL": "https://executor.internal",
            }
        )

        self.assertEqual(snapshot.service_name, "aegisops-control-plane")
        self.assertEqual(snapshot.ownership_boundary["runtime_root"], "control-plane/")
        self.assertEqual(snapshot.ownership_boundary["postgres_contract_root"], "postgres/control-plane/")
        self.assertEqual(
            snapshot.ownership_boundary["native_detection_intake"],
            "substrate-adapters/",
        )
        self.assertEqual(
            snapshot.ownership_boundary["admitted_signal_model"],
            "control-plane/analytic-signals",
        )
        self.assertEqual(
            snapshot.ownership_boundary["routine_automation_substrate"],
            "shuffle/",
        )
        self.assertEqual(
            snapshot.ownership_boundary["controlled_execution_surface"],
            "executor/isolated-executor",
        )

    def test_runtime_snapshot_rejects_non_integer_port(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            r"AEGISOPS_CONTROL_PLANE_PORT must be an integer, got: 'invalid'",
        ):
            build_runtime_snapshot({"AEGISOPS_CONTROL_PLANE_PORT": "invalid"})

    def test_runtime_snapshot_rejects_out_of_range_port(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            r"AEGISOPS_CONTROL_PLANE_PORT must be between 1 and 65535, got: 70000",
        ):
            build_runtime_snapshot({"AEGISOPS_CONTROL_PLANE_PORT": "70000"})

    def test_runtime_config_repr_hides_wazuh_shared_secret(self) -> None:
        config = RuntimeConfig(
            postgres_dsn="postgresql://control-plane.local/aegisops",
            wazuh_ingest_shared_secret="reviewed-shared-secret",
            wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",
        )

        self.assertNotIn("reviewed-shared-secret", repr(config))
        self.assertNotIn("reviewed-proxy-secret", repr(config))

    def test_runtime_config_parses_reverse_proxy_secret_from_env(self) -> None:
        config = RuntimeConfig.from_env(
            {
                "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET": (
                    "reviewed-proxy-secret"
                ),
            }
        )

        self.assertEqual(
            config.wazuh_ingest_reverse_proxy_secret,
            "reviewed-proxy-secret",
        )

    def test_runtime_config_parses_trusted_proxy_cidrs_from_env(self) -> None:
        config = RuntimeConfig.from_env(
            {
                "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_TRUSTED_PROXY_CIDRS": (
                    "10.10.0.5/32, 10.10.0.0/24 ,,2001:db8::/32"
                ),
            }
        )

        self.assertEqual(
            config.wazuh_ingest_trusted_proxy_cidrs,
            ("10.10.0.5/32", "10.10.0.0/24", "2001:db8::/32"),
        )

    def test_runtime_config_loads_postgres_and_secret_values_from_explicit_secret_files(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            secret_dir = pathlib.Path(temp_dir)
            postgres_dsn_path = secret_dir / "postgres_dsn"
            shared_secret_path = secret_dir / "wazuh_shared_secret"
            proxy_secret_path = secret_dir / "wazuh_proxy_secret"
            postgres_dsn_path.write_text(
                "postgresql://control-plane:reviewed-password@postgres:5432/aegisops\n",
                encoding="utf-8",
            )
            shared_secret_path.write_text("reviewed-shared-secret\n", encoding="utf-8")
            proxy_secret_path.write_text("reviewed-proxy-secret\n", encoding="utf-8")

            config = RuntimeConfig.from_env(
                {
                    "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_FILE": str(postgres_dsn_path),
                    "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_FILE": str(
                        shared_secret_path
                    ),
                    "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET_FILE": str(
                        proxy_secret_path
                    ),
                }
            )

        self.assertEqual(
            config.postgres_dsn,
            "postgresql://control-plane:reviewed-password@postgres:5432/aegisops",
        )
        self.assertEqual(config.wazuh_ingest_shared_secret, "reviewed-shared-secret")
        self.assertEqual(config.wazuh_ingest_reverse_proxy_secret, "reviewed-proxy-secret")

    def test_runtime_config_rejects_missing_secret_file_binding(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_FILE must point to a readable file",
        ):
            RuntimeConfig.from_env(
                {
                    "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_FILE": (
                        "/tmp/does-not-exist-aegisops"
                    ),
                }
            )

    def test_cli_module_owns_parser_and_command_dispatch(self) -> None:
        from aegisops_control_plane import cli

        parser = cli.build_parser()
        parsed = parser.parse_args(["runtime"])
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops")
        )

        payload = cli.run_command(parsed, service=service)

        self.assertEqual(payload["service_name"], "aegisops-control-plane")
        self.assertEqual(payload["persistence_mode"], "postgresql")

    def test_http_surface_module_owns_request_handler_construction(self) -> None:
        from aegisops_control_plane import http_surface

        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops")
        )

        handler_class = http_surface.build_handler_class(
            service=service,
            runtime_snapshot=service.describe_runtime().to_dict(),
            stderr=sys.stderr,
        )

        self.assertTrue(issubclass(handler_class, BaseHTTPRequestHandler))

    def test_readyz_uses_current_readiness_diagnostics_status(self) -> None:
        from http.server import ThreadingHTTPServer

        from aegisops_control_plane import http_surface

        readiness_snapshot = mock.Mock()
        readiness_snapshot.to_dict.return_value = {
            "read_only": True,
            "booted": True,
            "status": "degraded",
            "startup": {"startup_ready": True},
            "shutdown": {"shutdown_ready": False},
            "metrics": {
                "review_path_health": {"overall_state": "degraded"},
                "optional_extensions": {"overall_state": "degraded"},
            },
            "latest_reconciliation": None,
        }
        service = mock.Mock()
        service.inspect_readiness_diagnostics.return_value = readiness_snapshot

        handler_class = http_surface.build_handler_class(
            service=service,
            runtime_snapshot={
                "service_name": "aegisops-control-plane",
                "persistence_mode": "postgresql",
            },
            stderr=sys.stderr,
        )
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler_class)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with self.assertRaises(error.HTTPError) as raised:
                request.urlopen(  # noqa: S310 - local in-process test HTTP server
                    f"http://127.0.0.1:{server.server_port}/readyz",
                    timeout=2,
                )
            payload = json.loads(raised.exception.read().decode("utf-8"))
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

        self.assertEqual(raised.exception.code, 503)
        self.assertEqual(payload["status"], "degraded")
        self.assertEqual(payload["readiness_source"], "current_dependency_status")
        service.inspect_readiness_diagnostics.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
