from __future__ import annotations

import pathlib
import shutil
import subprocess
import tempfile
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase16FirstBootVerifierTests(unittest.TestCase):
    def test_phase16_first_boot_verifier_exists(self) -> None:
        verifier = REPO_ROOT / "scripts" / "verify-phase-16-first-boot-contract.sh"

        self.assertTrue(verifier.exists(), f"expected Phase 16 verifier at {verifier}")

    def test_phase16_first_boot_verifier_fails_closed_on_release_state_and_bootstrap_drift(
        self,
    ) -> None:
        verifier = REPO_ROOT / "scripts" / "verify-phase-16-first-boot-contract.sh"
        self.assertTrue(verifier.exists(), f"expected Phase 16 verifier at {verifier}")

        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_root = pathlib.Path(tmpdir) / "repo"
            self._create_repo_fixture(fixture_root)

            self._assert_verifier_passes(verifier, fixture_root)

            self._remove_text(
                fixture_root / "README.md",
                (
                    "That first-boot target is limited to the AegisOps control-plane service, "
                    "PostgreSQL for control-plane state, the approved reverse proxy boundary, "
                    "and reviewed Wazuh-facing analytic-signal intake expectations.\n"
                ),
            )
            self._assert_verifier_fails_with(
                verifier,
                fixture_root,
                "README.md",
            )

            self._create_repo_fixture(fixture_root)
            compose_path = (
                fixture_root / "control-plane" / "deployment" / "first-boot" / "docker-compose.yml"
            )
            self._insert_text_after(compose_path, "    image: aegisops-control-plane:first-boot\n", "    volumes:\n      - ../../../:/workspace:ro\n")
            self._assert_verifier_fails_with(
                verifier,
                fixture_root,
                "First-boot compose must not depend on repository-local runtime bind mounts.",
            )

            self._create_repo_fixture(fixture_root)
            compose_path = (
                fixture_root / "control-plane" / "deployment" / "first-boot" / "docker-compose.yml"
            )
            compose_path.write_text(
                compose_path.read_text(encoding="utf-8")
                + "\n  opensearch:\n    image: opensearchproject/opensearch:2\n",
                encoding="utf-8",
            )
            self._assert_verifier_fails_with(
                verifier,
                fixture_root,
                "must not define first-boot service: opensearch",
            )

            self._create_repo_fixture(fixture_root)
            self._remove_text(
                fixture_root
                / "control-plane"
                / "deployment"
                / "first-boot"
                / "control-plane-entrypoint.sh",
                'exec "$@"\n',
            )
            self._assert_verifier_fails_with(
                verifier,
                fixture_root,
                'Missing required line in control-plane/deployment/first-boot/control-plane-entrypoint.sh: exec "$@"',
            )

            self._create_repo_fixture(fixture_root)
            (
                fixture_root
                / "postgres"
                / "control-plane"
                / "migrations"
                / "0006_phase_23_lifecycle_transition_records.sql"
            ).unlink()
            self._assert_verifier_fails_with(
                verifier,
                fixture_root,
                "Missing reviewed control-plane migration asset",
            )

    @staticmethod
    def _create_repo_fixture(target: pathlib.Path) -> None:
        if target.exists():
            shutil.rmtree(target)

        required_files = (
            "README.md",
            "docs/phase-16-release-state-and-first-boot-scope.md",
            "docs/requirements-baseline.md",
            "docs/control-plane-runtime-service-boundary.md",
            "docs/runbook.md",
            "control-plane/deployment/first-boot/bootstrap.env.sample",
            "control-plane/deployment/first-boot/docker-compose.yml",
            "control-plane/deployment/first-boot/control-plane-entrypoint.sh",
            "postgres/control-plane/README.md",
            "postgres/control-plane/schema.sql",
            "postgres/control-plane/migrations/0001_control_plane_schema_skeleton.sql",
            "postgres/control-plane/migrations/0002_phase_14_reviewed_context_columns.sql",
            "postgres/control-plane/migrations/0003_phase_15_assistant_advisory_draft_columns.sql",
            "postgres/control-plane/migrations/0004_phase_20_action_request_binding_columns.sql",
            "postgres/control-plane/migrations/0005_phase_23_approval_decision_rationale.sql",
            "postgres/control-plane/migrations/0006_phase_23_lifecycle_transition_records.sql",
            "postgres/control-plane/migrations/0007_phase_23_lifecycle_transition_subject_index.sql",
        )

        for relative_path in required_files:
            source = REPO_ROOT / relative_path
            destination = target / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

    @staticmethod
    def _remove_text(path: pathlib.Path, text: str) -> None:
        content = path.read_text(encoding="utf-8")
        if text not in content:
            raise AssertionError(f"expected to remove text from {path}: {text!r}")
        path.write_text(content.replace(text, "", 1), encoding="utf-8")

    @staticmethod
    def _insert_text_after(path: pathlib.Path, anchor: str, inserted: str) -> None:
        content = path.read_text(encoding="utf-8")
        if anchor not in content:
            raise AssertionError(f"expected to insert text in {path} after: {anchor!r}")
        path.write_text(content.replace(anchor, anchor + inserted, 1), encoding="utf-8")

    @staticmethod
    def _assert_verifier_passes(verifier: pathlib.Path, repo_root: pathlib.Path) -> None:
        result = subprocess.run(
            ["bash", str(verifier), str(repo_root)],
            check=False,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise AssertionError(
                "expected verifier to pass\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )

    @staticmethod
    def _assert_verifier_fails_with(
        verifier: pathlib.Path,
        repo_root: pathlib.Path,
        expected_stderr: str,
    ) -> None:
        result = subprocess.run(
            ["bash", str(verifier), str(repo_root)],
            check=False,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            raise AssertionError(
                "expected verifier to fail\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )

        if expected_stderr not in result.stderr:
            raise AssertionError(
                "expected verifier stderr to contain\n"
                f"{expected_stderr!r}\n"
                f"actual stderr:\n{result.stderr}"
            )


if __name__ == "__main__":
    unittest.main()
