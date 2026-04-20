from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from typing import Mapping, Protocol

from .phase29_shadow_dataset import Phase29ShadowDatasetSnapshot

try:
    from mlflow.exceptions import MlflowException
except ImportError:  # pragma: no cover - mlflow is optional in unit-test environments.
    MlflowException = None


_REQUIRED_FEATURE_PROVENANCE_FIELDS = (
    "feature_source_record_family",
    "feature_source_record_id",
    "feature_source_field_path",
    "feature_extraction_spec_version",
    "feature_snapshot_timestamp",
    "feature_reviewed_linkage",
)
_REQUIRED_LABEL_PROVENANCE_FIELDS = (
    "label_record_family",
    "label_record_id",
    "label_field_path",
    "label_decision_basis",
    "label_decided_at",
    "label_linked_subject_record_id",
)
_MLFLOW_LOOKUP_EXCEPTIONS = tuple(
    exception_class
    for exception_class in (MlflowException,)
    if exception_class is not None
)


class MlflowRunInfo(Protocol):
    run_id: str


class MlflowRun(Protocol):
    info: MlflowRunInfo


class MlflowExperiment(Protocol):
    experiment_id: str


class MlflowModelVersion(Protocol):
    version: str


class Phase29MlflowClient(Protocol):
    def get_experiment_by_name(self, name: str) -> MlflowExperiment | None: ...

    def create_experiment(
        self,
        name: str,
        tags: Mapping[str, str] | None = None,
    ) -> str: ...

    def create_run(
        self,
        experiment_id: str,
        tags: Mapping[str, str] | None = None,
        run_name: str | None = None,
    ) -> MlflowRun: ...

    def log_param(self, run_id: str, key: str, value: object) -> None: ...

    def set_tag(self, run_id: str, key: str, value: object) -> None: ...

    def log_metric(
        self,
        run_id: str,
        key: str,
        value: float,
        timestamp: int | None = None,
        step: int = 0,
    ) -> None: ...

    def get_registered_model(self, name: str) -> object | None: ...

    def create_registered_model(
        self,
        name: str,
        tags: Mapping[str, str] | None = None,
        description: str | None = None,
    ) -> object: ...

    def create_model_version(
        self,
        name: str,
        source: str,
        run_id: str | None = None,
        tags: Mapping[str, str] | None = None,
        description: str | None = None,
    ) -> MlflowModelVersion: ...


class Phase29MlflowShadowModelRegistryError(ValueError):
    """Raised when shadow-model MLflow lineage cannot be justified explicitly."""


@dataclass(frozen=True)
class Phase29MlflowShadowModelTrackingResult:
    experiment_name: str
    run_id: str
    registered_model_name: str
    registered_model_version: str
    model_family: str
    model_version: str
    dataset_snapshot_id: str
    registry_posture: str


