"""Adapter placeholders for the first control-plane service boundary."""

from .executor import IsolatedExecutorAdapter
from .n8n import N8NReconciliationAdapter
from .opensearch import OpenSearchSignalAdapter
from .postgres import PostgresControlPlaneStore
from .shuffle import ShuffleActionAdapter
from .shuffle_real import RealShuffleActionAdapter, ShuffleReceiptPollingClient
from .wazuh import WazuhAlertAdapter

__all__ = [
    "IsolatedExecutorAdapter",
    "N8NReconciliationAdapter",
    "OpenSearchSignalAdapter",
    "PostgresControlPlaneStore",
    "ShuffleActionAdapter",
    "RealShuffleActionAdapter",
    "ShuffleReceiptPollingClient",
    "WazuhAlertAdapter",
]
