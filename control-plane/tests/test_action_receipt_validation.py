from __future__ import annotations
# ruff: noqa: E402

import pathlib
import sys
import unittest


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from aegisops_control_plane.action_receipt_validation import (
    MissingReceiptValueError,
    require_receipt_https_url_value,
)


class ActionReceiptValidationTests(unittest.TestCase):
    def test_https_url_value_returns_normalized_url_without_surrounding_whitespace(
        self,
    ) -> None:
        self.assertEqual(
            require_receipt_https_url_value(
                " https://tickets.example.test/#ticket/4242 ",
                "ticket_reference_url",
            ),
            "https://tickets.example.test/#ticket/4242",
        )

    def test_https_url_value_rejects_non_https_url(self) -> None:
        with self.assertRaises(MissingReceiptValueError):
            require_receipt_https_url_value(
                "http://tickets.example.test/#ticket/4242",
                "ticket_reference_url",
            )


if __name__ == "__main__":
    unittest.main()