def track_shadow_model_with_mlflow(
    *,
    client: Phase29MlflowClient,
    dataset_snapshot: Phase29ShadowDatasetSnapshot,
    experiment_name: str,
    run_name: str,
    registered_model_name: str,
    model_source_uri: str,
    model_family: str,
    model_version: str,
    training_spec_version: str,
    feature_schema_version: str,
    label_schema_version: str,
    lineage_review_note_id: str,
    evaluation_metrics: Mapping[str, float],
    evaluation_metadata: Mapping[str, object],
    run_timestamp: datetime,
) -> Phase29MlflowShadowModelTrackingResult:
    if not isinstance(dataset_snapshot, Phase29ShadowDatasetSnapshot):
        raise TypeError("dataset_snapshot must be a Phase29ShadowDatasetSnapshot")
    if (
        not isinstance(run_timestamp, datetime)
        or run_timestamp.tzinfo is None
        or run_timestamp.utcoffset() is None
    ):
        raise ValueError("run_timestamp must be a timezone-aware datetime")

    experiment_name = _require_non_empty_string(experiment_name, "experiment_name")
    run_name = _require_non_empty_string(run_name, "run_name")
    registered_model_name = _require_non_empty_string(
        registered_model_name,
        "registered_model_name",
    )
    model_source_uri = _require_non_empty_string(model_source_uri, "model_source_uri")
    model_family = _require_non_empty_string(model_family, "model_family")
    model_version = _require_non_empty_string(model_version, "model_version")
    training_spec_version = _require_non_empty_string(
        training_spec_version,
        "training_spec_version",
    )
    feature_schema_version = _require_non_empty_string(
        feature_schema_version,
        "feature_schema_version",
    )
    label_schema_version = _require_non_empty_string(
        label_schema_version,
        "label_schema_version",
    )
    lineage_review_note_id = _require_non_empty_string(
        lineage_review_note_id,
        "lineage_review_note_id",
    )

    if dataset_snapshot.example_count <= 0 or not dataset_snapshot.examples:
        raise Phase29MlflowShadowModelRegistryError(
            "shadow model tracking requires at least one lineage-backed dataset example"
        )

    dataset_lineage_summary = _validate_shadow_dataset_lineage(dataset_snapshot)
    run_tags = {
        "aegisops.phase": "29",
        "aegisops.registry_posture": "shadow-only",
        "aegisops.authority_path": "outside-control-plane",
        "aegisops.lineage_review_note_id": lineage_review_note_id,
        "aegisops.model_family": model_family,
        "aegisops.model_version": model_version,
        "aegisops.training_data_snapshot_id": dataset_snapshot.snapshot_id,
    }
    experiment_id = _resolve_experiment_id(
        client=client,
        experiment_name=experiment_name,
        experiment_tags={
            "aegisops.phase": "29",
            "aegisops.registry_posture": "shadow-only",
            "aegisops.authority_path": "outside-control-plane",
        },
    )
    run = client.create_run(experiment_id, tags=run_tags, run_name=run_name)
    run_id = run.info.run_id

    run_params = {
        "training_data_snapshot_id": dataset_snapshot.snapshot_id,
        "dataset_extraction_spec_version": dataset_snapshot.extraction_spec_version,
        "training_spec_version": training_spec_version,
        "feature_schema_version": feature_schema_version,
        "label_schema_version": label_schema_version,
        "model_family": model_family,
        "model_version": model_version,
        "lineage_review_note_id": lineage_review_note_id,
        "dataset_example_count": dataset_snapshot.example_count,
        "tracked_source_families": ",".join(dataset_lineage_summary["source_families"]),
        "tracked_subject_record_families": ",".join(
            dataset_lineage_summary["subject_record_families"]
        ),
    }
    run_params.update(_stringify_mapping(evaluation_metadata))

    for key, value in sorted(run_params.items()):
        client.log_param(run_id, key, value)

    for metric_name, metric_value in sorted(evaluation_metrics.items()):
        _validate_metric_name(metric_name)
        client.log_metric(
            run_id,
            metric_name,
            _coerce_float(metric_name, metric_value),
            timestamp=int(run_timestamp.timestamp() * 1000),
            step=0,
        )

    for tag_key, tag_value in sorted(dataset_lineage_summary["tags"].items()):
        client.set_tag(run_id, tag_key, tag_value)

    _ensure_registered_model(
        client=client,
        registered_model_name=registered_model_name,
    )
    model_version_payload = client.create_model_version(
        registered_model_name,
        model_source_uri,
        run_id=run_id,
        tags={
            "aegisops.registry_posture": "shadow-only",
            "aegisops.authority_path": "outside-control-plane",
            "aegisops.training_data_snapshot_id": dataset_snapshot.snapshot_id,
            "aegisops.dataset_extraction_spec_version": dataset_snapshot.extraction_spec_version,
            "aegisops.feature_schema_version": feature_schema_version,
            "aegisops.label_schema_version": label_schema_version,
            "aegisops.training_spec_version": training_spec_version,
            "aegisops.model_family": model_family,
            "aegisops.model_version": model_version,
            "aegisops.lineage_review_note_id": lineage_review_note_id,
            **{
                f"aegisops.{key}": value
                for key, value in sorted(_stringify_mapping(evaluation_metadata).items())
            },
        },
        description=(
            "Phase 29 shadow-only candidate model. "
            "Non-authoritative registry entry outside the control-plane truth chain."
        ),
    )
    return Phase29MlflowShadowModelTrackingResult(
        experiment_name=experiment_name,
        run_id=run_id,
        registered_model_name=registered_model_name,
        registered_model_version=str(model_version_payload.version),
        model_family=model_family,
        model_version=model_version,
        dataset_snapshot_id=dataset_snapshot.snapshot_id,
        registry_posture="shadow-only",
    )


def _resolve_experiment_id(
    *,
    client: Phase29MlflowClient,
    experiment_name: str,
    experiment_tags: Mapping[str, str],
) -> str:
    experiment = client.get_experiment_by_name(experiment_name)
    if experiment is not None:
        return experiment.experiment_id
    return client.create_experiment(experiment_name, tags=experiment_tags)


def _ensure_registered_model(
    *,
    client: Phase29MlflowClient,
    registered_model_name: str,
) -> None:
    if _MLFLOW_LOOKUP_EXCEPTIONS:
        try:
            existing = client.get_registered_model(registered_model_name)
        except _MLFLOW_LOOKUP_EXCEPTIONS as exc:
            if not _is_missing_registered_model_lookup(exc, registered_model_name):
                raise
            existing = None
    else:
        existing = client.get_registered_model(registered_model_name)
    if existing is not None:
        return
    client.create_registered_model(
        registered_model_name,
        tags={
            "aegisops.registry_posture": "shadow-only",
            "aegisops.authority_path": "outside-control-plane",
        },
        description=(
            "Shadow-only candidate registry namespace for Phase 29 reviewed ML lineage. "
            "This registry does not confer control-plane authority."
        ),
    )


def _is_missing_registered_model_lookup(
    exc: Exception,
    registered_model_name: str,
) -> bool:
    error_code = getattr(exc, "error_code", None)
    if error_code == "RESOURCE_DOES_NOT_EXIST":
        return True

    message = str(exc).lower()
    registered_model_name = registered_model_name.lower()
    return (
        "registered model" in message
        and registered_model_name in message
        and ("not found" in message or "does not exist" in message)
    )


