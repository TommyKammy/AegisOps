from __future__ import annotations

from datetime import date, timedelta
import pathlib
import sys
import unittest

CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from aegisops.control_plane.inspection.limitation_ownership_projection import (  # noqa: E402
    project_limitation_ownership_context,
)
from aegisops.control_plane.models import KnownLimitationOwnershipRecord  # noqa: E402
from aegisops.control_plane.record_validation import _validate_record  # noqa: E402


def _known_limitation_ownership_record(
    *,
    limitation_id: str = "limitation-phase64-control-plane-001",
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
) -> KnownLimitationOwnershipRecord:
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
    )


class Phase64LimitationOwnershipControlPlaneTests(unittest.TestCase):
    def test_validation_rejects_expired_review_due_date(self) -> None:
        expired_due_date = (date.today() - timedelta(days=1)).isoformat()

        with self.assertRaisesRegex(ValueError, "expired review"):
            _validate_record(
                _known_limitation_ownership_record(
                    review_cadence=None,
                    due_date=expired_due_date,
                )
            )

    def test_projection_exposes_subordinate_limitation_context_only(self) -> None:
        record = _known_limitation_ownership_record()
        _validate_record(record)

        projection = project_limitation_ownership_context(
            record,
            consumer="service_snapshot",
            requested_authority="none",
        )

        self.assertEqual(projection["limitation_id"], record.limitation_id)
        self.assertEqual(projection["consumer"], "service_snapshot")
        self.assertEqual(projection["review_state"], record.review_state)
        self.assertEqual(
            projection["authority_posture"],
            "subordinate_limitation_context_only",
        )
        self.assertFalse(projection["readiness_truth"])
        self.assertFalse(projection["release_truth"])
        self.assertFalse(projection["gate_truth"])
        self.assertFalse(projection["workflow_truth"])
        self.assertEqual(projection["workflow_authority"], "none")
        self.assertNotIn("lifecycle_state", projection)
        self.assertNotIn("readiness_claim", projection)

    def test_projection_rejects_authority_promotion_request(self) -> None:
        record = _known_limitation_ownership_record()
        _validate_record(record)

        with self.assertRaisesRegex(ValueError, "cannot provide workflow authority"):
            project_limitation_ownership_context(
                record,
                consumer="inspection",
                requested_authority="release_truth",
            )


if __name__ == "__main__":
    unittest.main()
