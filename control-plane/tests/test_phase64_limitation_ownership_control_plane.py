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
from aegisops.control_plane.config import RuntimeConfig  # noqa: E402
from aegisops.control_plane.models import KnownLimitationOwnershipRecord  # noqa: E402
from aegisops.control_plane.record_validation import _validate_record  # noqa: E402
from aegisops.control_plane.service import AegisOpsControlPlaneService  # noqa: E402
from aegisops.control_plane.validation.phase64_record_validators import (  # noqa: E402
    validate_known_limitation_current_review,
)
from postgres_test_support import make_store  # noqa: E402


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
    def test_current_review_validation_rejects_expired_review_due_date(self) -> None:
        expired_due_date = (date.today() - timedelta(days=1)).isoformat()

        with self.assertRaisesRegex(ValueError, "expired review"):
            validate_known_limitation_current_review(
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
        self.assertEqual(projection["review_due_date_status"], "not_specified")
        self.assertFalse(projection["review_due_date_expired"])
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

    def test_projection_preserves_expired_limitation_context(self) -> None:
        expired_due_date = (date.today() - timedelta(days=1)).isoformat()
        record = _known_limitation_ownership_record(
            review_cadence=None,
            due_date=expired_due_date,
        )

        projection = project_limitation_ownership_context(
            record,
            consumer="inspection",
            requested_authority="none",
        )

        self.assertEqual(projection["limitation_id"], record.limitation_id)
        self.assertEqual(projection["due_date"], expired_due_date)
        self.assertEqual(projection["review_due_date_status"], "expired")
        self.assertTrue(projection["review_due_date_expired"])
        self.assertEqual(
            projection["authority_posture"],
            "subordinate_limitation_context_only",
        )
        self.assertFalse(projection["workflow_truth"])

    def test_projection_rejects_authority_promotion_request(self) -> None:
        record = _known_limitation_ownership_record()
        _validate_record(record)

        with self.assertRaisesRegex(ValueError, "cannot provide workflow authority"):
            project_limitation_ownership_context(
                record,
                consumer="inspection",
                requested_authority="release_truth",
            )

    def test_read_surface_inspects_limitation_ownership_through_backend_projection(
        self,
    ) -> None:
        store, _backend = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        record = _known_limitation_ownership_record()

        service.persist_record(record)

        read_surface = service._operator_inspection_read_surface
        projection = read_surface.inspect_limitation_ownership_detail(
            record.limitation_id
        )
        self.assertEqual(projection["limitation_id"], record.limitation_id)
        self.assertEqual(projection["consumer"], "inspection")
        self.assertEqual(projection["review_cadence"], "weekly")
        self.assertFalse(projection["readiness_truth"])
        self.assertFalse(projection["release_truth"])
        self.assertFalse(projection["gate_truth"])
        self.assertFalse(projection["workflow_truth"])
        self.assertNotIn("stale_cache", projection)

    def test_read_surface_requires_explicit_limitation_when_multiple_records_exist(
        self,
    ) -> None:
        store, _backend = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        service.persist_record(
            _known_limitation_ownership_record(limitation_id="limitation-001")
        )
        service.persist_record(
            _known_limitation_ownership_record(limitation_id="limitation-002")
        )

        read_surface = service._operator_inspection_read_surface
        with self.assertRaisesRegex(LookupError, "explicit limitation_id"):
            read_surface.inspect_limitation_ownership_detail()


if __name__ == "__main__":
    unittest.main()
