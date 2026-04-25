from __future__ import annotations

from urllib.parse import urlparse


_PLACEHOLDER_RECEIPT_VALUES = frozenset(
    (
        "<set-me>",
        "<todo>",
        "placeholder",
        "sample",
        "tbd",
        "todo",
    )
)


class MissingReceiptValueError(ValueError):
    def __init__(self, field_name: str) -> None:
        self.field_name = field_name
        super().__init__(
            f"adapter receipt missing required '{field_name}' attribute"
        )


def require_receipt_string_value(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise MissingReceiptValueError(field_name)

    normalized_value = value.strip()
    if (
        normalized_value == ""
        or normalized_value.lower() in _PLACEHOLDER_RECEIPT_VALUES
    ):
        raise MissingReceiptValueError(field_name)

    return value


def require_receipt_https_url_value(value: object, field_name: str) -> str:
    normalized_value = require_receipt_string_value(value, field_name).strip()
    parsed_value = urlparse(normalized_value)
    if parsed_value.scheme != "https" or not parsed_value.netloc:
        raise MissingReceiptValueError(field_name)
    return value
