from __future__ import annotations

import pathlib
import sys

TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

import _service_persistence_support as support

for name, value in vars(support).items():
    if not (name.startswith("__") and name.endswith("__")):
        globals()[name] = value


class ControlPlaneServiceHelperLayoutTests(unittest.TestCase):
    def test_service_defines_require_non_empty_string_once(self) -> None:
        source = inspect.getsource(AegisOpsControlPlaneService)
        self.assertEqual(source.count("def _require_non_empty_string("), 1)

    def test_persistence_regressions_are_split_into_domain_focused_modules(self) -> None:
        tests_root = pathlib.Path(__file__).resolve().parent
        regression_modules = sorted(
            {
                path.name
                for pattern in (
                    "test_service_persistence_*.py",
                    "test_service_readiness_*.py",
                    "test_service_restore_*.py",
                )
                for path in tests_root.glob(pattern)
                if path.name != "test_service_persistence_restore_readiness.py"
            }
        )

        self.assertEqual(
            regression_modules,
            [
                "test_service_persistence_action_reconciliation.py",
                "test_service_persistence_action_reconciliation_create_tracking_ticket.py",
                "test_service_persistence_action_reconciliation_delegation.py",
                "test_service_persistence_action_reconciliation_reconciliation.py",
                "test_service_persistence_action_reconciliation_review_surfaces.py",
                "test_service_persistence_action_reconciliation_reviewed_requests.py",
                "test_service_persistence_assistant_advisory.py",
                "test_service_persistence_ingest_case_lifecycle.py",
                "test_service_readiness_projection.py",
                "test_service_restore_backup_codec.py",
                "test_service_restore_drill_transactions.py",
                "test_service_restore_readiness_boundaries.py",
                "test_service_restore_runtime_visibility.py",
                "test_service_restore_validation.py",
            ],
        )


class AssistantContextHelperTests(unittest.TestCase):
    def test_reviewed_context_identifier_citations_skip_blank_and_null_values(
        self,
    ) -> None:
        citations = _reviewed_context_identifier_citations(
            {
                "identity": {
                    "identity_id": "   ",
                    "principal_id": "None",
                    "subject_id": None,
                },
                "asset": {
                    "asset_id": "asset-citation-001",
                },
            }
        )

        self.assertEqual(
            citations,
            ("reviewed_context.asset.asset_id=asset-citation-001",),
        )
