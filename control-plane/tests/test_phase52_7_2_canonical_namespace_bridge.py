from __future__ import annotations

import importlib
import pathlib
import subprocess
import sys
import tempfile
import textwrap
import unittest


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))


class Phase5272CanonicalNamespaceBridgeTests(unittest.TestCase):
    def test_missing_bridge_registration_keeps_canonical_namespace_unavailable(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            package_root = pathlib.Path(temp_dir) / "aegisops_control_plane"
            package_root.mkdir()
            (package_root / "__init__.py").write_text("", encoding="utf-8")

            script = textwrap.dedent(
                """
                import importlib

                importlib.import_module("aegisops_control_plane")

                try:
                    importlib.import_module("aegisops.control_plane")
                except ModuleNotFoundError as exc:
                    if exc.name == "aegisops":
                        raise SystemExit(0)
                    raise
                raise SystemExit("canonical namespace unexpectedly imported")
                """
            )

            subprocess.run(
                [sys.executable, "-c", script],
                check=True,
                env={"PYTHONPATH": temp_dir},
            )

    def test_canonical_root_exports_legacy_public_surface(self) -> None:
        legacy = importlib.import_module("aegisops_control_plane")
        canonical = importlib.import_module("aegisops.control_plane")

        self.assertEqual(canonical.__all__, legacy.__all__)
        for attribute in (
            "AegisOpsControlPlaneService",
            "AlertRecord",
            "RuntimeConfig",
            "build_runtime_service",
        ):
            with self.subTest(attribute=attribute):
                self.assertIs(getattr(canonical, attribute), getattr(legacy, attribute))

    def test_canonical_submodules_share_legacy_module_identity(self) -> None:
        module_pairs = {
            "aegisops.control_plane.service": "aegisops_control_plane.service",
            "aegisops.control_plane.models": "aegisops_control_plane.models",
            "aegisops.control_plane.actions.review.action_review_chain": (
                "aegisops_control_plane.actions.review.action_review_chain"
            ),
            "aegisops.control_plane.reporting.audit_export": (
                "aegisops_control_plane.reporting.audit_export"
            ),
        }

        for canonical_name, legacy_name in module_pairs.items():
            with self.subTest(canonical_name=canonical_name):
                canonical = importlib.import_module(canonical_name)
                legacy = importlib.import_module(legacy_name)
                self.assertIs(canonical, legacy)

    def test_legacy_root_aliases_do_not_publish_synthetic_canonical_modules(
        self,
    ) -> None:
        script = textwrap.dedent(
            """
            import importlib
            import pathlib
            import sys

            control_plane_root = pathlib.Path.cwd()
            sys.path.insert(0, str(control_plane_root))

            importlib.import_module("aegisops.control_plane")

            synthetic_canonical_names = (
                "aegisops.control_plane.action_review_chain",
                "aegisops.control_plane.audit_export",
                "aegisops.control_plane.phase29_shadow_dataset",
            )
            for module_name in synthetic_canonical_names:
                if module_name in sys.modules:
                    raise SystemExit(f"synthetic canonical module registered: {module_name}")
                try:
                    importlib.import_module(module_name)
                except ModuleNotFoundError as exc:
                    if exc.name == module_name:
                        continue
                    raise
                raise SystemExit(f"synthetic canonical module imported: {module_name}")
            """
        )

        subprocess.run(
            [sys.executable, "-c", script],
            check=True,
            cwd=CONTROL_PLANE_ROOT,
        )

    def test_legacy_imports_remain_available_after_canonical_bridge(self) -> None:
        importlib.import_module("aegisops.control_plane")

        legacy_service = importlib.import_module("aegisops_control_plane.service")
        legacy_package = importlib.import_module("aegisops_control_plane")

        self.assertIs(
            legacy_service.AegisOpsControlPlaneService,
            legacy_package.AegisOpsControlPlaneService,
        )


if __name__ == "__main__":
    unittest.main()
