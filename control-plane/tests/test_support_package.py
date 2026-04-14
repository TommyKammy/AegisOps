from __future__ import annotations

from contextlib import contextmanager
import pathlib
import sys
import threading
import time
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

    def test_transaction_mutation_store_consumes_mutation_token_once(self) -> None:
        from support.fake_store import TransactionMutationStore

        store = TransactionMutationStore(
            inner=_NoOpStore(),
            mutate_once=_BlockingMutation(),
        )

        self._run_transaction_threads(store)

        self.assertEqual(store.mutate_once.calls, 1)

    def test_concurrent_list_mutation_store_consumes_mutation_token_once(self) -> None:
        from support.fake_store import ConcurrentListMutationStore

        mutation = _BlockingMutation()
        store = ConcurrentListMutationStore(
            inner=_NoOpStore(),
            mutate_once=mutation,
        )

        first_thread = threading.Thread(
            target=store.list,
            args=(object,),
        )
        first_thread.start()
        self.assertTrue(mutation.started.wait(timeout=1))

        second_thread = threading.Thread(
            target=store.inspect_readiness_aggregates,
        )
        second_thread.start()

        time.sleep(0.05)
        mutation.release.set()
        first_thread.join(timeout=1)
        second_thread.join(timeout=1)

        self.assertFalse(first_thread.is_alive())
        self.assertFalse(second_thread.is_alive())
        self.assertEqual(mutation.calls, 1)

    def test_out_of_band_mutation_store_consumes_mutation_token_once(self) -> None:
        from support.fake_store import OutOfBandMutationStore

        store = OutOfBandMutationStore(
            inner=_NoOpStore(),
            mutate_once=_BlockingMutation(),
        )

        self._run_transaction_threads(store)

        self.assertEqual(store.mutate_once.calls, 1)

    def _run_transaction_threads(self, store: object) -> None:
        first_thread = threading.Thread(target=self._run_transaction, args=(store,))
        first_thread.start()
        self.assertTrue(store.mutate_once.started.wait(timeout=1))

        second_thread = threading.Thread(target=self._run_transaction, args=(store,))
        second_thread.start()

        time.sleep(0.05)
        store.mutate_once.release.set()
        first_thread.join(timeout=1)
        second_thread.join(timeout=1)

        self.assertFalse(first_thread.is_alive())
        self.assertFalse(second_thread.is_alive())

    @staticmethod
    def _run_transaction(store: object) -> None:
        with store.transaction():
            return


class _BlockingMutation:
    def __init__(self) -> None:
        self.calls = 0
        self.started = threading.Event()
        self.release = threading.Event()
        self._lock = threading.Lock()

    def __call__(self, *_args: object) -> None:
        with self._lock:
            self.calls += 1
        self.started.set()
        self.release.wait(timeout=1)


class _NoOpStore:
    dsn = "sqlite://:memory:"
    persistence_mode = "test"

    def save(self, record: object) -> object:
        return record

    def get(self, record_type: object, record_id: str) -> None:
        return None

    def list(self, record_type: object) -> tuple[object, ...]:
        return ()

    def inspect_readiness_aggregates(self) -> dict[str, object]:
        return {}

    @contextmanager
    def transaction(self, *, isolation_level: str | None = None):
        del isolation_level
        yield
