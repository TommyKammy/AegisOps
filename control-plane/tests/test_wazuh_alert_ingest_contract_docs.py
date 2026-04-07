from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CONTRACT_DOC = REPO_ROOT / "docs" / "wazuh-alert-ingest-contract.md"
STATE_MODEL_DOC = REPO_ROOT / "docs" / "control-plane-state-model.md"
DOMAIN_MODEL_DOC = REPO_ROOT / "docs" / "secops-domain-model.md"
ACTION_SAFETY_DOC = REPO_ROOT / "docs" / "response-action-safety-model.md"
AUTOMATION_CONTRACT_DOC = REPO_ROOT / "docs" / "automation-substrate-contract.md"


class WazuhAlertIngestContractDocsTests(unittest.TestCase):
    def test_wazuh_contract_doc_defines_required_mapping_and_ownership_terms(self) -> None:
        self.assertTrue(
            CONTRACT_DOC.exists(),
            f"expected reviewed Wazuh contract doc at {CONTRACT_DOC}",
        )
        text = CONTRACT_DOC.read_text(encoding="utf-8")

        required_terms = (
            "Wazuh Alert Ingest Contract",
            "Required Fields",
            "Optional Fields",
            "substrate_detection_record_id",
            "analytic_signal_id",
            "alert_id",
            "provenance",
            "Substrate Detection Record",
            "Analytic Signal",
            "Alert",
            "Case",
            "Evidence",
            "Wazuh-native",
        )
        for term in required_terms:
            self.assertIn(term, text)

    def test_shared_docs_cross_link_to_the_reviewed_wazuh_contract(self) -> None:
        contract_path = "`docs/wazuh-alert-ingest-contract.md`"
        self.assertIn(
            contract_path,
            STATE_MODEL_DOC.read_text(encoding="utf-8"),
        )
        self.assertIn(
            contract_path,
            DOMAIN_MODEL_DOC.read_text(encoding="utf-8"),
        )

    def test_wazuh_contract_doc_names_reviewed_correlation_allowlist_and_provenance_only_fields(
        self,
    ) -> None:
        text = CONTRACT_DOC.read_text(encoding="utf-8")

        required_terms = (
            "current reviewed Wazuh correlation boundary uses the following native fields",
            "`location`",
            "`data.srcip`",
            "`data.srcuser`",
            "`data.integration`",
            "`data.event_type`",
            "provenance-only context",
            "`rule.groups`",
            "`decoder.name`",
        )
        for term in required_terms:
            self.assertIn(term, text)

    def test_shared_docs_cross_link_to_the_reviewed_automation_contract(self) -> None:
        contract_path = "`docs/automation-substrate-contract.md`"
        self.assertTrue(
            AUTOMATION_CONTRACT_DOC.exists(),
            f"expected reviewed automation contract doc at {AUTOMATION_CONTRACT_DOC}",
        )
        automation_contract_text = AUTOMATION_CONTRACT_DOC.read_text(encoding="utf-8")

        self.assertIn(
            contract_path,
            STATE_MODEL_DOC.read_text(encoding="utf-8"),
        )
        self.assertIn(
            contract_path,
            DOMAIN_MODEL_DOC.read_text(encoding="utf-8"),
        )
        self.assertIn(
            contract_path,
            ACTION_SAFETY_DOC.read_text(encoding="utf-8"),
        )

        required_terms = (
            "Approved Automation Delegation Contract",
            "delegation_id",
            "action_request_id",
            "approval_decision_id",
            "execution_surface_type",
            "execution_surface_id",
            "idempotency_key",
            "payload_hash",
            "Action Execution",
            "Reconciliation",
        )
        for term in required_terms:
            self.assertIn(term, automation_contract_text)


if __name__ == "__main__":
    unittest.main()
