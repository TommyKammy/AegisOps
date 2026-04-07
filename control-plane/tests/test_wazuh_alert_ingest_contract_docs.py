from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CONTRACT_DOC = REPO_ROOT / "docs" / "wazuh-alert-ingest-contract.md"
STATE_MODEL_DOC = REPO_ROOT / "docs" / "control-plane-state-model.md"
DOMAIN_MODEL_DOC = REPO_ROOT / "docs" / "secops-domain-model.md"
ACTION_SAFETY_DOC = REPO_ROOT / "docs" / "response-action-safety-model.md"
AUTOMATION_CONTRACT_DOC = REPO_ROOT / "docs" / "automation-substrate-contract.md"


def _extract_markdown_section(text: str, heading: str) -> str:
    start = text.index(heading)
    remainder = text[start:]
    next_same_level = remainder.find("\n### ", len(heading))
    if next_same_level == -1:
        return remainder
    return remainder[:next_same_level]


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

    def test_action_execution_ownership_is_consistent_across_shared_docs(self) -> None:
        domain_text = DOMAIN_MODEL_DOC.read_text(encoding="utf-8")
        state_model_text = STATE_MODEL_DOC.read_text(encoding="utf-8")
        automation_contract_text = AUTOMATION_CONTRACT_DOC.read_text(encoding="utf-8")

        domain_ownership_line = (
            "| `Action Execution` | AegisOps control-plane action-execution record | "
            "`Action Execution` remains the authoritative control-plane record for approved-versus-actual execution, "
            "while reviewed automation substrates and executor surfaces contribute correlated run identifiers, "
            "receipts, step progress, and other surface-local runtime evidence. |"
        )
        state_model_ownership_line = (
            "| `Action Execution` | AegisOps control-plane action-execution record | "
            "`Action Execution` remains the authoritative control-plane record for approved-versus-actual execution, "
            "while reviewed automation substrates and executor surfaces contribute correlated run identifiers, "
            "receipts, step progress, and other surface-local runtime evidence. |"
        )

        self.assertIn(domain_ownership_line, domain_text)
        self.assertIn(state_model_ownership_line, state_model_text)
        self.assertIn(
            "Execution-surface receipts, vendor run identifiers, and step logs are downstream evidence inputs. "
            "They must not replace the AegisOps-owned `Action Execution` or `Reconciliation` records.",
            automation_contract_text,
        )

    def test_reconciliation_identity_is_consistent_with_delegation_contract(self) -> None:
        state_model_text = STATE_MODEL_DOC.read_text(encoding="utf-8")
        automation_contract_text = AUTOMATION_CONTRACT_DOC.read_text(encoding="utf-8")

        self.assertIn(
            "The downstream execution intent must preserve `action_request_id`, `approval_decision_id`, "
            "`delegation_id`, `execution_surface_type`, `execution_surface_id`, `idempotency_key`, "
            "and `payload_hash` so later `Action Execution` and `Reconciliation` records can prove what "
            "was authorized and what actually ran.",
            automation_contract_text,
        )
        self.assertIn(
            "- `approval_decision_id`, `action_request_id`, `delegation_id`, "
            "`execution_surface_type`, `execution_surface_id`, `execution_run_id`, "
            "and an action idempotency key for the reviewed automation-substrate or executor run being reconciled.",
            state_model_text,
        )

    def test_action_execution_state_model_definition_matches_delegation_contract(self) -> None:
        state_model_text = STATE_MODEL_DOC.read_text(encoding="utf-8")
        automation_contract_text = AUTOMATION_CONTRACT_DOC.read_text(encoding="utf-8")
        action_execution_section = _extract_markdown_section(
            state_model_text,
            "### 6.12 Action Execution",
        )

        self.assertIn("### 6.12 Action Execution", state_model_text)
        self.assertIn(
            "| `action_execution_id` | Immutable AegisOps control-plane identifier for one action-execution record. |",
            action_execution_section,
        )
        self.assertIn(
            "| `action_request_id`, `approval_decision_id`, and `delegation_id` | Required lineage proving which approved request and emitted delegation the execution record represents. |",
            action_execution_section,
        )
        self.assertIn(
            "| `execution_surface_type`, `execution_surface_id`, and `execution_run_id` | Required downstream correlation fields identifying the reviewed surface and observed run. |",
            action_execution_section,
        )
        self.assertIn(
            "| Payload hash and idempotency key | Required binding fields proving the execution remained attached to the approved execution intent. |",
            action_execution_section,
        )
        for lifecycle_row in (
            "| `queued` | The approved execution was delegated and recorded, but the reviewed surface has not yet reported active execution. |",
            "| `running` | The reviewed surface reported that execution is actively in progress under the bound delegation context. |",
            "| `succeeded` | The observed run completed and reported a successful execution outcome, pending any later reconciliation updates. |",
            "| `failed` | The observed run completed with an execution failure or post-action verification failure under the current approved intent. |",
            "| `canceled` | The execution attempt was intentionally stopped before successful completion under operator or policy control. |",
            "| `superseded` | A newer execution record replaced this one for the same approved request after an explicit retry, re-drive, or recovery decision. |",
        ):
            self.assertIn(lifecycle_row, action_execution_section)
        for stale_lifecycle_row in (
            "| `pending` | The approved execution was delegated, but the reviewed surface has not yet reported that the run started. |",
            "| `timed_out` | The reviewed surface or control plane could not confirm completion before the bounded execution window expired. |",
            "| `unresolved` | Operators cannot yet prove whether the observed run matched the approved intent closely enough to classify it as succeeded, failed, or canceled. |",
        ):
            self.assertNotIn(stale_lifecycle_row, action_execution_section)
        self.assertIn(
            "Each later `Action Execution` record must link back to the originating `Action Request`, "
            "the governing `Approval Decision`, the emitted `delegation_id`, and the downstream "
            "`execution_run_id` observed on the reviewed surface.",
            automation_contract_text,
        )


if __name__ == "__main__":
    unittest.main()
