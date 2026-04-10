from __future__ import annotations

import pathlib
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
        readme_path = asset_dir / "README.md"

        for path in (compose_path, bootstrap_path, integration_path, readme_path):
            self.assertTrue(path.exists(), f"expected Phase 18 Wazuh lab asset at {path}")

        compose_text = compose_path.read_text(encoding="utf-8")
        for term in (
            "name: aegisops-wazuh-single-node-lab",
            "wazuh-manager:",
            "wazuh-indexer:",
            "wazuh-dashboard:",
            "5601:5601",
            "1514:1514/udp",
            "1515:1515",
            "55000:55000",
            "AEGISOPS_WAZUH_AEGISOPS_INGEST_URL",
            "AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET_FILE",
            "GitHub audit remains the only approved first live source family",
            "do not add Shuffle, n8n, or a direct control-plane backend publication path here",
        ):
            self.assertIn(term, compose_text)

        bootstrap_text = bootstrap_path.read_text(encoding="utf-8")
        for term in (
            "AEGISOPS_WAZUH_HOSTNAME=",
            "AEGISOPS_WAZUH_INDEXER_HOSTNAME=",
            "AEGISOPS_WAZUH_DASHBOARD_HOSTNAME=",
            "AEGISOPS_WAZUH_AEGISOPS_INGEST_URL=https://",
            "AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET_FILE=",
            "AEGISOPS_WAZUH_GITHUB_AUDIT_ENROLLMENT_STATUS=reviewed-first-live-family-only",
            "Do not commit live secrets",
        ):
            self.assertIn(term, bootstrap_text)

        integration_text = integration_path.read_text(encoding="utf-8")
        for term in (
            "<name>aegisops-github-audit</name>",
            "<hook_url>${AEGISOPS_WAZUH_AEGISOPS_INGEST_URL}</hook_url>",
            "<api_key>${AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET}</api_key>",
            "<alert_format>json</alert_format>",
            "GitHub audit only",
        ):
            self.assertIn(term, integration_text)

        readme_text = readme_path.read_text(encoding="utf-8")
        for term in (
            "single-node Wazuh lab target",
            "reviewed reverse proxy",
            "bootable AegisOps control-plane runtime boundary",
            "PostgreSQL-backed control-plane state",
            "GitHub audit",
            "not an approved production deployment",
            "must not publish the control-plane backend port directly",
        ):
            self.assertIn(term, readme_text)


if __name__ == "__main__":
    unittest.main()
