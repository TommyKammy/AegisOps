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
    FalsePositiveReviewRecord,
    LifecycleTransitionRecord,
    SuppressionProposalRecord,
)
from aegisops.control_plane.runtime.restore_backup_validation import (
    RestoreValidationBoundary,
)
from aegisops.control_plane.service import (
    AUTHORITATIVE_RECORD_CHAIN_RECORD_TYPES,
    AUTHORITATIVE_RECORD_CHAIN_BACKUP_SCHEMA_VERSION,
    RECORD_TYPES_BY_FAMILY,
    _AUTHORITATIVE_PRIMARY_ID_FIELD_BY_FAMILY,
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


def _false_positive_review_record(
    *,
    false_positive_review_id: str = "fp-review-001",
    owner: str = "fp-review-owner",
    detector_lifecycle_id: str = "det-001",
    source_family: str = "github_audit",
    source_catalog_entry: str = "docs/source-families/github-audit/onboarding-package.md",
    alert_id: str | None = "alert-001",
    case_id: str | None = "case-001",
    evidence_ids: tuple[str, ...] = ("evidence-001",),
    disposition: str = "benign_activity",
    disposition_rationale: str = "Reviewed admin membership change matched approved access ticket.",
    dispute_state: str = "undisputed",
    recurrence_posture: str = "single_reviewed_instance",
    review_evidence_references: tuple[str, ...] = ("evidence://case-001/admin-ticket",),
    source_signal_handling: str = "preserve_source_signal",
    lifecycle_state: str = "reviewed",
) -> FalsePositiveReviewRecord:
    return FalsePositiveReviewRecord(
        false_positive_review_id=false_positive_review_id,
        detector_lifecycle_id=detector_lifecycle_id,
        source_family=source_family,
        source_catalog_entry=source_catalog_entry,
        alert_id=alert_id,
        case_id=case_id,
        evidence_ids=evidence_ids,
        owner=owner,
        disposition=disposition,
        disposition_rationale=disposition_rationale,
        dispute_state=dispute_state,
        recurrence_posture=recurrence_posture,
        review_evidence_references=review_evidence_references,
        source_signal_handling=source_signal_handling,
        lifecycle_state=lifecycle_state,
    )


def _suppression_proposal_record(
    *,
    suppression_proposal_id: str = "suppression-proposal-001",
    detector_lifecycle_id: str = "det-001",
    source_family: str = "github_audit",
    source_catalog_entry: str = "docs/source-families/github-audit/onboarding-package.md",
    alert_id: str | None = "alert-001",
    case_id: str | None = "case-001",
    evidence_ids: tuple[str, ...] = ("evidence-001",),
    owner: str = "suppression-owner",
    rationale: str = "Reviewed admin membership churn from approved break-glass rotation.",
    citation_references: tuple[str, ...] = ("evidence://case-001/change-ticket",),
    expires_at: datetime | None = datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc),
    review_cadence: str = "weekly",
    expected_signal_impact: str = "Reduce duplicate admin-membership alerts while preserving source signals.",
    scope: str = "detector_case_context",
    source_signal_handling: str = "preserve_source_signal",
    lifecycle_state: str = "proposed",
) -> SuppressionProposalRecord:
    return SuppressionProposalRecord(
        suppression_proposal_id=suppression_proposal_id,
        detector_lifecycle_id=detector_lifecycle_id,
        source_family=source_family,
        source_catalog_entry=source_catalog_entry,
        alert_id=alert_id,
        case_id=case_id,
        evidence_ids=evidence_ids,
        owner=owner,
        rationale=rationale,
        citation_references=citation_references,
        expires_at=expires_at,
        review_cadence=review_cadence,
        expected_signal_impact=expected_signal_impact,
        scope=scope,
        source_signal_handling=source_signal_handling,
        lifecycle_state=lifecycle_state,
    )


