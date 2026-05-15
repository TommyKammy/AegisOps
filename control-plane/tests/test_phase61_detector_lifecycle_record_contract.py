from __future__ import annotations

import pathlib
import sys
import unittest
from datetime import datetime, timezone

CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from aegisops.control_plane.ingestion.detection_lifecycle_helpers import (
    DetectionLifecycleTransitionHelper,
)
from aegisops.control_plane.models import (
    DetectorLifecycleRecord,
    LifecycleTransitionRecord,
)
from aegisops.control_plane.record_validation import _validate_record


class _FakeLifecycleTransitionStore:
    def __init__(self, latest_transition: LifecycleTransitionRecord | None = None) -> None:
        self.latest_transition = latest_transition

    def latest_lifecycle_transition(
        self,
        _record_family: str,
        _record_id: str,
    ) -> LifecycleTransitionRecord | None:
        return self.latest_transition


class _FakeLifecycleTransitionService:
    def __init__(self, latest_transition: LifecycleTransitionRecord | None = None) -> None:
        self._store = _FakeLifecycleTransitionStore(latest_transition=latest_transition)


def _detector_lifecycle_record(
    *,
    lifecycle_state: str,
    owner: str = "detector-owner",
    source_family: str = "github_audit",
    source_catalog_entry: str = "docs/source-families/github-audit/onboarding-package.md",
    lifecycle_audit_references: tuple[str, ...] = ("audit-evidence://catalog-entry",),
    disabled_reason: str | None = None,
    rollback_reason: str | None = None,
    review_overdue_reason: str | None = None,
) -> DetectorLifecycleRecord:
    return DetectorLifecycleRecord(
        detector_lifecycle_id="det-001",
        owner=owner,
        source_family=source_family,
        source_catalog_entry=source_catalog_entry,
        detector_identifier="wazuh-rule-windows-004",
        expected_signal_posture="high-confidence",
        review_cadence="daily",
        rollback_owner="rollback-owner",
        disable_owner="disable-owner",
        lifecycle_audit_references=lifecycle_audit_references,
        lifecycle_state=lifecycle_state,
        disabled_reason=disabled_reason,
        rollback_reason=rollback_reason,
        review_overdue_reason=review_overdue_reason,
    )


class Phase61DetectorLifecycleRecordContractTests(unittest.TestCase):
    def test_detector_lifecycle_transition_helper_rejects_candidate_to_active_skip(self) -> None:
        baseline_transition = LifecycleTransitionRecord(
            transition_id="t-candidate-001",
            subject_record_family="detector_lifecycle",
            subject_record_id="det-001",
            previous_lifecycle_state=None,
            lifecycle_state="candidate",
            transitioned_at=datetime.now(timezone.utc),
            attribution={},
        )
        helper = DetectionLifecycleTransitionHelper(
            _FakeLifecycleTransitionService(latest_transition=baseline_transition)
        )
        with self.assertRaisesRegex(
            ValueError,
            r"detector_lifecycle record transition from 'candidate' to 'active' is not supported",
        ):
            helper.build_lifecycle_transition_record(
                _detector_lifecycle_record(lifecycle_state="active"),
                existing_record=_detector_lifecycle_record(lifecycle_state="candidate"),
                latest_transition=baseline_transition,
            )

    def test_detector_lifecycle_transition_helper_allows_candidate_to_staging_progression(self) -> None:
        baseline_transition = LifecycleTransitionRecord(
            transition_id="t-candidate-001",
            subject_record_family="detector_lifecycle",
            subject_record_id="det-001",
            previous_lifecycle_state=None,
            lifecycle_state="candidate",
            transitioned_at=datetime.now(timezone.utc),
            attribution={},
        )
        helper = DetectionLifecycleTransitionHelper(
            _FakeLifecycleTransitionService(latest_transition=baseline_transition)
        )
        transition = helper.build_lifecycle_transition_record(
            _detector_lifecycle_record(lifecycle_state="staging"),
            existing_record=_detector_lifecycle_record(lifecycle_state="candidate"),
            latest_transition=baseline_transition,
        )
        self.assertIsNotNone(transition)
        assert transition is not None
        self.assertEqual(transition.previous_lifecycle_state, "candidate")
        self.assertEqual(transition.lifecycle_state, "staging")

    def test_detector_lifecycle_record_requires_owner_and_required_catalog_binding(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "requires non-blank owner",
        ):
            _validate_record(
                _detector_lifecycle_record(lifecycle_state="active", owner="")
            )

        with self.assertRaisesRegex(
            ValueError,
            "unsupported source_family",
        ):
            _validate_record(
                _detector_lifecycle_record(
                    lifecycle_state="active",
                    source_family="unreviewed-source",
                )
            )

    def test_detector_lifecycle_record_requires_disabled_reason_and_rollback_reason(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "in state 'disabled' requires non-blank disabled_reason",
        ):
            _validate_record(
                _detector_lifecycle_record(
                    lifecycle_state="disabled",
                    disabled_reason=" ",
                )
            )

        with self.assertRaisesRegex(
            ValueError,
            "in state 'rollback' requires non-blank rollback_reason",
        ):
            _validate_record(
                _detector_lifecycle_record(
                    lifecycle_state="rollback",
                    rollback_reason=None,
                )
            )

    def test_detector_lifecycle_record_rejects_non_matching_lifecycle_reason_fields(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            r"must not set disabled_reason; expected reason fields \[\]",
        ):
            _validate_record(
                _detector_lifecycle_record(
                    lifecycle_state="active",
                    disabled_reason="disabled for now",
                )
            )

    def test_detector_lifecycle_record_rejects_blank_lifecycle_audit_references(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            r"requires non-blank lifecycle_audit_references",
        ):
            _validate_record(
                _detector_lifecycle_record(
                    lifecycle_state="active",
                    lifecycle_audit_references=("",),
                )
            )

    def test_detector_lifecycle_record_requires_initial_candidate_state(self) -> None:
        helper = DetectionLifecycleTransitionHelper(
            _FakeLifecycleTransitionService(latest_transition=None)
        )
        with self.assertRaisesRegex(
            ValueError,
            r"must start at lifecycle_state 'candidate'",
        ):
            helper.build_lifecycle_transition_record(
                _detector_lifecycle_record(lifecycle_state="staging"),
                existing_record=None,
                latest_transition=None,
            )

    def test_detector_lifecycle_record_requires_review_overdue_reason(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "in state 'review-overdue' requires non-blank review_overdue_reason",
        ):
            _validate_record(
                _detector_lifecycle_record(
                    lifecycle_state="review-overdue",
                    review_overdue_reason=" ",
                )
            )
