from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase17FirstBootRuntimeArtifactTests(unittest.TestCase):
    def test_reviewed_runtime_image_artifact_exists(self) -> None:
        dockerfile = (
            REPO_ROOT / "control-plane" / "deployment" / "first-boot" / "Dockerfile"
        )

        self.assertTrue(dockerfile.exists(), f"expected first-boot runtime image at {dockerfile}")

        text = dockerfile.read_text(encoding="utf-8")
        for term in (
            "FROM python:",
            "postgresql-client",
            "psycopg[binary]",
            "COPY control-plane /opt/aegisops/control-plane",
            "COPY postgres/control-plane/migrations /opt/aegisops/postgres-migrations",
            "COPY control-plane/deployment/first-boot/control-plane-entrypoint.sh /opt/aegisops/bin/first-boot-entrypoint.sh",
            'ENTRYPOINT ["/opt/aegisops/bin/first-boot-entrypoint.sh"]',
            'CMD ["python3", "main.py", "serve"]',
        ):
            self.assertIn(term, text)

    def test_first_boot_compose_uses_reviewed_image_path_instead_of_repo_local_runtime_mounts(
        self,
    ) -> None:
        compose_path = (
            REPO_ROOT / "control-plane" / "deployment" / "first-boot" / "docker-compose.yml"
        )
        self.assertTrue(compose_path.exists(), f"expected first-boot compose at {compose_path}")

        text = compose_path.read_text(encoding="utf-8")
        for term in (
            "build:",
            "dockerfile: control-plane/deployment/first-boot/Dockerfile",
            "image: aegisops-control-plane:first-boot",
            "AEGISOPS_CONTROL_PLANE_BOOT_MODE: ${AEGISOPS_CONTROL_PLANE_BOOT_MODE:-first-boot}",
            "AEGISOPS_CONTROL_PLANE_LOG_LEVEL: ${AEGISOPS_CONTROL_PLANE_LOG_LEVEL:-INFO}",
        ):
            self.assertIn(term, text)

        for forbidden in (
            "image: alpine:3.22.1",
            "working_dir: /workspace/control-plane",
            "../../../:/workspace:ro",
            "./control-plane-entrypoint.sh:/opt/aegisops/bin/first-boot-entrypoint.sh:ro",
            "../../../postgres/control-plane/migrations:/opt/aegisops/postgres-migrations:ro",
        ):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
