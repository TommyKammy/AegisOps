from __future__ import annotations

import pathlib
import sys
import tempfile
import unittest


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from aegisops_control_plane.config import RuntimeConfig


class _MutableOpenBaoTransport:
    def __init__(self, secrets: dict[str, str] | None = None, *, error: Exception | None = None) -> None:
        self._secrets = secrets or {}
        self._error = error

    def read_secret(
        self,
        *,
        address: str,
        token: str,
        mount: str,
        secret_path: str,
    ) -> str:
        del address
        del token
        del mount
        if self._error is not None:
            raise self._error
        return self._secrets[secret_path]


class RuntimeSecretBoundaryTests(unittest.TestCase):
    def test_runtime_config_loads_secret_from_openbao_reference(self) -> None:
        transport = _MutableOpenBaoTransport(
            {
                "kv/aegisops/control-plane/postgres-dsn": "postgresql://reviewed-user:reviewed-pass@postgres:5432/aegisops",
                "kv/aegisops/control-plane/wazuh-ingest-shared-secret": "reviewed-shared-secret",
            }
        )

        config = RuntimeConfig.from_env(
            {
                "AEGISOPS_OPENBAO_ADDRESS": "https://openbao.example.test",
                "AEGISOPS_OPENBAO_TOKEN": "reviewed-openbao-token",
                "AEGISOPS_OPENBAO_KV_MOUNT": "secret",
                "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_OPENBAO_PATH": (
                    "kv/aegisops/control-plane/postgres-dsn"
                ),
                "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_OPENBAO_PATH": (
                    "kv/aegisops/control-plane/wazuh-ingest-shared-secret"
                ),
            },
            secret_backend_transport=transport,
        )

        self.assertEqual(
            config.postgres_dsn,
            "postgresql://reviewed-user:reviewed-pass@postgres:5432/aegisops",
        )
        self.assertEqual(
            config.wazuh_ingest_shared_secret,
            "reviewed-shared-secret",
        )

    def test_runtime_config_rejects_openbao_reference_without_backend_transport(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_OPENBAO_PATH requires an OpenBao transport",
        ):
            RuntimeConfig.from_env(
                {
                    "AEGISOPS_OPENBAO_ADDRESS": "https://openbao.example.test",
                    "AEGISOPS_OPENBAO_TOKEN": "reviewed-openbao-token",
                    "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_OPENBAO_PATH": (
                        "kv/aegisops/control-plane/postgres-dsn"
                    ),
                }
            )

    def test_runtime_config_fails_closed_when_openbao_backend_is_unavailable(self) -> None:
        transport = _MutableOpenBaoTransport(error=RuntimeError("backend unavailable"))

        with self.assertRaisesRegex(
            ValueError,
            "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_OPENBAO_PATH could not be read from OpenBao",
        ):
            RuntimeConfig.from_env(
                {
                    "AEGISOPS_OPENBAO_ADDRESS": "https://openbao.example.test",
                    "AEGISOPS_OPENBAO_TOKEN": "reviewed-openbao-token",
                    "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_OPENBAO_PATH": (
                        "kv/aegisops/control-plane/postgres-dsn"
                    ),
                },
                secret_backend_transport=transport,
            )

    def test_runtime_config_fails_closed_when_openbao_secret_is_empty(self) -> None:
        transport = _MutableOpenBaoTransport(
            {
                "kv/aegisops/control-plane/postgres-dsn": "",
            }
        )

        with self.assertRaisesRegex(
            ValueError,
            "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_OPENBAO_PATH must not resolve to an empty value",
        ):
            RuntimeConfig.from_env(
                {
                    "AEGISOPS_OPENBAO_ADDRESS": "https://openbao.example.test",
                    "AEGISOPS_OPENBAO_TOKEN": "reviewed-openbao-token",
                    "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_OPENBAO_PATH": (
                        "kv/aegisops/control-plane/postgres-dsn"
                    ),
                },
                secret_backend_transport=transport,
            )

    def test_runtime_config_reloads_rotated_openbao_secret_on_fresh_load(self) -> None:
        transport = _MutableOpenBaoTransport(
            {
                "kv/aegisops/control-plane/wazuh-ingest-shared-secret": "reviewed-shared-secret-v1",
            }
        )

        initial = RuntimeConfig.from_env(
            {
                "AEGISOPS_OPENBAO_ADDRESS": "https://openbao.example.test",
                "AEGISOPS_OPENBAO_TOKEN": "reviewed-openbao-token",
                "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_OPENBAO_PATH": (
                    "kv/aegisops/control-plane/wazuh-ingest-shared-secret"
                ),
            },
            secret_backend_transport=transport,
        )

        transport._secrets["kv/aegisops/control-plane/wazuh-ingest-shared-secret"] = (
            "reviewed-shared-secret-v2"
        )

        rotated = RuntimeConfig.from_env(
            {
                "AEGISOPS_OPENBAO_ADDRESS": "https://openbao.example.test",
                "AEGISOPS_OPENBAO_TOKEN": "reviewed-openbao-token",
                "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_OPENBAO_PATH": (
                    "kv/aegisops/control-plane/wazuh-ingest-shared-secret"
                ),
            },
            secret_backend_transport=transport,
        )

        self.assertEqual(initial.wazuh_ingest_shared_secret, "reviewed-shared-secret-v1")
        self.assertEqual(rotated.wazuh_ingest_shared_secret, "reviewed-shared-secret-v2")

    def test_runtime_config_keeps_file_binding_available_for_local_secret_mounts(self) -> None:
        with tempfile.NamedTemporaryFile("w+", encoding="utf-8") as handle:
            handle.write("reviewed-admin-bootstrap-token\n")
            handle.flush()

            config = RuntimeConfig.from_env(
                {
                    "AEGISOPS_CONTROL_PLANE_ADMIN_BOOTSTRAP_TOKEN_FILE": handle.name,
                }
            )

        self.assertEqual(
            config.admin_bootstrap_token,
            "reviewed-admin-bootstrap-token",
        )


if __name__ == "__main__":
    unittest.main()
