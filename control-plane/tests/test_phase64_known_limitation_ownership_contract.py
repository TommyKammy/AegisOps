from __future__ import annotations

import pathlib
import sys
import unittest

CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from aegisops.control_plane.config import RuntimeConfig
from aegisops.control_plane.models import (
    KnownLimitationOwnershipRecord,
    LifecycleTransitionRecord,
)
from aegisops.control_plane.record_validation import _validate_record
from aegisops.control_plane.service import (
    AegisOpsControlPlaneService,
    AUTHORITATIVE_RECORD_CHAIN_BACKUP_SCHEMA_VERSION,
    RECORD_TYPES_BY_FAMILY,
)
from aegisops.control_plane.validation import phase64_record_validators
from postgres_test_support import make_store


def _known_limitation_ownership_record(
    *,
    limitation_id: str = "limitation-phase64-support-bundle-001",
    title: str = "Support bundle evidence remains separately tracked.",
    severity: str = "material",
    affected_surface: str = "supportability_evidence",
    owner: str = "supportability-owner",
    mitigation: str = "Track the support bundle slice before Phase 66 RC proof.",
    evidence_references: tuple[str, ...] = (
        "docs/phase-63-closeout-evaluation.md#support-bundle-gap-disposition",
    ),
    review_state: str = "accepted_risk",
    review_cadence: str | None = "weekly",
    due_date: str | None = None,
    accepted_risk_posture: str = "bounded_pre_rc_limitation",
    phase66_handoff_posture: str = "handoff_required",
    authority_boundary: str = "reviewed_evidence_input_only",
    readiness_claim: str | None = None,
    lifecycle_state: str | None = None,
) -> KnownLimitationOwnershipRecord:
    if lifecycle_state is None:
        lifecycle_state = review_state
    return KnownLimitationOwnershipRecord(
        limitation_id=limitation_id,
        title=title,
        severity=severity,
        affected_surface=affected_surface,
        owner=owner,
        mitigation=mitigation,
        evidence_references=evidence_references,
        review_state=review_state,
        review_cadence=review_cadence,
        due_date=due_date,
        accepted_risk_posture=accepted_risk_posture,
        phase66_handoff_posture=phase66_handoff_posture,
        authority_boundary=authority_boundary,
        readiness_claim=readiness_claim,
        lifecycle_state=lifecycle_state,
    )


