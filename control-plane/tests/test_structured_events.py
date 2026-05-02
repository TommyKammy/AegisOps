from __future__ import annotations

import pathlib
import sys
import unittest


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from aegisops.control_plane.structured_events import sanitize_structured_event_fields


class StructuredEventSanitizationTests(unittest.TestCase):
    def test_sanitizer_redacts_peer_address_and_identity_values(self) -> None:
        sanitized = sanitize_structured_event_fields(
            {
                "peer_addr": "10.10.0.5",
                "requester_identity": "analyst-001",
                "approver_identities": ("approver-001", "  ", "approver-002"),
                "payload": {"safe": ("tuple-value",)},
            }
        )

        self.assertEqual(sanitized["peer_addr_class"], "private")
        self.assertTrue(sanitized["requester_identity_present"])
        self.assertEqual(sanitized["approver_identities_count"], 2)
        self.assertEqual(sanitized["payload"], {"safe": ["tuple-value"]})
        self.assertNotIn("peer_addr", sanitized)
        self.assertNotIn("requester_identity", sanitized)
        self.assertNotIn("approver_identities", sanitized)

    def test_sanitizer_fails_closed_to_non_identifying_peer_classes(self) -> None:
        self.assertEqual(
            sanitize_structured_event_fields({"peer_addr": None})["peer_addr_class"],
            "missing",
        )
        self.assertEqual(
            sanitize_structured_event_fields({"peer_addr": "not-an-ip"})[
                "peer_addr_class"
            ],
            "invalid",
        )
        self.assertEqual(
            sanitize_structured_event_fields({"peer_addr": "127.0.0.1"})[
                "peer_addr_class"
            ],
            "loopback",
        )


if __name__ == "__main__":
    unittest.main()
