from __future__ import annotations

import pathlib
import sys
import unittest


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from aegisops_control_plane.service import build_runtime_snapshot


class RuntimeSkeletonTests(unittest.TestCase):
    def test_runtime_snapshot_uses_non_secret_local_defaults(self) -> None:
        snapshot = build_runtime_snapshot({})

        self.assertEqual(snapshot.bind_host, "127.0.0.1")
        self.assertEqual(snapshot.bind_port, 8080)
        self.assertEqual(snapshot.postgres_dsn, "<set-me>")
        self.assertEqual(snapshot.opensearch_url, "<set-me>")
        self.assertEqual(snapshot.n8n_base_url, "<set-me>")

    def test_runtime_snapshot_preserves_boundary_split(self) -> None:
        snapshot = build_runtime_snapshot(
            {
                "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN": "postgresql://control-plane.local",
                "AEGISOPS_CONTROL_PLANE_OPENSEARCH_URL": "https://opensearch.internal",
                "AEGISOPS_CONTROL_PLANE_N8N_BASE_URL": "https://n8n.internal",
            }
        )

        self.assertEqual(snapshot.service_name, "aegisops-control-plane")
        self.assertEqual(snapshot.ownership_boundary["runtime_root"], "control-plane/")
        self.assertEqual(snapshot.ownership_boundary["postgres_contract_root"], "postgres/control-plane/")
        self.assertEqual(snapshot.ownership_boundary["signal_source"], "opensearch/")
        self.assertEqual(snapshot.ownership_boundary["execution_plane"], "n8n/")


if __name__ == "__main__":
    unittest.main()