class Phase64KnownLimitationOwnershipContractTests(unittest.TestCase):
    def test_known_limitation_ownership_record_is_registered_reviewed_contract_family(
        self,
    ) -> None:
        record = _known_limitation_ownership_record()

        self.assertTrue(phase64_record_validators.is_phase64_record_family(record))
        self.assertIs(
            RECORD_TYPES_BY_FAMILY["known_limitation_ownership"],
            KnownLimitationOwnershipRecord,
        )
        _validate_record(record)

    def test_known_limitation_ownership_persists_and_inspects_with_lifecycle_history(
        self,
    ) -> None:
        store, _backend = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        record = _known_limitation_ownership_record(review_state="under_review")

        service.persist_record(record)

        self.assertEqual(
            store.get(KnownLimitationOwnershipRecord, record.record_id),
            record,
        )
        inspection = service.inspect_records("known_limitation_ownership")
        self.assertEqual(
            inspection.records,
            (
                {
                    "limitation_id": record.limitation_id,
                    "title": record.title,
                    "severity": record.severity,
                    "affected_surface": record.affected_surface,
                    "owner": record.owner,
                    "mitigation": record.mitigation,
                    "evidence_references": record.evidence_references,
                    "review_state": record.review_state,
                    "review_cadence": record.review_cadence,
                    "due_date": record.due_date,
                    "accepted_risk_posture": record.accepted_risk_posture,
                    "phase66_handoff_posture": record.phase66_handoff_posture,
                    "authority_boundary": record.authority_boundary,
                    "readiness_claim": record.readiness_claim,
                    "lifecycle_state": record.review_state,
                },
            ),
        )
        transitions = service.list_lifecycle_transitions(
            "known_limitation_ownership",
            record.limitation_id,
        )
        self.assertEqual(len(transitions), 1)
        self.assertIsInstance(transitions[0], LifecycleTransitionRecord)
        self.assertEqual(
            transitions[0].subject_record_family,
            "known_limitation_ownership",
        )
        self.assertEqual(transitions[0].lifecycle_state, "under_review")

    def test_known_limitation_ownership_is_authoritative_backup_family(
        self,
    ) -> None:
        store, _backend = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        record = _known_limitation_ownership_record(review_state="accepted_risk")
        service.persist_record(record)

        backup = service.export_authoritative_record_chain_backup()

        self.assertEqual(
            backup["backup_schema_version"],
            AUTHORITATIVE_RECORD_CHAIN_BACKUP_SCHEMA_VERSION,
        )
        self.assertEqual(backup["record_counts"]["known_limitation_ownership"], 1)
        self.assertEqual(
            backup["record_families"]["known_limitation_ownership"][0][
                "limitation_id"
            ],
            record.limitation_id,
        )
        self.assertTrue(
            any(
                transition["subject_record_family"]
                == "known_limitation_ownership"
                and transition["subject_record_id"] == record.limitation_id
                for transition in backup["record_families"]["lifecycle_transition"]
            )
        )

        restored_store, _backend = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )
        restore_summary = restored_service.restore_authoritative_record_chain_backup(
            backup
        )

        self.assertEqual(
            restore_summary.restored_record_counts["known_limitation_ownership"],
            1,
        )
        self.assertEqual(
            restored_store.get(KnownLimitationOwnershipRecord, record.limitation_id),
            record,
        )

    def test_known_limitation_ownership_restore_dry_run_rejects_invalid_contract_shape(
        self,
    ) -> None:
        store, _backend = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        record = _known_limitation_ownership_record()
        service.persist_record(record)
        backup = service.export_authoritative_record_chain_backup()
        backup["record_families"]["known_limitation_ownership"][0][
            "severity"
        ] = "catastrophic"

        restored_store, _backend = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )
        diagnostics_service = (
            restored_service._runtime_restore_readiness_diagnostics_service
        )

        with self.assertRaisesRegex(ValueError, "unsupported severity"):
            diagnostics_service.dry_run_authoritative_record_chain_restore(backup)
        self.assertEqual(restored_store.list(KnownLimitationOwnershipRecord), ())

    def test_known_limitation_ownership_default_lifecycle_state_follows_review_state(
        self,
    ) -> None:
        record = KnownLimitationOwnershipRecord(
            limitation_id="limitation-phase64-default-lifecycle-001",
            title="Default lifecycle state follows the reviewed state.",
            severity="medium",
            affected_surface="record_contract",
            owner="contract-owner",
            mitigation="Keep lifecycle history aligned to review state.",
            evidence_references=(
                "docs/phase-64-1-known-limitation-ownership-record-contract.md",
            ),
            review_state="mitigation_planned",
            review_cadence="weekly",
            due_date=None,
            accepted_risk_posture="bounded_pre_rc_limitation",
            phase66_handoff_posture="handoff_required",
            authority_boundary="reviewed_evidence_input_only",
        )

        self.assertEqual(record.lifecycle_state, "mitigation_planned")
        _validate_record(record)

    def test_known_limitation_ownership_requires_explicit_owner_mitigation_evidence_surface_review_and_handoff(
        self,
    ) -> None:
        required_fields = (
            "owner",
            "mitigation",
            "evidence_references",
            "affected_surface",
            "review_state",
            "phase66_handoff_posture",
        )

        for field_name in required_fields:
            with self.subTest(field_name=field_name):
                kwargs: dict[str, object] = {field_name: ""}
                if field_name == "evidence_references":
                    kwargs[field_name] = ()
                record = _known_limitation_ownership_record(**kwargs)
                with self.assertRaisesRegex(ValueError, field_name):
                    _validate_record(record)

    def test_known_limitation_ownership_rejects_unsupported_review_and_handoff_states(
        self,
    ) -> None:
        with self.assertRaisesRegex(ValueError, "review_state"):
            _validate_record(
                _known_limitation_ownership_record(review_state="ready_for_rc")
            )

        with self.assertRaisesRegex(ValueError, "phase66_handoff_posture"):
            _validate_record(
                _known_limitation_ownership_record(
                    phase66_handoff_posture="rc_proof_complete"
                )
            )

    def test_known_limitation_ownership_allows_ordinary_workflow_limitation_text(
        self,
    ) -> None:
        record = _known_limitation_ownership_record(
            title="Approval expiry mitigation remains manual.",
            mitigation="Track the execution gap as a known limitation.",
            accepted_risk_posture=(
                "Reconciliation coverage remains partial until the evidence owner review."
            ),
        )

        _validate_record(record)

    def test_known_limitation_ownership_rejects_readiness_and_release_overclaims(
        self,
    ) -> None:
        forbidden_claims = (
            "AegisOps is RC ready because this limitation has an owner.",
            "AegisOps is GA ready because this limitation has an owner.",
            "AegisOps is a self-service commercial replacement.",
            "Support-bundle completion is achieved for this limitation.",
            "This limitation is gate truth for Phase 66.",
            "This limitation proves case closure.",
            "This limitation proves approval, execution, and reconciliation.",
            "AegisOps has SIEM/SOAR replacement readiness.",
            "Verifier output is readiness truth for this limitation.",
            "Issue-lint output is readiness truth for this limitation.",
        )

        for readiness_claim in forbidden_claims:
            with self.subTest(readiness_claim=readiness_claim):
                with self.assertRaisesRegex(ValueError, "readiness"):
                    _validate_record(
                        _known_limitation_ownership_record(
                            readiness_claim=readiness_claim
                        )
                    )

    def test_known_limitation_ownership_rejects_affected_surface_overclaims(
        self,
    ) -> None:
        with self.assertRaisesRegex(ValueError, "affected_surface"):
            _validate_record(
                _known_limitation_ownership_record(
                    affected_surface="SIEM/SOAR replacement readiness"
                )
            )


if __name__ == "__main__":
    unittest.main()