class Phase61DetectorLifecycleRecordContractTests(unittest.TestCase):
    def test_restore_validation_accepts_detector_lifecycle_transition_subjects(self) -> None:
        detector = _detector_lifecycle_record(lifecycle_state="candidate")
        transition = LifecycleTransitionRecord(
            transition_id="t-detector-candidate-001",
            subject_record_family="detector_lifecycle",
            subject_record_id=detector.detector_lifecycle_id,
            previous_lifecycle_state=None,
            lifecycle_state="candidate",
            transitioned_at=datetime.now(timezone.utc),
            attribution={},
        )
        boundary = RestoreValidationBoundary(
            authoritative_primary_id_field_by_family=_AUTHORITATIVE_PRIMARY_ID_FIELD_BY_FAMILY,
            find_duplicate_strings=lambda values: tuple(
                value
                for index, value in enumerate(values)
                if value in values[:index]
            ),
            assistant_ids_from_mapping=lambda _mapping, _field_name: (),
        )

        boundary.validate_authoritative_record_chain_restore(
            {
                "detector_lifecycle": (detector,),
                "lifecycle_transition": (transition,),
            },
            require_lifecycle_transition_history=True,
        )

    def test_restore_validation_rejects_detector_lifecycle_transition_skips(self) -> None:
        detector = _detector_lifecycle_record(lifecycle_state="active")
        candidate_transition = LifecycleTransitionRecord(
            transition_id="t-detector-candidate-001",
            subject_record_family="detector_lifecycle",
            subject_record_id=detector.detector_lifecycle_id,
            previous_lifecycle_state=None,
            lifecycle_state="candidate",
            transitioned_at=datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
            attribution={},
        )
        active_skip_transition = LifecycleTransitionRecord(
            transition_id="t-detector-active-skip-001",
            subject_record_family="detector_lifecycle",
            subject_record_id=detector.detector_lifecycle_id,
            previous_lifecycle_state="candidate",
            lifecycle_state="active",
            transitioned_at=datetime(2026, 1, 1, 0, 1, tzinfo=timezone.utc),
            attribution={},
        )
        boundary = RestoreValidationBoundary(
            authoritative_primary_id_field_by_family=_AUTHORITATIVE_PRIMARY_ID_FIELD_BY_FAMILY,
            find_duplicate_strings=lambda values: tuple(
                value
                for index, value in enumerate(values)
                if value in values[:index]
            ),
            assistant_ids_from_mapping=lambda _mapping, _field_name: (),
        )

        with self.assertRaisesRegex(
            ValueError,
            r"detector_lifecycle record transition from 'candidate' to 'active' is not supported",
        ):
            boundary.validate_authoritative_record_chain_restore(
                {
                    "detector_lifecycle": (detector,),
                    "lifecycle_transition": (
                        candidate_transition,
                        active_skip_transition,
                    ),
                },
                require_lifecycle_transition_history=True,
            )

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
            r"requires lifecycle_audit_references to be a tuple/list",
        ):
            _validate_record(
                _detector_lifecycle_record(
                    lifecycle_state="active",
                    lifecycle_audit_references="abc",  # type: ignore[arg-type]
                )
            )

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

        with self.assertRaisesRegex(
            ValueError,
            r"requires non-blank lifecycle_audit_references",
        ):
            _validate_record(
                _detector_lifecycle_record(
                    lifecycle_state="active",
                    lifecycle_audit_references=("   ",),
                )
            )

        with self.assertRaisesRegex(
            ValueError,
            r"requires non-blank lifecycle_audit_references",
        ):
            _validate_record(
                _detector_lifecycle_record(
                    lifecycle_state="active",
                    lifecycle_audit_references=(123,),  # type: ignore[arg-type]
                )
            )

    def test_detector_lifecycle_record_is_registered_in_service_registries(self) -> None:
        self.assertIn("detector_lifecycle", RECORD_TYPES_BY_FAMILY)
        self.assertIs(
            RECORD_TYPES_BY_FAMILY["detector_lifecycle"], DetectorLifecycleRecord
        )
        self.assertIn(
            DetectorLifecycleRecord,
            AUTHORITATIVE_RECORD_CHAIN_RECORD_TYPES,
        )
        self.assertEqual(
            _AUTHORITATIVE_PRIMARY_ID_FIELD_BY_FAMILY["detector_lifecycle"],
            "detector_lifecycle_id",
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

    def test_false_positive_review_records_cover_normal_disputed_and_repeated_cases(
        self,
    ) -> None:
        for record in (
            _false_positive_review_record(),
            _false_positive_review_record(
                false_positive_review_id="fp-review-disputed-001",
                disposition="needs_detector_tuning",
                dispute_state="disputed",
                lifecycle_state="disputed",
            ),
            _false_positive_review_record(
                false_positive_review_id="fp-review-repeated-001",
                disposition="recurring_benign_activity",
                recurrence_posture="recurring_reviewed_pattern",
                review_evidence_references=(
                    "evidence://case-001/admin-ticket",
                    "evidence://case-002/admin-ticket",
                ),
            ),
        ):
            _validate_record(record)

    def test_false_positive_review_rejects_missing_authoritative_links(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires non-blank detector_lifecycle_id"):
            _validate_record(
                _false_positive_review_record(detector_lifecycle_id="")
            )

        with self.assertRaisesRegex(ValueError, "requires at least one linkage field"):
            _validate_record(
                _false_positive_review_record(
                    alert_id=None,
                    case_id=None,
                    evidence_ids=(),
                )
            )

    def test_false_positive_review_rejects_non_collection_evidence_ids(self) -> None:
        for evidence_ids in ("evidence-001", 123):
            with self.subTest(evidence_ids=evidence_ids):
                record = _false_positive_review_record()
                object.__setattr__(record, "evidence_ids", evidence_ids)

                with self.assertRaisesRegex(
                    ValueError,
                    "requires evidence_ids to be a tuple/list",
                ):
                    _validate_record(record)

    def test_false_positive_review_rejects_uncited_or_silent_source_suppression(
        self,
    ) -> None:
        with self.assertRaisesRegex(ValueError, "requires non-blank owner"):
            _validate_record(_false_positive_review_record(owner=" "))

        with self.assertRaisesRegex(ValueError, "requires non-blank disposition_rationale"):
            _validate_record(_false_positive_review_record(disposition_rationale=""))

        with self.assertRaisesRegex(ValueError, "requires non-empty review_evidence_references"):
            _validate_record(
                _false_positive_review_record(review_evidence_references=())
            )

        with self.assertRaisesRegex(ValueError, "must preserve source signals"):
            _validate_record(
                _false_positive_review_record(source_signal_handling="delete_source_signal")
            )

    def test_false_positive_review_rejects_disputed_or_repeated_as_final_truth(
        self,
    ) -> None:
        with self.assertRaisesRegex(ValueError, "disputed reviews must use lifecycle_state 'disputed'"):
            _validate_record(
                _false_positive_review_record(
                    dispute_state="disputed",
                    lifecycle_state="reviewed",
                )
            )

        with self.assertRaisesRegex(ValueError, "repeated false positives require recurrence_posture"):
            _validate_record(
                _false_positive_review_record(
                    disposition="recurring_benign_activity",
                    recurrence_posture="single_reviewed_instance",
                )
            )

    def test_false_positive_review_record_is_registered_in_service_registries(self) -> None:
        self.assertIn("false_positive_review", RECORD_TYPES_BY_FAMILY)
        self.assertIs(
            RECORD_TYPES_BY_FAMILY["false_positive_review"],
            FalsePositiveReviewRecord,
        )
        self.assertIn(
            FalsePositiveReviewRecord,
            AUTHORITATIVE_RECORD_CHAIN_RECORD_TYPES,
        )
        self.assertEqual(
            _AUTHORITATIVE_PRIMARY_ID_FIELD_BY_FAMILY["false_positive_review"],
            "false_positive_review_id",
        )
        self.assertEqual(
            AUTHORITATIVE_RECORD_CHAIN_BACKUP_SCHEMA_VERSION,
            "phase23.authoritative-record-chain.v5",
        )

    def test_suppression_proposal_record_is_proposal_only_and_reviewable(self) -> None:
        _validate_record(_suppression_proposal_record())

        self.assertIn("suppression_proposal", RECORD_TYPES_BY_FAMILY)
        self.assertIs(
            RECORD_TYPES_BY_FAMILY["suppression_proposal"],
            SuppressionProposalRecord,
        )
        self.assertIn(
            SuppressionProposalRecord,
            AUTHORITATIVE_RECORD_CHAIN_RECORD_TYPES,
        )
        self.assertEqual(
            _AUTHORITATIVE_PRIMARY_ID_FIELD_BY_FAMILY["suppression_proposal"],
            "suppression_proposal_id",
        )

    def test_suppression_proposal_rejects_uncited_ownerless_or_silent_suppression(
        self,
    ) -> None:
        with self.assertRaisesRegex(ValueError, "requires non-blank owner"):
            _validate_record(_suppression_proposal_record(owner=" "))

        with self.assertRaisesRegex(ValueError, "requires non-empty citation_references"):
            _validate_record(_suppression_proposal_record(citation_references=()))

        with self.assertRaisesRegex(ValueError, "requires non-blank rationale"):
            _validate_record(_suppression_proposal_record(rationale=""))

        with self.assertRaisesRegex(ValueError, "must preserve source signals"):
            _validate_record(
                _suppression_proposal_record(source_signal_handling="hide_source_signal")
            )

    def test_suppression_proposal_rejects_overbroad_permanent_or_applied_suppression(
        self,
    ) -> None:
        with self.assertRaisesRegex(ValueError, "must set a finite expires_at"):
            _validate_record(_suppression_proposal_record(expires_at=None))

        with self.assertRaisesRegex(ValueError, "has invalid scope"):
            _validate_record(_suppression_proposal_record(scope="all_sources"))

        with self.assertRaisesRegex(ValueError, "has invalid lifecycle_state"):
            _validate_record(_suppression_proposal_record(lifecycle_state="applied"))

    def test_restore_validation_rejects_false_positive_review_without_detector_anchor(
        self,
    ) -> None:
        boundary = RestoreValidationBoundary(
            authoritative_primary_id_field_by_family=_AUTHORITATIVE_PRIMARY_ID_FIELD_BY_FAMILY,
            find_duplicate_strings=lambda values: tuple(
                value
                for index, value in enumerate(values)
                if value in values[:index]
            ),
            assistant_ids_from_mapping=lambda _mapping, _field_name: (),
        )

        with self.assertRaisesRegex(
            ValueError,
            "missing detector_lifecycle record 'det-001' required by false-positive review",
        ):
            boundary.validate_authoritative_record_chain_restore(
                {
                    "false_positive_review": (
                        _false_positive_review_record(
                            alert_id=None,
                            case_id=None,
                        ),
                    ),
                },
                require_lifecycle_transition_history=False,
            )

    def test_restore_validation_rejects_suppression_proposal_without_detector_anchor(
        self,
    ) -> None:
        boundary = RestoreValidationBoundary(
            authoritative_primary_id_field_by_family=_AUTHORITATIVE_PRIMARY_ID_FIELD_BY_FAMILY,
            find_duplicate_strings=lambda values: tuple(
                value
                for index, value in enumerate(values)
                if value in values[:index]
            ),
            assistant_ids_from_mapping=lambda _mapping, _field_name: (),
        )

        with self.assertRaisesRegex(
            ValueError,
            "missing detector_lifecycle record 'det-001' required by suppression proposal",
        ):
            boundary.validate_authoritative_record_chain_restore(
                {
                    "suppression_proposal": (
                        _suppression_proposal_record(
                            alert_id=None,
                            case_id=None,
                        ),
                    ),
                },
                require_lifecycle_transition_history=False,
            )
