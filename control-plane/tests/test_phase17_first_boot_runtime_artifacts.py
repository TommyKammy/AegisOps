from __future__ import annotations

import pathlib
import re
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
APPROVED_FIRST_BOOT_BASE_IMAGE = "python:3.12-slim-bookworm"


class Phase17FirstBootRuntimeArtifactTests(unittest.TestCase):
    def test_reviewed_runtime_image_artifact_exists(self) -> None:
        dockerfile = (
            REPO_ROOT / "control-plane" / "deployment" / "first-boot" / "Dockerfile"
        )

        self.assertTrue(dockerfile.exists(), f"expected first-boot runtime image at {dockerfile}")

        text = dockerfile.read_text(encoding="utf-8")
        for term in (
            f"FROM {APPROVED_FIRST_BOOT_BASE_IMAGE}",
            "postgresql-client",
            "psycopg[binary]",
            "COPY --chown=aegisops:aegisops control-plane /opt/aegisops/control-plane",
            "COPY --chown=aegisops:aegisops postgres/control-plane/migrations /opt/aegisops/postgres-migrations",
            "COPY --chown=aegisops:aegisops control-plane/deployment/first-boot/control-plane-entrypoint.sh /opt/aegisops/bin/first-boot-entrypoint.sh",
            "USER aegisops:aegisops",
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
        control_plane_block = self._control_plane_service_block(text)
        for term in (
            "build:",
            "dockerfile: control-plane/deployment/first-boot/Dockerfile",
            "image: aegisops-control-plane:first-boot",
            "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_FILE: ${AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_FILE:-}",
            "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_OPENBAO_PATH: ${AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_OPENBAO_PATH:-}",
            "AEGISOPS_CONTROL_PLANE_BOOT_MODE: ${AEGISOPS_CONTROL_PLANE_BOOT_MODE:-first-boot}",
            "AEGISOPS_CONTROL_PLANE_LOG_LEVEL: ${AEGISOPS_CONTROL_PLANE_LOG_LEVEL:-INFO}",
            "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_FILE: ${AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_FILE:-}",
            "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_OPENBAO_PATH: ${AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_OPENBAO_PATH:-}",
            "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET_FILE: ${AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET_FILE:-}",
            "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET_OPENBAO_PATH: ${AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET_OPENBAO_PATH:-}",
            "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_TRUSTED_PROXY_CIDRS: ${AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_TRUSTED_PROXY_CIDRS:-}",
            "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET_FILE: ${AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET_FILE:-}",
            "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET_OPENBAO_PATH: ${AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET_OPENBAO_PATH:-}",
            "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_TRUSTED_PROXY_CIDRS: ${AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_TRUSTED_PROXY_CIDRS:-}",
            "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_PROXY_SERVICE_ACCOUNT: ${AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_PROXY_SERVICE_ACCOUNT:-}",
            "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVIEWED_IDENTITY_PROVIDER: ${AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVIEWED_IDENTITY_PROVIDER:-}",
            "AEGISOPS_CONTROL_PLANE_ADMIN_BOOTSTRAP_TOKEN_FILE: ${AEGISOPS_CONTROL_PLANE_ADMIN_BOOTSTRAP_TOKEN_FILE:-}",
            "AEGISOPS_CONTROL_PLANE_ADMIN_BOOTSTRAP_TOKEN_OPENBAO_PATH: ${AEGISOPS_CONTROL_PLANE_ADMIN_BOOTSTRAP_TOKEN_OPENBAO_PATH:-}",
            "AEGISOPS_CONTROL_PLANE_BREAK_GLASS_TOKEN_FILE: ${AEGISOPS_CONTROL_PLANE_BREAK_GLASS_TOKEN_FILE:-}",
            "AEGISOPS_CONTROL_PLANE_BREAK_GLASS_TOKEN_OPENBAO_PATH: ${AEGISOPS_CONTROL_PLANE_BREAK_GLASS_TOKEN_OPENBAO_PATH:-}",
            "AEGISOPS_OPENBAO_ADDRESS: ${AEGISOPS_OPENBAO_ADDRESS:-}",
            "AEGISOPS_OPENBAO_TOKEN: ${AEGISOPS_OPENBAO_TOKEN:-}",
            "AEGISOPS_OPENBAO_TOKEN_FILE: ${AEGISOPS_OPENBAO_TOKEN_FILE:-}",
            "AEGISOPS_OPENBAO_KV_MOUNT: ${AEGISOPS_OPENBAO_KV_MOUNT:-secret}",
        ):
            self.assertIn(term, control_plane_block)

        for forbidden in (
            "image: alpine:3.22.1",
            "working_dir: /workspace/control-plane",
            "../../../:/workspace:ro",
            "./control-plane-entrypoint.sh:/opt/aegisops/bin/first-boot-entrypoint.sh:ro",
            "../../../postgres/control-plane/migrations:/opt/aegisops/postgres-migrations:ro",
        ):
            self.assertNotIn(forbidden, control_plane_block)

        self.assertNotIn("volumes:", control_plane_block)
        self.assertNotIn("working_dir:", control_plane_block)

    def test_first_boot_compose_keeps_proxy_as_only_published_ingress(self) -> None:
        compose_path = (
            REPO_ROOT / "control-plane" / "deployment" / "first-boot" / "docker-compose.yml"
        )
        self.assertTrue(compose_path.exists(), f"expected first-boot compose at {compose_path}")

        text = compose_path.read_text(encoding="utf-8")
        control_plane_block = self._control_plane_service_block(text)
        proxy_block = self._service_block(text, "proxy")

        self.assertIn(
            "AEGISOPS_CONTROL_PLANE_HOST: ${AEGISOPS_CONTROL_PLANE_HOST:-0.0.0.0}",
            control_plane_block,
        )
        self.assertNotIn("ports:", control_plane_block)
        self.assertIn("ports:", proxy_block)
        self.assertIn('- "${AEGISOPS_FIRST_BOOT_PROXY_PORT:-8080}:8080"', proxy_block)

    def test_first_boot_proxy_routes_reviewed_runtime_surfaces_to_control_plane(self) -> None:
        proxy_config = REPO_ROOT / "proxy" / "nginx" / "conf.d-first-boot" / "control-plane.conf"
        self.assertTrue(proxy_config.exists(), f"expected first-boot proxy config at {proxy_config}")

        text = proxy_config.read_text(encoding="utf-8")
        reviewed_routes = (
            "upstream aegisops_control_plane {",
            "server control-plane:8080;",
            "location = /healthz {",
            "proxy_pass http://aegisops_control_plane/healthz;",
            "location = /readyz {",
            "proxy_pass http://aegisops_control_plane/readyz;",
            "location = /runtime {",
            "proxy_pass http://aegisops_control_plane/runtime;",
            "location = /inspect-records {",
            "proxy_pass http://aegisops_control_plane/inspect-records$is_args$args;",
            "location = /inspect-reconciliation-status {",
            "proxy_pass http://aegisops_control_plane/inspect-reconciliation-status;",
            "location = /inspect-analyst-queue {",
            "proxy_pass http://aegisops_control_plane/inspect-analyst-queue$is_args$args;",
            "location = /inspect-alert-detail {",
            "proxy_pass http://aegisops_control_plane/inspect-alert-detail$is_args$args;",
            "location = /inspect-case-detail {",
            "proxy_pass http://aegisops_control_plane/inspect-case-detail$is_args$args;",
            "location = /inspect-action-review {",
            "proxy_pass http://aegisops_control_plane/inspect-action-review$is_args$args;",
            "location = /inspect-advisory-output {",
            "proxy_pass http://aegisops_control_plane/inspect-advisory-output$is_args$args;",
            "location = /operator/queue {",
            "proxy_pass http://aegisops_control_plane/inspect-analyst-queue$is_args$args;",
        )
        for term in reviewed_routes:
            self.assertIn(term, text)

        for forbidden in (
            "render-recommendation-draft",
            "/operator/promote-alert-to-case",
            "/operator/record-case-observation",
            "/operator/record-action-approval-decision",
            "/operator/create-reviewed-action-request",
            "/admin/bootstrap",
        ):
            self.assertNotIn(forbidden, text)

    @staticmethod
    def _control_plane_service_block(compose_text: str) -> str:
        return Phase17FirstBootRuntimeArtifactTests._service_block(
            compose_text,
            "control-plane",
        )

    @staticmethod
    def _service_block(compose_text: str, service_name: str) -> str:
        match = re.search(
            rf"(?ms)^  {re.escape(service_name)}:\n(.*?)(?=^  [a-z0-9-]+:\n|\Z)",
            compose_text,
        )
        if match is None:
            raise AssertionError(f"expected {service_name} service block in first-boot compose file")
        return match.group(0)


if __name__ == "__main__":
    unittest.main()