def _validate_shadow_dataset_lineage(
    dataset_snapshot: Phase29ShadowDatasetSnapshot,
) -> dict[str, object]:
    source_families: set[str] = set()
    subject_record_families: set[str] = set()
    linked_case_ids: set[str] = set()
    linked_alert_ids: set[str] = set()

    for example in dataset_snapshot.examples:
        if not isinstance(example, Mapping):
            raise Phase29MlflowShadowModelRegistryError(
                "dataset example must be a mapping with feature and label lineage"
            )
        subject_record_family = _require_non_empty_mapping_string(
            example,
            "subject_record_family",
        )
        _require_non_empty_mapping_string(example, "subject_record_id")
        linked_case_ids.add(_require_non_empty_mapping_string(example, "linked_case_id"))
        linked_alert_ids.add(_require_non_empty_mapping_string(example, "linked_alert_id"))
        subject_record_families.add(subject_record_family)

        features = example.get("features")
        if not isinstance(features, Mapping) or not features:
            raise Phase29MlflowShadowModelRegistryError(
                "dataset example must include at least one tracked feature"
            )
        for feature_name, feature_payload in features.items():
            if not isinstance(feature_payload, Mapping):
                raise Phase29MlflowShadowModelRegistryError(
                    f"feature {feature_name!r} must include provenance"
                )
            provenance = feature_payload.get("provenance")
            if not isinstance(provenance, Mapping):
                raise Phase29MlflowShadowModelRegistryError(
                    f"feature {feature_name!r} is missing required feature provenance"
                )
            _require_mapping_keys(
                provenance,
                _REQUIRED_FEATURE_PROVENANCE_FIELDS,
                "missing required feature provenance",
            )
            source_families.add(
                _require_non_empty_mapping_string(
                    provenance,
                    "feature_source_record_family",
                )
            )

        label = example.get("label")
        if not isinstance(label, Mapping):
            raise Phase29MlflowShadowModelRegistryError(
                "dataset example must include label lineage"
            )
        label_provenance = label.get("provenance")
        if not isinstance(label_provenance, Mapping):
            raise Phase29MlflowShadowModelRegistryError(
                "dataset example is missing required label provenance"
            )
        _require_mapping_keys(
            label_provenance,
            _REQUIRED_LABEL_PROVENANCE_FIELDS,
            "missing required label provenance",
        )

    return {
        "source_families": tuple(sorted(source_families)),
        "subject_record_families": tuple(sorted(subject_record_families)),
        "tags": {
            "aegisops.dataset_source_families": ",".join(sorted(source_families)),
            "aegisops.dataset_subject_record_families": ",".join(
                sorted(subject_record_families)
            ),
            "aegisops.linked_case_count": str(len(linked_case_ids)),
            "aegisops.linked_alert_count": str(len(linked_alert_ids)),
        },
    }


def _require_mapping_keys(
    mapping: Mapping[str, object],
    required_keys: tuple[str, ...],
    error_prefix: str,
) -> None:
    missing = [
        key
        for key in required_keys
        if _optional_string(mapping.get(key)) is None
    ]
    if missing:
        raise Phase29MlflowShadowModelRegistryError(
            f"{error_prefix}: {', '.join(missing)}"
        )


def _require_non_empty_mapping_string(
    mapping: Mapping[str, object],
    key: str,
) -> str:
    value = _optional_string(mapping.get(key))
    if value is None:
        raise Phase29MlflowShadowModelRegistryError(
            f"dataset lineage is missing required field {key}"
        )
    return value


def _require_non_empty_string(value: object, field_name: str) -> str:
    normalized = _optional_string(value)
    if normalized is None:
        raise Phase29MlflowShadowModelRegistryError(
            f"{field_name} must be a non-empty string"
        )
    return normalized


def _stringify_mapping(values: Mapping[str, object]) -> dict[str, str]:
    return {
        _normalize_param_key(key): _stringify_value(value)
        for key, value in values.items()
    }


def _normalize_param_key(key: object) -> str:
    normalized = _optional_string(key)
    if normalized is None:
        raise Phase29MlflowShadowModelRegistryError(
            "evaluation metadata keys must be non-empty strings"
        )
    return normalized


def _stringify_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, (str, int, float)):
        return str(value)
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise Phase29MlflowShadowModelRegistryError(
                "datetime metadata must be timezone-aware"
            )
        return value.isoformat()
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _validate_metric_name(metric_name: object) -> str:
    normalized = _optional_string(metric_name)
    if normalized is None:
        raise Phase29MlflowShadowModelRegistryError(
            "evaluation metric names must be non-empty strings"
        )
    return normalized


def _coerce_float(metric_name: str, metric_value: object) -> float:
    if isinstance(metric_value, bool):
        raise Phase29MlflowShadowModelRegistryError(
            f"evaluation metric {metric_name} must be numeric"
        )
    if not isinstance(metric_value, (int, float)):
        raise Phase29MlflowShadowModelRegistryError(
            f"evaluation metric {metric_name} must be numeric"
        )
    return float(metric_value)


def _optional_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped if stripped else None
