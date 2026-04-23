from __future__ import annotations

import pathlib


def read_operator_routes_test_bundle(repo_root: pathlib.Path) -> str:
    app_root = repo_root / "apps/operator-ui/src/app"
    bundle_parts = [
        app_root / "OperatorRoutes.test.tsx",
        *sorted(app_root.glob("OperatorRoutes.*.testSuite.tsx")),
    ]

    missing = [path for path in bundle_parts if not path.exists()]
    if missing:
        missing_paths = ", ".join(str(path) for path in missing)
        raise AssertionError(f"expected operator route test source at {missing_paths}")

    return "\n".join(path.read_text(encoding="utf-8") for path in bundle_parts)
