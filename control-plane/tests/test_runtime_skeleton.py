from __future__ import annotations

import pathlib
import sys
import tempfile
import unittest


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from aegisops_control_plane import AlertRecord, ControlPlaneRecord
from aegisops_control_plane.config import RuntimeConfig
from aegisops_control_plane.service import build_runtime_snapshot


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


if __name__ == "__main__":
    unittest.main()
