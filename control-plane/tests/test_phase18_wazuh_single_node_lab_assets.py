from __future__ import annotations

import os
import pathlib
import subprocess
import tempfile
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase18WazuhSingleNodeLabAssetsTests(unittest.TestCase):
    @staticmethod
    def _asset_doc() -> pathlib.Path:
        return REPO_ROOT / "docs" / "phase-18-wazuh-single-node-lab-assets.md"

    @staticmethod
    def _asset_dir() -> pathlib.Path:
        return REPO_ROOT / "ingest" / "wazuh" / "single-node-lab"

    def test_phase18_asset_doc_exists(self) -> None:
        asset_doc = self._asset_doc()

        self.assertTrue(asset_doc.exists(), f"expected Phase 18 asset doc at {asset_doc}")

    def test_phase18_asset_doc_defines_bootstrap_inputs_and_operator_expectations(self) -> None:
        asset_doc = self._asset_doc()
        self.assertTrue(asset_doc.exists(), f"expected Phase 18 asset doc at {asset_doc}")
        text = asset_doc.read_text(encoding="utf-8")

        for term in (
            "Phase 18 Wazuh Single-Node Lab Assets",
            "single-node Wazuh lab target",
            "bootstrap inputs",
            "operator expectations",
            "GitHub audit",
            "Wazuh -> AegisOps",
            "Authorization: Bearer <shared secret>",
            "must remain untracked",
            "OpenSearch runtime extension",
            "multi-node or production-scale Wazuh",
        ):
            self.assertIn(term, text)

    def test_phase18_asset_bundle_exists_and_stays_narrow(self) -> None:
        asset_dir = self._asset_dir()
        compose_path = asset_dir / "docker-compose.yml"
        bootstrap_path = asset_dir / "bootstrap.env.sample"
        integration_path = asset_dir / "ossec.integration.sample.xml"
        render_helper_path = asset_dir / "render-ossec-integration.sh"
        readme_path = asset_dir / "README.md"

        for path in (compose_path, bootstrap_path, integration_path, render_helper_path, readme_path):
            self.assertTrue(path.exists(), f"expected Phase 18 Wazuh lab asset at {path}")

        compose_text = compose_path.read_text(encoding="utf-8")
        for term in (
            "name: aegisops-wazuh-single-node-lab",
            "wazuh-manager:",
            "wazuh-indexer:",
            "wazuh-dashboard:",
            '      - "1514/udp"',
            '      - "1515"',
            '      - "55000"',
            '      - "5601"',
            "AEGISOPS_WAZUH_AEGISOPS_INGEST_URL",
            "AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET_FILE",
            "./render-ossec-integration.sh:/wazuh-config-placeholder/render-ossec-integration.sh:ro",
            "GitHub audit remains the only approved first live source family",
            "render-ossec-integration.sh consumes the mounted secret file before operators copy literal values into active Wazuh config",
            "manager interfaces stay internal to the lab compose network until a reviewed lab access path exists",
            "dashboard access must stay on an internal-only or separately reviewed lab access path",
            "do not add Shuffle, n8n, or a direct control-plane backend publication path here",
        ):
            self.assertIn(term, compose_text)
        self.assertNotIn("ports:", compose_text)

        bootstrap_text = bootstrap_path.read_text(encoding="utf-8")
        for term in (
            "AEGISOPS_WAZUH_HOSTNAME=",
            "AEGISOPS_WAZUH_INDEXER_HOSTNAME=",
            "AEGISOPS_WAZUH_DASHBOARD_HOSTNAME=",
            "AEGISOPS_WAZUH_AEGISOPS_INGEST_URL=https://",
            "AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET_FILE=/run/aegisops-secrets/",
            "AEGISOPS_WAZUH_GITHUB_AUDIT_ENROLLMENT_STATUS=reviewed-first-live-family-only",
            "Do not commit live secrets",
            "render helper expects that path to resolve inside the manager container",
        ):
            self.assertIn(term, bootstrap_text)

        integration_text = integration_path.read_text(encoding="utf-8")
        for term in (
            "Render this sample with render-ossec-integration.sh before use.",
            "Wazuh reads hook_url and api_key literally",
            "<name>aegisops-github-audit</name>",
            "<hook_url>${AEGISOPS_WAZUH_AEGISOPS_INGEST_URL}</hook_url>",
            "<api_key>${AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET}</api_key>",
            "<alert_format>json</alert_format>",
            "GitHub audit only",
            "<group>github_audit</group>",
        ):
            self.assertIn(term, integration_text)

        render_helper_text = render_helper_path.read_text(encoding="utf-8")
        for term in (
            'require_env "AEGISOPS_WAZUH_AEGISOPS_INGEST_URL"',
            'require_env "AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET_FILE"',
            "<hook_url>",
            "<api_key>",
            "<group>github_audit</group>",
        ):
            self.assertIn(term, render_helper_text)

        readme_text = readme_path.read_text(encoding="utf-8")
        for term in (
            "single-node Wazuh lab target",
            "reviewed reverse proxy",
            "bootable AegisOps control-plane runtime boundary",
            "PostgreSQL-backed control-plane state",
            "GitHub audit",
            "not an approved production deployment",
            "service interfaces internal-only",
            "must not publish the control-plane backend port directly",
            "render-ossec-integration.sh",
            "Wazuh config",
        ):
            self.assertIn(term, readme_text)

    def test_render_helper_materializes_literal_integration_values(self) -> None:
        render_helper_path = self._asset_dir() / "render-ossec-integration.sh"
        self.assertTrue(render_helper_path.exists(), f"expected Phase 18 render helper at {render_helper_path}")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            secret_path = temp_path / "shared-secret.txt"
            output_path = temp_path / "rendered.xml"
            secret_path.write_text("reviewed<&>secret\n", encoding="utf-8")

            env = {
                **os.environ,
                "AEGISOPS_WAZUH_AEGISOPS_INGEST_URL": "https://aegisops.example.internal/intake/wazuh?channel=github&mode=lab",
                "AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET_FILE": str(secret_path),
            }
            completed = subprocess.run(
                ["bash", str(render_helper_path), str(output_path)],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )

            self.assertIn("Rendered", completed.stdout)
            rendered_text = output_path.read_text(encoding="utf-8")
            self.assertIn("<hook_url>https://aegisops.example.internal/intake/wazuh?channel=github&amp;mode=lab</hook_url>", rendered_text)
            self.assertIn("<api_key>reviewed&lt;&amp;&gt;secret</api_key>", rendered_text)
            self.assertIn("<group>github_audit</group>", rendered_text)


if __name__ == "__main__":
    unittest.main()
