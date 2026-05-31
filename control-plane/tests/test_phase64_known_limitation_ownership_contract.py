from __future__ import annotations

import pathlib
import sys
import unittest

CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from aegisops.control_plane.models import KnownLimitationOwnershipRecord
from aegisops.control_plane.record_validation import _validate_record
from aegisops.control_plane.service import RECORD_TYPES_BY_FAMILY
from aegisops.control_plane.validation import phase64_record_validators


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

    def test_known_limitation_ownership_rejects_readiness_and_release_overclaims(
        self,
    ) -> None:
        forbidden_claims = (
            "AegisOps is RC ready because this limitation has an owner.",
            "AegisOps is GA ready because this limitation has an owner.",
            "AegisOps is a self-service commercial replacement.",
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


if __name__ == "__main__":
    unittest.main()
