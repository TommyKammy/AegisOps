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

from aegisops.control_plane.publishable_paths import is_workstation_local_path


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
VERIFY_SCRIPT = REPO_ROOT / "scripts/verify-publishable-path-hygiene.sh"
MACOS_HOME_SEGMENT = "Users"
LINUX_HOME_SEGMENT = "home"
WINDOWS_HOME_SEGMENT = "Users"
UNIX_USERS_PATH = f"/{MACOS_HOME_SEGMENT}/alice/project/docs"
UNIX_HOME_PATH = f"/{LINUX_HOME_SEGMENT}/alice/project/docs"
WINDOWS_USERS_PATH = rf"C:\{WINDOWS_HOME_SEGMENT}\alice\project\docs"
WINDOWS_USERS_PATH_POSIX = f"C:/{WINDOWS_HOME_SEGMENT}/alice/project/docs"
OFFENDER_PATH = f"/{MACOS_HOME_SEGMENT}/alice/private/project"
ROOT_SEGMENT = "root"
ROOT_PATH = f"/{ROOT_SEGMENT}/private/project"


class PublishablePathHygieneTests(unittest.TestCase):
    def test_detects_unix_and_windows_workstation_paths_in_text(self) -> None:
        escaped_slash = r"\/"
        self.assertTrue(is_workstation_local_path(UNIX_USERS_PATH))
        self.assertTrue(is_workstation_local_path(f"see {UNIX_HOME_PATH} for details"))
        self.assertTrue(is_workstation_local_path(f"path:{UNIX_HOME_PATH}"))
        self.assertTrue(is_workstation_local_path(f"path:{UNIX_USERS_PATH}"))
        self.assertTrue(is_workstation_local_path(f"path:{ROOT_PATH}"))
        self.assertTrue(is_workstation_local_path(WINDOWS_USERS_PATH))
        self.assertTrue(is_workstation_local_path(f"path={WINDOWS_USERS_PATH_POSIX}"))
        self.assertTrue(is_workstation_local_path(f"path:{WINDOWS_USERS_PATH_POSIX}"))
        self.assertTrue(
            is_workstation_local_path(
                f"path:{escaped_slash}Users{escaped_slash}alice"
                f"{escaped_slash}project{escaped_slash}docs"
            )
        )
        self.assertTrue(
            is_workstation_local_path(
                f"path:{escaped_slash}home{escaped_slash}alice"
                f"{escaped_slash}project{escaped_slash}docs"
            )
        )
        self.assertTrue(
            is_workstation_local_path(
                f"path:{escaped_slash}root{escaped_slash}private{escaped_slash}docs"
            )
        )
        self.assertTrue(
            is_workstation_local_path(
                f"path=C:{escaped_slash}Users{escaped_slash}alice"
                f"{escaped_slash}project{escaped_slash}docs"
            )
        )

    def test_ignores_urls_and_non_user_windows_paths(self) -> None:
        self.assertFalse(
            is_workstation_local_path(
                f"https://example.com/{LINUX_HOME_SEGMENT}/alice/project/docs"
            )
        )
        self.assertFalse(
            is_workstation_local_path(
                f"https://example.com/C:/{WINDOWS_HOME_SEGMENT}/alice/project/docs"
            )
        )
        self.assertFalse(is_workstation_local_path(r"D:\Program Files\AegisOps"))
        self.assertFalse(is_workstation_local_path("relative/path/to/docs"))

    def test_verify_script_skips_binary_files_and_redacts_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = pathlib.Path(tmpdir)
            subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True)

            docs_dir = repo_root / "docs"
            docs_dir.mkdir()
            scripts_dir = repo_root / "scripts"
            scripts_dir.mkdir()
            (repo_root / "control-plane" / "tests").mkdir(parents=True)
            (repo_root / ".github" / "workflows").mkdir(parents=True)

            (repo_root / "README.md").write_text("No local paths here.\n", encoding="utf-8")
            (docs_dir / "binary.bin").write_bytes(
                b"\x00\x01\x02/" + LINUX_HOME_SEGMENT.encode("utf-8") + b"/alice/private"
            )
            (docs_dir / "offender.md").write_text(
                f"operator note: {OFFENDER_PATH}\n",
                encoding="utf-8",
            )
            (scripts_dir / "clean.sh").write_text(
                "echo no local paths here\n",
                encoding="utf-8",
            )

            subprocess.run(
                [
                    "git",
                    "add",
                    "README.md",
                    "docs/binary.bin",
                    "docs/offender.md",
                    "scripts/clean.sh",
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

    def test_verify_script_scans_scripts_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = pathlib.Path(tmpdir)
            subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True)

            (repo_root / "scripts").mkdir()
            (repo_root / "scripts" / "offender.sh").write_text(
                f"echo {OFFENDER_PATH}\n",
                encoding="utf-8",
            )
            subprocess.run(
                ["git", "add", "scripts/offender.sh"],
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
                "scripts/offender.sh:1: contains workstation-local absolute path",
                result.stderr,
            )


if __name__ == "__main__":
    unittest.main()
