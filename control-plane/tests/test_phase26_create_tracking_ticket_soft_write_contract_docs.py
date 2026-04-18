from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase26CreateTrackingTicketSoftWriteContractDocsTests(unittest.TestCase):
    @staticmethod
    def _read(relative_path: str) -> str:
        path = REPO_ROOT / relative_path
        if not path.exists():
            raise AssertionError(f"expected document at {path}")
        return path.read_text(encoding="utf-8")

    def test_create_tracking_ticket_contract_doc_exists_and_stays_narrow(self) -> None:
        text = self._read(
            "docs/phase-26-create-tracking-ticket-soft-write-contract.md"
        )

        for term in (
            "# AegisOps Phase 26 First Reviewed Create-Tracking-Ticket Soft-Write Contract",
            "This document defines the first reviewed `create_tracking_ticket` soft-write contract for the Phase 26 coordination boundary.",
            "`create_tracking_ticket` remains a bounded `Soft Write` coordination action.",
            "AegisOps remains authoritative for case, approval, action-execution, and reconciliation truth.",
            "`case_id`",
            "`coordination_reference_id`",
            "`coordination_target_type`",
            "`requested_payload`",
            "`payload_hash`",
            "`idempotency_key`",
            "Only the reviewed coordination ticket create payload may leave AegisOps.",
            "The first reviewed payload is limited to reviewed coordination fields and must not export AegisOps-owned lifecycle truth.",
            "The downstream receipt must prove which reviewed coordination target accepted which bounded create request.",
            "If the downstream target cannot prove whether a duplicate create request matches the same approved intent, AegisOps must fail closed",
            "A failed, rejected, expired, or unbound create attempt must not leave durable partial truth behind inside AegisOps.",
            "Human approval is required for the first reviewed `create_tracking_ticket` path.",
            "This contract does not approve status synchronization, close or reopen delegation, comment synchronization, downstream case ownership, or downstream approval authority.",
        ):
            self.assertIn(term, text)

        outbound_section = text.split("## 4. Idempotency, Receipt, and Reconciliation Contract")[0]
        self.assertIn(
            "Allowed values for this phase: `zammad` for the preferred reviewed coordination substrate or `glpi` for the reviewed fallback only.",
            outbound_section,
        )
        self.assertNotIn("| `external_receipt_id` |", outbound_section)
        self.assertIn(
            "`external_receipt_id` is mandatory for receipt binding once the reviewed downstream target accepts the create request, and it is not part of the outbound create request payload.",
            text,
        )

    def test_create_tracking_ticket_contract_validation_note_records_alignment(self) -> None:
        text = self._read(
            "docs/phase-26-create-tracking-ticket-soft-write-contract-validation.md"
        )

        for term in (
            "# Phase 26 First Reviewed Create-Tracking-Ticket Soft-Write Contract Validation",
            "Validation status: PASS",
            "docs/phase-26-create-tracking-ticket-soft-write-contract.md",
            "docs/phase-26-first-coordination-substrate-and-non-authoritative-ticket-boundary.md",
            "docs/response-action-safety-model.md",
            "docs/control-plane-state-model.md",
            "`create_tracking_ticket` remains a bounded `Soft Write` coordination action.",
            "AegisOps remains authoritative for case, approval, action-execution, and reconciliation truth.",
            "The reviewed contract excludes status sync, close or reopen control, comment sync, and downstream truth ownership.",
            'python3 -m unittest discover -s control-plane/tests -p "test_phase26_create_tracking_ticket_soft_write_contract_docs.py"',
        ):
            self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
