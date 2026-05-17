from __future__ import annotations

import pathlib
import re
import unittest


def _doc_path(relative_path: str) -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[2] / relative_path


def _catalog_rows(catalog_text: str) -> list[list[str]]:
    in_table = False
    rows: list[list[str]] = []
    for line in catalog_text.splitlines():
        if line.startswith("| Catalog action | Family | Owner |"):
            in_table = True
            continue
        if not in_table:
            continue
        if not line.startswith("|"):
            if rows:
                break
            continue
        if re.fullmatch(r"\|[ \-:|]+\|", line):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) == 10:
            rows.append(cells)
    return rows


def _catalog_validation_errors(catalog_text: str) -> list[str]:
    rows = _catalog_rows(catalog_text)
    errors: list[str] = []
    required_families = {"Read", "Notify", "Soft Write"}
    seen_families: set[str] = set()
    required_columns = (
        "action",
        "family",
        "owner",
        "substrate mapping need",
        "approval posture",
        "receipt shape",
        "reconciliation expectation",
        "allowed roles",
        "idempotency posture",
        "explicit limitations",
    )

    if not rows:
        errors.append("missing catalog rows")

    for row in rows:
        action = row[0].strip("`")
        family = row[1]
        seen_families.add(family)
        for index, column_name in enumerate(required_columns):
            if not row[index] or row[index] in {"-", "TBD", "TODO"}:
                errors.append(f"{action} missing {column_name}")
        if family in {"Controlled Write", "Hard Write"}:
            errors.append(f"{action} uses disallowed default family {family}")
        if "owner" in row[2].lower() and "missing" in row[2].lower():
            errors.append(f"{action} missing owner")
        if "direct ad-hoc Shuffle launch" not in row[3]:
            errors.append(f"{action} missing direct Shuffle launch rejection")
        if "AegisOps" not in row[4] or "action request" not in row[4]:
            errors.append(f"{action} missing action request approval posture")
        if "AegisOps execution receipt" not in row[5]:
            errors.append(f"{action} missing AegisOps receipt expectation")
        if "cannot" not in row[6].lower():
            errors.append(f"{action} missing reconciliation limitation")
        if "`analyst`" not in row[7] or "`approver`" not in row[7]:
            errors.append(f"{action} missing role boundary")
        if "Idempotency key" not in row[8]:
            errors.append(f"{action} missing idempotency posture")
        if "No " not in row[9]:
            errors.append(f"{action} missing explicit negative limitation")

    for family in required_families - seen_families:
        errors.append(f"missing required family {family}")

    broad_claims = (
        "broad SOAR marketplace coverage is implemented",
        "arbitrary SOAR connector marketplace import is approved",
        "Phase 62.1 claims Beta",
        "Controlled Write is a default Phase 62.1 catalog entry",
        "Hard Write is a default Phase 62.1 catalog entry",
    )
    rendered_without_forbidden = catalog_text.split("## 6. Forbidden Claims", 1)[0]
    for claim in broad_claims:
        if claim in rendered_without_forbidden:
            errors.append(f"forbidden overclaim outside rejection context: {claim}")
    return errors


