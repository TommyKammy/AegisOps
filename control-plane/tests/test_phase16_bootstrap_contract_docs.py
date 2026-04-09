from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase16BootstrapContractDocsTests(unittest.TestCase):
    @staticmethod
    def _scope_doc() -> pathlib.Path:
        return REPO_ROOT / "docs" / "phase-16-release-state-and-first-boot-scope.md"

    def test_phase16_scope_doc_exists(self) -> None:
        design_doc = self._scope_doc()

        self.assertTrue(design_doc.exists(), f"expected Phase 16 design doc at {design_doc}")

    def test_phase16_scope_doc_defines_bootstrap_contracts(self) -> None:
        design_doc = self._scope_doc()
        self.assertTrue(design_doc.exists(), f"expected Phase 16 design doc at {design_doc}")
        text = design_doc.read_text(encoding="utf-8")

        for term in (
            "Bootstrap Environment Contract",
            "Migration Bootstrap Contract",
            "Healthcheck and Readiness Contract",
            "Deployment-Entrypoint Contract",
            "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN",
            "must fail closed",
            "migration bootstrap",
            "Healthcheck success",
            "readiness",
            "deployment entrypoint",
        ):
            self.assertIn(term, text)

    def test_first_boot_bootstrap_artifacts_exist_and_stay_narrow(self) -> None:
        bootstrap_sample = REPO_ROOT / "control-plane" / "deployment" / "first-boot" / "bootstrap.env.sample"
        compose_skeleton = (
            REPO_ROOT / "control-plane" / "deployment" / "first-boot" / "docker-compose.yml"
        )
        entrypoint_skeleton = (
            REPO_ROOT / "control-plane" / "deployment" / "first-boot" / "control-plane-entrypoint.sh"
        )

        for path in (bootstrap_sample, compose_skeleton, entrypoint_skeleton):
            self.assertTrue(path.exists(), f"expected first-boot artifact at {path}")

        bootstrap_text = bootstrap_sample.read_text(encoding="utf-8")
        for term in (
            "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN=",
            "AEGISOPS_CONTROL_PLANE_HOST=",
            "AEGISOPS_CONTROL_PLANE_PORT=",
            "Optional and deferred components below must remain non-blocking for first boot.",
            "AEGISOPS_CONTROL_PLANE_OPENSEARCH_URL=",
            "AEGISOPS_CONTROL_PLANE_N8N_BASE_URL=",
            "AEGISOPS_CONTROL_PLANE_ISOLATED_EXECUTOR_BASE_URL=",
        ):
            self.assertIn(term, bootstrap_text)

        compose_text = compose_skeleton.read_text(encoding="utf-8")
        for term in (
            "name: aegisops-first-boot",
            "control-plane:",
            "postgres:",
            "proxy:",
            "control-plane-entrypoint.sh:/opt/aegisops/bin/first-boot-entrypoint.sh:ro",
            "optional extensions remain out of scope for this first-boot skeleton",
            "do not add OpenSearch, n8n, analyst-assistant UI, or executor services here",
        ):
            self.assertIn(term, compose_text)

        entrypoint_text = entrypoint_skeleton.read_text(encoding="utf-8")
        for term in (
            "Phase 16 first-boot skeleton only",
            "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN",
            "migration bootstrap",
            "readiness",
            "OpenSearch, n8n, the full analyst-assistant surface, and executor wiring remain deferred",
            "exec \"$@\"",
        ):
            self.assertIn(term, entrypoint_text)


if __name__ == "__main__":
    unittest.main()
