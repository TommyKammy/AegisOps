from __future__ import annotations

import importlib
import unittest


_PHASE24_RUNTIME_MODULES = (
    "control-plane.tests.test_phase24_live_assistant_surface_validation",
    "control-plane.tests.test_phase24_live_assistant_fallback_validation",
    "control-plane.tests.test_phase24_live_assistant_provider_validation",
    "control-plane.tests.test_phase24_live_assistant_feedback_loop_validation",
    "control-plane.tests.test_phase24_live_assistant_adversarial_validation",
)


def load_tests(
    loader: unittest.TestLoader,
    tests: unittest.TestSuite,
    pattern: str | None,
) -> unittest.TestSuite:
    suite = unittest.TestSuite()
    for module_name in _PHASE24_RUNTIME_MODULES:
        suite.addTests(loader.loadTestsFromModule(importlib.import_module(module_name)))
    return suite


if __name__ == "__main__":
    unittest.main()