class Phase62ReviewedAutomationCatalogContractTests(unittest.TestCase):
    catalog_doc = _doc_path("docs/phase-62-reviewed-automation-catalog-contract.md")
    validation_doc = _doc_path(
        "docs/phase-62-1-reviewed-automation-catalog-validation.md"
    )
    phase54_closeout = _doc_path("docs/phase-54-closeout-evaluation.md")
    phase56_closeout = _doc_path("docs/phase-56-closeout-evaluation.md")
    phase57_closeout = _doc_path("docs/phase-57-closeout-evaluation.md")
    phase61_closeout = _doc_path("docs/phase-61-closeout-evaluation.md")
    policy_doc = _doc_path("docs/phase-51-6-authority-boundary-negative-test-policy.md")

    def test_required_artifacts_exist(self) -> None:
        for path in (
            self.catalog_doc,
            self.validation_doc,
            self.phase54_closeout,
            self.phase56_closeout,
            self.phase57_closeout,
            self.phase61_closeout,
            self.policy_doc,
        ):
            self.assertTrue(path.exists(), f"expected {path} to exist")

    def test_catalog_covers_default_read_notify_soft_write_entries(self) -> None:
        catalog_text = self.catalog_doc.read_text(encoding="utf-8")
        rows = _catalog_rows(catalog_text)
        by_action = {row[0].strip("`"): row for row in rows}

        self.assertEqual(
            {
                "enrichment_only_lookup",
                "operator_notification",
                "manual_escalation_request",
                "create_tracking_ticket",
            },
            set(by_action),
        )
        self.assertEqual("Read", by_action["enrichment_only_lookup"][1])
        self.assertEqual("Notify", by_action["operator_notification"][1])
        self.assertEqual("Notify", by_action["manual_escalation_request"][1])
        self.assertEqual("Soft Write", by_action["create_tracking_ticket"][1])

    def test_catalog_rows_have_required_contract_fields(self) -> None:
        catalog_text = self.catalog_doc.read_text(encoding="utf-8")

        self.assertEqual([], _catalog_validation_errors(catalog_text))

    def test_catalog_references_reviewed_shuffle_without_direct_launch(self) -> None:
        catalog_text = self.catalog_doc.read_text(encoding="utf-8")

        required_terms = (
            "reviewed Phase 54 Shuffle profile",
            "reviewed Phase 54 Shuffle `enrichment_only_lookup` template contract",
            "reviewed Phase 54 Shuffle `operator_notification` template contract",
            "reviewed Phase 54 Shuffle `manual_escalation_request` template contract",
            "reviewed Phase 54 Shuffle `create_tracking_ticket` template import contract",
            "No direct ad-hoc Shuffle launch.",
        )
        for term in required_terms:
            self.assertIn(term, catalog_text)

    def test_rejects_controlled_and_hard_write_default_entries(self) -> None:
        catalog_text = self.catalog_doc.read_text(encoding="utf-8")
        controlled_text = catalog_text.replace(
            "| `operator_notification` | Notify |",
            "| `operator_notification` | Controlled Write |",
        )
        hard_text = catalog_text.replace(
            "| `create_tracking_ticket` | Soft Write |",
            "| `create_tracking_ticket` | Hard Write |",
        )

        self.assertIn(
            "operator_notification uses disallowed default family Controlled Write",
            _catalog_validation_errors(controlled_text),
        )
        self.assertIn(
            "create_tracking_ticket uses disallowed default family Hard Write",
            _catalog_validation_errors(hard_text),
        )

    def test_rejects_missing_owner_receipt_and_limitation(self) -> None:
        catalog_text = self.catalog_doc.read_text(encoding="utf-8")
        missing_owner = catalog_text.replace(
            "| `enrichment_only_lookup` | Read | AegisOps maintainers and IT Operations, Information Systems Department |",
            "| `enrichment_only_lookup` | Read | TODO |",
        )
        missing_receipt = catalog_text.replace(
            "AegisOps execution receipt with `action_request_id`, `catalog_action`, `family`, `reviewed_template_version`, `correlation_id`, `idempotency_key`, `started_at`, `finished_at`, `status`, and subordinate lookup evidence reference.",
            "TODO",
        )
        missing_limitation = catalog_text.replace(
            "Read-only enrichment context. No protected target mutation, credential change, ticket mutation, case closure, detector activation, suppression activation, direct source actioning, or marketplace expansion.",
            "TODO",
        )

        self.assertIn(
            "enrichment_only_lookup missing owner",
            _catalog_validation_errors(missing_owner),
        )
        self.assertIn(
            "enrichment_only_lookup missing receipt shape",
            _catalog_validation_errors(missing_receipt),
        )
        self.assertIn(
            "enrichment_only_lookup missing explicit limitations",
            _catalog_validation_errors(missing_limitation),
        )

    def test_rejects_marketplace_and_readiness_overclaim_outside_forbidden_context(
        self,
    ) -> None:
        catalog_text = self.catalog_doc.read_text(encoding="utf-8")
        overclaim_text = catalog_text.replace(
            "Phase 62.1 records the default reviewed automation catalog",
            "Phase 62.1 records that broad SOAR marketplace coverage is implemented and the default reviewed automation catalog",
        )

        self.assertIn(
            "forbidden overclaim outside rejection context: broad SOAR marketplace coverage is implemented",
            _catalog_validation_errors(overclaim_text),
        )

    def test_validation_file_states_pass_and_handoff_limitations(self) -> None:
        validation_text = self.validation_doc.read_text(encoding="utf-8")

        required_terms = (
            "# Phase 62.1 Reviewed Automation Catalog Contract Validation",
            "- Validation status: PASS",
            "Read: `enrichment_only_lookup`",
            "Notify: `operator_notification`, `manual_escalation_request`",
            "Soft Write: `create_tracking_ticket`",
            "Controlled Write and Hard Write default entries",
            "No deviations.",
            "Controlled Write and Hard Write remain blocked from default enablement",
        )
        for term in required_terms:
            self.assertIn(term, validation_text)


if __name__ == "__main__":
    unittest.main()
