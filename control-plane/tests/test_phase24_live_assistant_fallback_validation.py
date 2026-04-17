from __future__ import annotations

import pathlib
import sys


TESTS_ROOT = pathlib.Path(__file__).resolve().parent
CONTROL_PLANE_ROOT = TESTS_ROOT.parents[0]
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from _service_persistence_support import (
    ServicePersistenceTestBase,
    mock,
    replace,
)


class Phase24LiveAssistantFallbackValidationTests(ServicePersistenceTestBase):
    def test_workflow_preserves_reviewed_unresolved_summary_for_missing_citations(
        self,
    ) -> None:
        _, service, promoted_case, _, _ = self._build_phase19_in_scope_case()
        context_snapshot = service.inspect_assistant_context(
            "case",
            promoted_case.case_id,
        )
        expected_summary = "Reviewed case summary remains unresolved until citations are restored."
        unresolved_context = replace(
            context_snapshot,
            advisory_output={
                **dict(context_snapshot.advisory_output),
                "status": "unresolved",
                "cited_summary": {
                    "text": expected_summary,
                    "citations": (promoted_case.case_id,),
                },
                "uncertainty_flags": ("missing_supporting_citations",),
            },
        )
        service._assistant_provider_adapter = mock.Mock()

        with mock.patch.object(
            service,
            "inspect_assistant_context",
            return_value=unresolved_context,
        ):
            snapshot = service.run_live_assistant_workflow(
                workflow_task="case_summary",
                record_family="case",
                record_id=promoted_case.case_id,
            )

        self.assertEqual(snapshot.status, "unresolved")
        self.assertEqual(snapshot.summary, expected_summary)
        self.assertEqual(
            snapshot.unresolved_reasons,
            ("required citations are missing",),
        )
        service._assistant_provider_adapter.generate.assert_not_called()

    def test_workflow_preserves_reviewed_unresolved_summary_for_ambiguity(
        self,
    ) -> None:
        _, service, promoted_case, _, _ = self._build_phase19_in_scope_case()
        case_record = service.get_record(type(promoted_case), promoted_case.case_id)
        assert case_record is not None
        service.persist_record(
            replace(
                case_record,
                reviewed_context={
                    **dict(case_record.reviewed_context),
                    "identity": {"aliases": ("svc-prod-shared",)},
                },
            )
        )
        expected_summary = service.inspect_assistant_context(
            "case",
            promoted_case.case_id,
        ).advisory_output["cited_summary"]["text"]
        service._assistant_provider_adapter = mock.Mock()

        snapshot = service.run_live_assistant_workflow(
            workflow_task="case_summary",
            record_family="case",
            record_id=promoted_case.case_id,
        )

        self.assertEqual(snapshot.status, "unresolved")
        self.assertEqual(snapshot.summary, expected_summary)
        self.assertEqual(
            snapshot.unresolved_reasons,
            (
                "the requested summary would require the assistant to collapse identity ambiguity",
            ),
        )
        service._assistant_provider_adapter.generate.assert_not_called()

    def test_workflow_preserves_reviewed_unresolved_summary_for_conflicting_context(
        self,
    ) -> None:
        _, service, promoted_case, _, _ = self._build_phase19_in_scope_case()
        context_snapshot = service.inspect_assistant_context(
            "case",
            promoted_case.case_id,
        )
        expected_summary = (
            "Reviewed case summary remains unresolved until conflicting reviewed context is reconciled."
        )
        unresolved_context = replace(
            context_snapshot,
            advisory_output={
                **dict(context_snapshot.advisory_output),
                "status": "unresolved",
                "cited_summary": {
                    "text": expected_summary,
                    "citations": (promoted_case.case_id,),
                },
                "uncertainty_flags": ("conflicting_reviewed_context",),
            },
        )
        service._assistant_provider_adapter = mock.Mock()

        with mock.patch.object(
            service,
            "inspect_assistant_context",
            return_value=unresolved_context,
        ):
            snapshot = service.run_live_assistant_workflow(
                workflow_task="case_summary",
                record_family="case",
                record_id=promoted_case.case_id,
            )

        self.assertEqual(snapshot.status, "unresolved")
        self.assertEqual(snapshot.summary, expected_summary)
        self.assertEqual(
            snapshot.unresolved_reasons,
            (
                "reviewed records conflict on lifecycle state, ownership, scope, or evidence-backed facts",
            ),
        )
        service._assistant_provider_adapter.generate.assert_not_called()

    def test_workflow_preserves_reviewed_summary_for_provider_failure(
        self,
    ) -> None:
        _, service, promoted_case, _, _ = self._build_phase19_in_scope_case()
        expected_summary = service.inspect_assistant_context(
            "case",
            promoted_case.case_id,
        ).advisory_output["cited_summary"]["text"]
        service._assistant_provider_adapter = mock.Mock()
        service._assistant_provider_adapter.generate.side_effect = RuntimeError(
            "provider transport failed"
        )

        snapshot = service.run_live_assistant_workflow(
            workflow_task="case_summary",
            record_family="case",
            record_id=promoted_case.case_id,
        )

        self.assertEqual(snapshot.status, "unresolved")
        self.assertEqual(snapshot.summary, expected_summary)
        self.assertEqual(
            snapshot.unresolved_reasons,
            (
                "the bounded live assistant did not return a trusted summary within the reviewed retry budget",
            ),
        )
        service._assistant_provider_adapter.generate.assert_called_once()


if __name__ == "__main__":
    import unittest

    unittest.main()
