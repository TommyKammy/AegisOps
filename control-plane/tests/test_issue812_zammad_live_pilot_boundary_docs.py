from __future__ import annotations

import pathlib
import shutil
import subprocess
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Issue812ZammadLivePilotBoundaryDocsTests(unittest.TestCase):
    @staticmethod
    def _read(relative_path: str) -> str:
        path = REPO_ROOT / relative_path
        if not path.exists():
            raise AssertionError(f"expected document at {path}")
        return path.read_text(encoding="utf-8")

    def test_zammad_live_pilot_boundary_doc_defines_scope_and_non_authority(
        self,
    ) -> None:
        text = self._read("docs/operations-zammad-live-pilot-boundary.md")

        for term in (
            "# Operations Zammad-First Live Pilot Boundary and Credential Custody",
            "Zammad is the only approved live coordination substrate for the first pilot.",
            "GLPI remains a documented fallback only after a separate reviewed change rejects Zammad for the pilot.",
            "The pilot is link-first and coordination-only.",
            "AegisOps remains authoritative for case, action, approval, execution, and reconciliation records.",
            "Ticket state, SLA state, comments, assignee, queue, priority, escalation, or closure in Zammad must not become AegisOps case, action, approval, execution, or reconciliation authority.",
            "multi-ITSM abstraction",
            "bidirectional sync",
            "ticket-system authority",
        ):
            self.assertIn(term, text)

    def test_zammad_live_pilot_boundary_doc_defines_credential_custody(
        self,
    ) -> None:
        text = self._read("docs/operations-zammad-live-pilot-boundary.md")

        for term in (
            "## 3. Credential Custody and Rotation",
            "Zammad live-pilot credentials must resolve only from the reviewed managed-secret boundary.",
            "`AEGISOPS_ZAMMAD_BASE_URL`",
            "`AEGISOPS_ZAMMAD_TOKEN_FILE`",
            "`AEGISOPS_ZAMMAD_OPENBAO_PATH`",
            "No Zammad credential, bearer token, API key, session cookie, customer secret, or environment-specific endpoint credential may be committed to Git",
            "Placeholder, sample, fake, TODO, unsigned, empty, stale, or human-mailbox credentials are invalid.",
            "Rotation must be documented before pilot activation, after suspected exposure, after custodian or scope change, and after any break-glass use.",
            "If the reviewed secret source is unavailable, unreadable, empty, stale, or only placeholder-backed, the pilot remains unavailable and fails closed.",
        ):
            self.assertIn(term, text)

    def test_zammad_live_pilot_boundary_doc_defines_endpoint_and_degraded_behavior(
        self,
    ) -> None:
        text = self._read("docs/operations-zammad-live-pilot-boundary.md")

        for term in (
            "## 4. Endpoint and Proxy Assumptions",
            "Zammad access for the pilot must use the reviewed outbound integration path and the documented endpoint in `AEGISOPS_ZAMMAD_BASE_URL`.",
            "Operators must not trust raw `X-Forwarded-*`, `Forwarded`, host, proto, tenant, or user identity hints from Zammad",
            "The AegisOps backend and operator UI must not expose a direct inbound Zammad webhook authority path for this pilot.",
            "## 5. Unavailable and Degraded Operator Behavior",
            "`available`",
            "`degraded`",
            "`unavailable`",
            "When Zammad is unavailable or credentials fail custody validation, operators may continue AegisOps case review, approval, execution, and reconciliation from AegisOps records.",
            "Operators must not infer ticket existence, approval, execution, reconciliation, closure, or customer notification from a missing, stale, unreachable, or mismatched Zammad record.",
            "No failed Zammad write, stale read, timeout, proxy failure, auth failure, or degraded ticket payload may create an orphan AegisOps authority record or mark an AegisOps lifecycle step complete.",
        ):
            self.assertIn(term, text)

    def test_zammad_live_pilot_verifier_is_present_and_passes(self) -> None:
        verifier = REPO_ROOT / "scripts" / "verify-zammad-live-pilot-boundary.sh"

        self.assertTrue(verifier.exists(), f"expected verifier at {verifier}")

        bash_path = shutil.which("bash")
        self.assertIsNotNone(bash_path, "bash executable not found in PATH")
        result = subprocess.run(
            [bash_path, str(verifier), str(REPO_ROOT)],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(
            result.returncode,
            0,
            f"verifier failed\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
