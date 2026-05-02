from __future__ import annotations

import importlib
import pathlib
import sys
import unittest


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))


class Phase5274PhysicalLayoutMigrationTests(unittest.TestCase):
    def test_canonical_package_owns_physical_implementation_files(self) -> None:
        canonical_root = CONTROL_PLANE_ROOT / "aegisops" / "control_plane"
        legacy_root = CONTROL_PLANE_ROOT / "aegisops_control_plane"

        self.assertTrue((canonical_root / "service.py").is_file())
        self.assertTrue((canonical_root / "models.py").is_file())
        self.assertTrue((canonical_root / "core" / "legacy_import_aliases.py").is_file())
        self.assertTrue((legacy_root / "__init__.py").is_file())

        self.assertFalse((legacy_root / "service.py").exists())
        self.assertFalse((legacy_root / "models.py").exists())
        self.assertFalse((legacy_root / "core" / "legacy_import_aliases.py").exists())

    def test_legacy_imports_alias_to_canonical_module_identity(self) -> None:
        module_pairs = {
            "aegisops_control_plane.service": "aegisops.control_plane.service",
            "aegisops_control_plane.models": "aegisops.control_plane.models",
            "aegisops_control_plane.actions.review.action_review_chain": (
                "aegisops.control_plane.actions.review.action_review_chain"
            ),
            "aegisops_control_plane.audit_export": (
                "aegisops.control_plane.reporting.audit_export"
            ),
        }

        for legacy_name, canonical_name in module_pairs.items():
            with self.subTest(legacy_name=legacy_name):
                legacy = importlib.import_module(legacy_name)
                canonical = importlib.import_module(canonical_name)
                self.assertIs(legacy, canonical)

    def test_legacy_root_exports_canonical_public_surface(self) -> None:
        legacy = importlib.import_module("aegisops_control_plane")
        canonical = importlib.import_module("aegisops.control_plane")

        self.assertEqual(legacy.__all__, canonical.__all__)
        for attribute in (
            "AegisOpsControlPlaneService",
            "AlertRecord",
            "RuntimeConfig",
            "build_runtime_service",
        ):
            with self.subTest(attribute=attribute):
                self.assertIs(getattr(legacy, attribute), getattr(canonical, attribute))


if __name__ == "__main__":
    unittest.main()
