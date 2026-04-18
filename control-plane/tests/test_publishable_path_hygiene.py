from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import tempfile
import unittest


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from aegisops_control_plane.publishable_paths import is_workstation_local_path


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
VERIFY_SCRIPT = REPO_ROOT / "scripts/verify-publishable-path-hygiene.sh"
UNIX_USERS_PATH = "/Users/alice/project/docs"  # publishable-path-hygiene: allowlist
UNIX_HOME_PATH = "/home/alice/project/docs"  # publishable-path-hygiene: allowlist
WINDOWS_USERS_PATH = r"C:\Users\alice\project\docs"  # publishable-path-hygiene: allowlist
WINDOWS_USERS_PATH_POSIX = "C:/Users/alice/project/docs"  # publishable-path-hygiene: allowlist
OFFENDER_PATH = "/Users/alice/private/project"  # publishable-path-hygiene: allowlist


class PublishablePathHygieneTests(unittest.TestCase):
    def test_detects_unix_and_windows_workstation_paths_in_text(self) -> None:
        self.assertTrue(is_workstation_local_path(UNIX_USERS_PATH))
        self.assertTrue(is_workstation_local_path(f"see {UNIX_HOME_PATH} for details"))
        self.assertTrue(is_workstation_local_path(f"path:{UNIX_HOME_PATH}"))
        self.assertTrue(is_workstation_local_path(f"path:{UNIX_USERS_PATH}"))
        self.assertTrue(is_workstation_local_path(WINDOWS_USERS_PATH))
        self.assertTrue(is_workstation_local_path(f"path={WINDOWS_USERS_PATH_POSIX}"))
        self.assertTrue(is_workstation_local_path(f"path:{WINDOWS_USERS_PATH_POSIX}"))

    def test_ignores_urls_and_non_user_windows_paths(self) -> None:
        self.assertFalse(
            is_workstation_local_path("https://example.com/home/alice/project/docs")  # publishable-path-hygiene: allowlist
        )
        self.assertFalse(
            is_workstation_local_path("https://example.com/C:/Users/alice/project/docs")  # publishable-path-hygiene: allowlist
        )
        self.assertFalse(is_workstation_local_path(r"D:\Program Files\AegisOps"))
        self.assertFalse(is_workstation_local_path("relative/path/to/docs"))

    def test_verify_script_skips_binary_files_and_redacts_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = pathlib.Path(tmpdir)
            subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True)

            docs_dir = repo_root / "docs"
            docs_dir.mkdir()
            (repo_root / "control-plane" / "tests").mkdir(parents=True)
            (repo_root / ".github" / "workflows").mkdir(parents=True)

            (repo_root / "README.md").write_text("No local paths here.\n", encoding="utf-8")
            (docs_dir / "binary.bin").write_bytes(b"\x00\x01\x02/home/alice/private")  # publishable-path-hygiene: allowlist
            (docs_dir / "offender.md").write_text(
                f"operator note: {OFFENDER_PATH}\n",
                encoding="utf-8",
            )

            subprocess.run(
                [
                    "git",
                    "add",
                    "README.md",
                    "docs/binary.bin",
                    "docs/offender.md",
                ],
                cwd=repo_root,
                check=True,
                capture_output=True,
            )

            env = os.environ.copy()
            existing_pythonpath = env.get("PYTHONPATH")
            control_plane_path = str(REPO_ROOT / "control-plane")
            env["PYTHONPATH"] = (
                f"{control_plane_path}:{existing_pythonpath}"
                if existing_pythonpath
                else control_plane_path
            )

            result = subprocess.run(
                ["bash", str(VERIFY_SCRIPT), str(repo_root)],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn(
                "docs/offender.md:1: contains workstation-local absolute path",
                result.stderr,
            )
            self.assertNotIn(OFFENDER_PATH, result.stderr)
            self.assertNotIn("binary.bin", result.stderr)


if __name__ == "__main__":
    unittest.main()
