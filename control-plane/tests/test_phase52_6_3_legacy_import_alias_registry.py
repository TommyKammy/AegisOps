from __future__ import annotations

import importlib
import pathlib
import sys
import unittest


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))


class LegacyImportAliasRegistryTests(unittest.TestCase):
    def test_approved_legacy_alias_resolves_to_registered_owner(self) -> None:
        registry = importlib.import_module(
            "aegisops_control_plane.core.legacy_import_aliases"
        )

        alias = "aegisops_control_plane.audit_export"
        owner = "aegisops_control_plane.reporting.audit_export"

        self.assertIn(alias, registry.LEGACY_IMPORT_ALIASES)
        self.assertEqual(registry.LEGACY_IMPORT_ALIASES[alias].target_module, owner)
        self.assertEqual(registry.LEGACY_IMPORT_ALIASES[alias].target_family, "reporting")

        legacy_module = importlib.import_module(alias)
        owner_module = importlib.import_module(owner)
        package = importlib.import_module("aegisops_control_plane")
        from aegisops_control_plane import audit_export as legacy_from_package

        self.assertIs(legacy_module, owner_module)
        self.assertIs(legacy_from_package, owner_module)
        self.assertIs(package.audit_export, owner_module)
        self.assertIs(
            legacy_module.export_audit_retention_baseline,
            owner_module.export_audit_retention_baseline,
        )


if __name__ == "__main__":
    unittest.main()
