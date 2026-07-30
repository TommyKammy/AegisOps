from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from http import client as http_client
import json
import socket
import ssl
from typing import Mapping, Protocol
from urllib import error, parse, request
from uuid import UUID

from .shuffle import ShuffleActionAdapter, ShuffleDelegationReceipt


_REVIEWED_ACTION_ID = "67f30000-0000-4000-8000-000000000011"
_REVIEWED_ACTION_NAME = "repeat_back_to_me"


class _RejectRedirectHandler(request.HTTPRedirectHandler):
    def redirect_request(
        self,
        req: request.Request,
        fp: object,
        code: int,
        msg: str,
        headers: object,
        newurl: str,
    ) -> None:
        del req, fp, code, msg, headers, newurl
        return None


class ShuffleTransportFailure(RuntimeError):
    def __init__(
        self,
        category: str,
        *,
        retryable: bool = False,
        transient: bool = False,
        outcome_unknown: bool = False,
    ) -> None:
        super().__init__(f"Shuffle transport failed: {category}")
        self.category = category
        self.retryable = retryable
        self.transient = transient
        self.outcome_unknown = outcome_unknown


def _json_values_equal(left: object, right: object) -> bool:
    try:
        return json.dumps(
            _json_ready(left),
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ) == json.dumps(
            _json_ready(right),
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError):
        return False


def _json_ready(value: object) -> object:
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise TypeError("JSON object keys must be strings")
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    return value


