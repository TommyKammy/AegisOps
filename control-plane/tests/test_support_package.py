from __future__ import annotations

import pathlib
import sys
import unittest


TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))


class ControlPlaneTestSupportPackageTests(unittest.TestCase):
    def test_support_package_exposes_shared_control_plane_test_helpers(self) -> None:
        from support.auth import (
            REVIEWED_ANALYST_PRINCIPAL,
            REVIEWED_PLATFORM_ADMIN_PRINCIPAL,
            REVIEWED_PROXY_SERVICE_ACCOUNT,
        )
        from support.fake_store import (
            CommitFailingStore,
            ConcurrentListMutationStore,
            ListCountingStore,
            OutOfBandMutationStore,
            RecordTypeSaveFailingStore,
            TransactionMutationStore,
        )
        from support.fixtures import load_wazuh_fixture
        from support.payloads import (
            approved_binding_hash,
            phase20_notify_identity_owner_payload,
        )

        self.assertEqual(
            REVIEWED_PROXY_SERVICE_ACCOUNT,
            "svc-aegisops-proxy-control-plane",
        )
        self.assertEqual(REVIEWED_ANALYST_PRINCIPAL.identity, "analyst-001")
        self.assertEqual(
            REVIEWED_PLATFORM_ADMIN_PRINCIPAL.identity,
            "platform-admin-001",
        )
        self.assertTrue(callable(load_wazuh_fixture))
        self.assertTrue(callable(phase20_notify_identity_owner_payload))
        self.assertTrue(callable(approved_binding_hash))
        self.assertTrue(issubclass(TransactionMutationStore, object))
        self.assertTrue(issubclass(ConcurrentListMutationStore, object))
        self.assertTrue(issubclass(CommitFailingStore, object))
        self.assertTrue(issubclass(RecordTypeSaveFailingStore, object))
        self.assertTrue(issubclass(ListCountingStore, object))
        self.assertTrue(issubclass(OutOfBandMutationStore, object))

