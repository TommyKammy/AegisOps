from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Type, TypeVar

from .adapters.n8n import N8NReconciliationAdapter
from .adapters.opensearch import OpenSearchSignalAdapter
from .adapters.postgres import PostgresControlPlaneStore
from .config import RuntimeConfig
from .models import ControlPlaneRecord


RecordT = TypeVar("RecordT", bound=ControlPlaneRecord)


@dataclass(frozen=True)
class RuntimeSnapshot:
    service_name: str
    bind_host: str
    bind_port: int
    postgres_dsn: str
    persistence_mode: str
    opensearch_url: str
    n8n_base_url: str
    ownership_boundary: dict[str, str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class AegisOpsControlPlaneService:
    """Minimal local runtime skeleton for the first control-plane service."""

    def __init__(self, config: RuntimeConfig) -> None:
        self._config = config
        self._signal_intake = OpenSearchSignalAdapter(config.opensearch_url)
        self._store = PostgresControlPlaneStore(config.postgres_dsn)
        self._reconciliation = N8NReconciliationAdapter(config.n8n_base_url)

    def describe_runtime(self) -> RuntimeSnapshot:
        return RuntimeSnapshot(
            service_name="aegisops-control-plane",
            bind_host=self._config.host,
            bind_port=self._config.port,
            postgres_dsn=self._store.dsn,
            persistence_mode=self._store.persistence_mode,
            opensearch_url=self._signal_intake.base_url,
            n8n_base_url=self._reconciliation.base_url,
            ownership_boundary={
                "runtime_root": "control-plane/",
                "postgres_contract_root": "postgres/control-plane/",
                "signal_source": "opensearch/",
                "execution_plane": "n8n/",
            },
        )

    def persist_record(self, record: RecordT) -> RecordT:
        return self._store.save(record)

    def get_record(self, record_type: Type[RecordT], record_id: str) -> RecordT | None:
        return self._store.get(record_type, record_id)


def build_runtime_snapshot(environ: Mapping[str, str] | None = None) -> RuntimeSnapshot:
    config = RuntimeConfig.from_env(environ)
    service = AegisOpsControlPlaneService(config)
    return service.describe_runtime()