def _canonical_utc_datetime(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Shuffle delegated_at must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class ShuffleJsonTransport(Protocol):
    def request_json(
        self,
        *,
        method: str,
        url: str,
        api_key: str,
        payload: Mapping[str, object] | None,
        timeout_seconds: float,
    ) -> object:
        """Send one authenticated request without exposing the credential."""


@dataclass(frozen=True)
class UrllibShuffleJsonTransport:
    ca_file: str

    def __post_init__(self) -> None:
        if not isinstance(self.ca_file, str) or self.ca_file.strip() == "":
            raise ValueError("real Shuffle transport requires an explicit CA file")
        object.__setattr__(self, "ca_file", self.ca_file.strip())

    def request_json(
        self,
        *,
        method: str,
        url: str,
        api_key: str,
        payload: Mapping[str, object] | None,
        timeout_seconds: float,
    ) -> object:
        body = None
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        if payload is not None:
            body = json.dumps(
                payload,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
            headers["Content-Type"] = "application/json"
        shuffle_request = request.Request(
            url,
            data=body,
            headers=headers,
            method=method,
        )
        context = ssl.create_default_context(cafile=self.ca_file)
        opener = request.build_opener(
            request.HTTPSHandler(context=context),
            _RejectRedirectHandler(),
        )
        try:
            with opener.open(  # noqa: S310
                shuffle_request,
                timeout=timeout_seconds,
            ) as response:
                content_type = response.headers.get_content_type()
                if content_type != "application/json":
                    raise ShuffleTransportFailure(
                        "invalid_content_type",
                        outcome_unknown=method == "POST",
                    )
                response_body = response.read(1_048_577)
                if len(response_body) > 1_048_576:
                    raise ShuffleTransportFailure(
                        "response_too_large",
                        outcome_unknown=method == "POST",
                    )
        except error.HTTPError as exc:
            category = (
                "redirect_rejected"
                if 300 <= exc.code <= 399
                else "authentication_rejected"
                if exc.code in {401, 403}
                else "workflow_not_found"
                if exc.code == 404
                else f"http_{exc.code}"
            )
            transient = 500 <= exc.code <= 599
            raise ShuffleTransportFailure(
                category,
                transient=transient,
                outcome_unknown=method == "POST"
                and (transient or category == "redirect_rejected"),
            ) from exc
        except TimeoutError as exc:
            raise ShuffleTransportFailure(
                "timeout",
                transient=True,
                outcome_unknown=method == "POST",
            ) from exc
        except http_client.HTTPException as exc:
            raise ShuffleTransportFailure(
                "invalid_http_response",
                transient=True,
                outcome_unknown=method == "POST",
            ) from exc
        except error.URLError as exc:
            retryable = isinstance(exc.reason, (ConnectionRefusedError, socket.gaierror))
            transient = isinstance(
                exc.reason,
                (ConnectionError, TimeoutError, socket.gaierror),
            )
            category = (
                "connection_not_established" if retryable else "connection_failure"
            )
            raise ShuffleTransportFailure(
                category,
                retryable=retryable,
                transient=transient,
                outcome_unknown=method == "POST" and transient and not retryable,
            ) from exc
        except OSError as exc:
            retryable = isinstance(exc, (ConnectionRefusedError, socket.gaierror))
            transient = isinstance(
                exc,
                (ConnectionError, TimeoutError, socket.gaierror),
            )
            category = (
                "connection_not_established" if retryable else "connection_failure"
            )
            raise ShuffleTransportFailure(
                category,
                retryable=retryable,
                transient=transient,
                outcome_unknown=method == "POST" and transient and not retryable,
            ) from exc
        try:
            return json.loads(response_body)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ShuffleTransportFailure(
                "malformed_json",
                outcome_unknown=method == "POST",
            ) from exc


def _require_non_empty_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or value.strip() == "":
        raise ValueError(f"Shuffle {field_name} must be a non-empty string")
    return value.strip()


def _require_real_identifier(value: object, field_name: str) -> str:
    identifier = _require_non_empty_string(value, field_name)
    if identifier.startswith(("shuffle-run-", "shuffle-receipt-")):
        raise ValueError(f"Shuffle {field_name} must be a real identifier")
    return identifier


def _require_real_execution_id(value: object) -> str:
    identifier = _require_real_identifier(value, "execution id")
    try:
        parsed = UUID(identifier)
    except ValueError as exc:
        raise ValueError("Shuffle execution id must be a UUID") from exc
    if str(parsed) != identifier.lower():
        raise ValueError("Shuffle execution id must use canonical UUID form")
    return identifier.lower()


def _require_api_workflow_id(value: str) -> str:
    try:
        parsed = UUID(value)
    except ValueError as exc:
        raise ValueError("Shuffle API workflow id must be a UUID") from exc
    if str(parsed) != value.lower():
        raise ValueError("Shuffle API workflow id must use canonical UUID form")
    return value.lower()


def _require_https_base_url(value: str) -> str:
    normalized = value.strip().rstrip("/")
    parsed = parse.urlsplit(normalized)
    if parsed.scheme != "https" or parsed.netloc == "":
        raise ValueError("real Shuffle transport requires an HTTPS base URL")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("Shuffle base URL must not contain userinfo")
    if parsed.query or parsed.fragment:
        raise ValueError("Shuffle base URL must not include a query or fragment")
    return normalized


@dataclass(frozen=True)
class RealShuffleActionAdapter:
    base_url: str
    api_key: str = field(repr=False)
    api_workflow_id: str
    transport: ShuffleJsonTransport
    timeout_seconds: float = 10.0
    max_attempts: int = 2
    execution_surface_type: str = "automation_substrate"
    execution_surface_id: str = "shuffle"

    def __post_init__(self) -> None:
        object.__setattr__(self, "base_url", _require_https_base_url(self.base_url))
        object.__setattr__(
            self,
            "api_workflow_id",
            _require_api_workflow_id(self.api_workflow_id),
        )
        _require_non_empty_string(self.api_key, "API key")
        if self.timeout_seconds <= 0:
            raise ValueError("Shuffle timeout must be positive")
        if self.max_attempts not in {1, 2}:
            raise ValueError("Shuffle dispatch attempts must be one or two")

    def dispatch_approved_action(
        self,
        *,
        delegation_id: str,
        action_request_id: str,
        approval_decision_id: str,
        payload_hash: str,
        idempotency_key: str,
        approved_payload: Mapping[str, object],
        delegated_at: datetime,
    ) -> ShuffleDelegationReceipt:
        execution_argument = self._reviewed_execution_argument(
            delegation_id=delegation_id,
            action_request_id=action_request_id,
            approval_decision_id=approval_decision_id,
            payload_hash=payload_hash,
            idempotency_key=idempotency_key,
            approved_payload=approved_payload,
            delegated_at=delegated_at,
        )
        request_payload = {
            "execution_argument": json.dumps(
                execution_argument,
                separators=(",", ":"),
                sort_keys=True,
            ),
            "execution_source": "aegisops_phase67_lab",
        }
        endpoint = (
            f"{self.base_url}/api/v1/workflows/{self.api_workflow_id}/execute"
        )
        response: object | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                response = self.transport.request_json(
                    method="POST",
                    url=endpoint,
                    api_key=self.api_key,
                    payload=request_payload,
                    timeout_seconds=self.timeout_seconds,
                )
                break
            except ShuffleTransportFailure as exc:
                if not exc.retryable or attempt == self.max_attempts:
                    raise
        if not isinstance(response, Mapping):
            raise ShuffleTransportFailure(
                "malformed_dispatch_response",
                outcome_unknown=True,
            )
        if response.get("success") is not True:
            raise ShuffleTransportFailure("dispatch_rejected")
        try:
            execution_id = _require_real_execution_id(response.get("execution_id"))
        except ValueError as exc:
            raise ShuffleTransportFailure(
                "malformed_dispatch_response",
                outcome_unknown=True,
            ) from exc
        return self._delegation_receipt(
            execution_id=execution_id,
            execution_argument=execution_argument,
        )

    def recover_interrupted_dispatch(
        self,
        *,
        delegation_id: str,
        action_request_id: str,
        approval_decision_id: str,
        payload_hash: str,
        idempotency_key: str,
        approved_payload: Mapping[str, object],
        delegated_at: datetime,
    ) -> ShuffleDelegationReceipt:
        expected_argument = self._reviewed_execution_argument(
            delegation_id=delegation_id,
            action_request_id=action_request_id,
            approval_decision_id=approval_decision_id,
            payload_hash=payload_hash,
            idempotency_key=idempotency_key,
            approved_payload=approved_payload,
            delegated_at=delegated_at,
        )
        response = self.transport.request_json(
            method="GET",
            url=(
                f"{self.base_url}/api/v1/workflows/"
                f"{self.api_workflow_id}/executions"
            ),
            api_key=self.api_key,
            payload=None,
            timeout_seconds=self.timeout_seconds,
        )
        raw_executions = (
            response.get("executions")
            if isinstance(response, Mapping)
            else response
        )
        if not isinstance(raw_executions, list):
            raise ShuffleTransportFailure("malformed_receipt_collection")

        matches: list[tuple[Mapping[str, object], Mapping[str, object]]] = []
        for execution in raw_executions:
            if not isinstance(execution, Mapping):
                continue
            argument = self._decode_execution_argument(
                execution.get("execution_argument")
            )
            if (
                argument is not None
                and argument.get("idempotency_key") == idempotency_key
            ):
                matches.append((execution, argument))
        if not matches:
            raise ShuffleTransportFailure("interrupted_dispatch_not_observed")
        if len(matches) != 1:
            raise ShuffleTransportFailure("duplicate_idempotency_execution")

        execution, observed_argument = matches[0]
        if not _json_values_equal(observed_argument, expected_argument):
            raise ShuffleTransportFailure(
                "interrupted_dispatch_binding_mismatch"
            )
        execution_id = _require_real_execution_id(
            execution.get("execution_id")
        )
        return self._delegation_receipt(
            execution_id=execution_id,
            execution_argument=expected_argument,
        )

    @staticmethod
    def _decode_execution_argument(
        value: object,
    ) -> Mapping[str, object] | None:
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                return None
        return value if isinstance(value, Mapping) else None

    @staticmethod
    def _reviewed_execution_argument(
        *,
        delegation_id: str,
        action_request_id: str,
        approval_decision_id: str,
        payload_hash: str,
        idempotency_key: str,
        approved_payload: Mapping[str, object],
        delegated_at: datetime,
    ) -> dict[str, object]:
        binding = approved_payload.get("shuffle_delegation_binding")
        if not isinstance(binding, Mapping):
            raise ValueError(
                "real Shuffle dispatch requires an explicit reviewed delegation binding"
            )
        ShuffleActionAdapter._require_reviewed_phase20_notify_payload(approved_payload)
        workflow_id = _require_non_empty_string(binding.get("workflow_id"), "workflow id")
        workflow_version_id = _require_non_empty_string(
            binding.get("workflow_version_id"),
            "workflow version id",
        )
        correlation_id = _require_non_empty_string(
            binding.get("correlation_id"),
            "correlation id",
        )
        expected_receipt_id = _require_real_identifier(
            binding.get("expected_execution_receipt_id"),
            "expected receipt id",
        )
        requested_scope = binding.get("requested_scope")
        if not isinstance(requested_scope, Mapping):
            raise ValueError("Shuffle requested scope must be a mapping")

        return {
            "action_request_id": action_request_id,
            "approval_decision_id": approval_decision_id,
            "delegation_id": delegation_id,
            "payload_hash": payload_hash,
            "idempotency_key": idempotency_key,
            "workflow_id": workflow_id,
            "workflow_version_id": workflow_version_id,
            "correlation_id": correlation_id,
            "expected_execution_receipt_id": expected_receipt_id,
            "requested_scope": dict(requested_scope),
            "delegated_at": _canonical_utc_datetime(delegated_at),
            "action": {
                "action_type": approved_payload["action_type"],
                "recipient_identity": approved_payload["recipient_identity"],
                "message_intent": approved_payload["message_intent"],
                "escalation_reason": approved_payload["escalation_reason"],
            },
        }

    def _delegation_receipt(
        self,
        *,
        execution_id: str,
        execution_argument: Mapping[str, object],
    ) -> ShuffleDelegationReceipt:
        return ShuffleDelegationReceipt(
            execution_surface_type=self.execution_surface_type,
            execution_surface_id=self.execution_surface_id,
            execution_run_id=execution_id,
            action_request_id=str(execution_argument["action_request_id"]),
            approval_decision_id=str(
                execution_argument["approval_decision_id"]
            ),
            delegation_id=str(execution_argument["delegation_id"]),
            payload_hash=str(execution_argument["payload_hash"]),
            adapter="shuffle_real_http",
            base_url=self.base_url,
            workflow_id=str(execution_argument["workflow_id"]),
            workflow_version_id=str(
                execution_argument["workflow_version_id"]
            ),
            correlation_id=str(execution_argument["correlation_id"]),
            expected_execution_receipt_id=str(
                execution_argument["expected_execution_receipt_id"]
            ),
            requested_scope=dict(execution_argument["requested_scope"]),
            external_receipt_id=str(
                execution_argument["expected_execution_receipt_id"]
            ),
        )


@dataclass(frozen=True)
class ShuffleReceiptPollingClient:
    base_url: str
    api_key: str = field(repr=False)
    api_workflow_id: str
    transport: ShuffleJsonTransport
    timeout_seconds: float = 10.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "base_url", _require_https_base_url(self.base_url))
        object.__setattr__(
            self,
            "api_workflow_id",
            _require_api_workflow_id(self.api_workflow_id),
        )
        _require_non_empty_string(self.api_key, "API key")
        if self.timeout_seconds <= 0:
            raise ValueError("Shuffle timeout must be positive")

    def poll_normalized_receipt(
        self,
        *,
        execution_id: str,
        idempotency_key: str,
        expected_binding: Mapping[str, object],
        observed_at: datetime,
    ) -> Mapping[str, object]:
        execution_id = _require_real_execution_id(execution_id)
        response = self.transport.request_json(
            method="GET",
            url=(
                f"{self.base_url}/api/v1/workflows/"
                f"{self.api_workflow_id}/executions"
            ),
            api_key=self.api_key,
            payload=None,
            timeout_seconds=self.timeout_seconds,
        )
        raw_executions: object
        if isinstance(response, Mapping):
            raw_executions = response.get("executions")
        else:
            raw_executions = response
        if not isinstance(raw_executions, list):
            raise ShuffleTransportFailure("malformed_receipt_collection")
        matching = []
        for item in raw_executions:
            if not isinstance(item, Mapping):
                continue
            try:
                observed_execution_id = _require_real_execution_id(
                    item.get("execution_id")
                )
            except ValueError:
                continue
            if observed_execution_id == execution_id:
                matching.append(item)
        if len(matching) != 1:
            category = "missing_receipt" if not matching else "duplicate_receipt"
            raise ShuffleTransportFailure(category)
        execution = matching[0]
        argument = execution.get("execution_argument")
        if isinstance(argument, str):
            try:
                argument = json.loads(argument)
            except json.JSONDecodeError as exc:
                raise ShuffleTransportFailure("malformed_receipt") from exc
        if not isinstance(argument, Mapping):
            raise ShuffleTransportFailure("malformed_receipt")

        required_binding_fields = (
            "action_request_id",
            "approval_decision_id",
            "delegation_id",
            "payload_hash",
            "workflow_id",
            "workflow_version_id",
            "correlation_id",
            "expected_execution_receipt_id",
        )
        for field_name in required_binding_fields:
            expected_value = expected_binding.get(field_name)
            if (
                not isinstance(expected_value, str)
                or expected_value.strip() == ""
                or argument.get(field_name) != expected_value
            ):
                raise ShuffleTransportFailure(f"{field_name}_mismatch")
        if argument.get("idempotency_key") != idempotency_key:
            raise ShuffleTransportFailure("idempotency_key_mismatch")
        idempotency_matches = 0
        for item in raw_executions:
            if not isinstance(item, Mapping):
                continue
            item_argument = item.get("execution_argument")
            if isinstance(item_argument, str):
                try:
                    item_argument = json.loads(item_argument)
                except json.JSONDecodeError:
                    continue
            if (
                isinstance(item_argument, Mapping)
                and item_argument.get("idempotency_key") == idempotency_key
            ):
                idempotency_matches += 1
        if idempotency_matches != 1:
            raise ShuffleTransportFailure("duplicate_idempotency_execution")
        expected_scope = expected_binding.get("requested_scope")
        if not isinstance(expected_scope, Mapping):
            raise ShuffleTransportFailure("requested_scope_malformed")
        if not _json_values_equal(
            argument.get("requested_scope"),
            expected_scope,
        ):
            raise ShuffleTransportFailure("requested_scope_mismatch")
        expected_argument = dict(expected_binding)
        expected_argument["idempotency_key"] = idempotency_key
        if not _json_values_equal(argument, expected_argument):
            raise ShuffleTransportFailure("execution_argument_mismatch")

        status = self._normalize_status(execution.get("status"))
        if status == "success" and not self._reviewed_action_succeeded(execution):
            status = "failed"
        return {
            "execution_surface_type": self.execution_surface_type,
            "execution_surface_id": self.execution_surface_id,
            "execution_run_id": execution_id,
            "idempotency_key": idempotency_key,
            "observed_at": observed_at,
            "status": status,
            "requested_scope": dict(expected_scope),
            "idempotency_execution_count": idempotency_matches,
            **{
                field_name: argument[field_name]
                for field_name in required_binding_fields
            },
            "external_receipt_id": argument["expected_execution_receipt_id"],
        }

    execution_surface_type: str = "automation_substrate"
    execution_surface_id: str = "shuffle"

    @staticmethod
    def _reviewed_action_succeeded(execution: Mapping[str, object]) -> bool:
        results = execution.get("results")
        if (
            not isinstance(results, list)
            or len(results) != 1
            or not isinstance(results[0], Mapping)
        ):
            raise ShuffleTransportFailure("malformed_reviewed_action_result")
        result = results[0]
        action = result.get("action")
        if (
            not isinstance(action, Mapping)
            or action.get("id") != _REVIEWED_ACTION_ID
            or action.get("name") != _REVIEWED_ACTION_NAME
        ):
            raise ShuffleTransportFailure("reviewed_action_result_mismatch")
        result_status = result.get("status")
        if not isinstance(result_status, str) or result_status.strip() == "":
            raise ShuffleTransportFailure("malformed_reviewed_action_result")
        return result_status.strip().upper() == "SUCCESS"

    @staticmethod
    def _normalize_status(value: object) -> str:
        status = _require_non_empty_string(value, "execution status").upper()
        if status in {"EXECUTING", "RUNNING", "WAITING"}:
            return "running"
        if status in {"FINISHED", "COMPLETED", "SUCCESS"}:
            return "success"
        if status in {"ABORTED", "FAILURE", "FAILED"}:
            return "failed"
        raise ShuffleTransportFailure("unknown_execution_status")
