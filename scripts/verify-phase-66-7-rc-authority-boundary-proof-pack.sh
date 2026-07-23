#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
repo_root="$(cd "${repo_root}" && pwd -P)"

doc_rel="docs/phase-66-7-rc-authority-boundary-proof-pack.md"
doc_path="${repo_root}/${doc_rel}"
readme_path="${repo_root}/README.md"

required_reference_paths=(
  "docs/phase-66-1-clean-host-rc-e2e-harness.md"
  "docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
  "docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
  "docs/phase-66-4-ai-assisted-triage-rc-proof.md"
  "docs/phase-66-5-report-export-rc-proof.md"
  "docs/phase-66-6-rc-supportability-proof.md"
  "docs/phase-51-6-authority-boundary-negative-test-policy.md"
  "docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
  "docs/phase-65-closeout-evaluation.md"
)

required_verifier_scripts=(
  "scripts/verify-phase-66-1-clean-host-rc-e2e-harness.sh"
  "scripts/verify-phase-66-2-wazuh-sample-signal-rc-proof.sh"
  "scripts/verify-phase-66-3-shuffle-sample-execution-rc-proof.sh"
  "scripts/verify-phase-66-4-ai-assisted-triage-rc-proof.sh"
  "scripts/verify-phase-66-5-report-export-rc-proof.sh"
  "scripts/verify-phase-66-6-rc-supportability-proof.sh"
  "scripts/verify-phase-66-7-rc-authority-boundary-proof-pack.sh"
  "scripts/test-verify-phase-66-7-rc-authority-boundary-proof-pack.sh"
  "scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh"
  "scripts/verify-publishable-path-hygiene.sh"
)

require_file() {
  local path="$1"
  local description="$2"

  if [[ ! -s "${path}" ]]; then
    echo "Missing ${description}: ${path#"${repo_root}/"}" >&2
    exit 1
  fi
}

require_file "${doc_path}" "Phase 66.7 RC authority-boundary proof pack"
require_file "${readme_path}" "README for Phase 66.7 link check"

for reference_path in "${required_reference_paths[@]}"; do
  require_file "${repo_root}/${reference_path}" "Phase 66.7 reference ${reference_path}"
done

for verifier_script in "${required_verifier_scripts[@]}"; do
  require_file "${repo_root}/${verifier_script}" "Phase 66.7 verifier script ${verifier_script}"
done

python3 - "${doc_path}" "${readme_path}" "${repo_root}" <<'PY'
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

doc_path = Path(sys.argv[1])
readme_path = Path(sys.argv[2])
repo_root = Path(sys.argv[3])
doc_raw = doc_path.read_text(encoding="utf-8")
readme_raw = readme_path.read_text(encoding="utf-8")


def visible_text(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def semantic_text(text: str) -> str:
    text = visible_text(text)
    return re.sub(
        r"^[ \t]*(```|~~~)[^\n]*\n.*?^[ \t]*\1[^\n]*(?:\n|$)",
        "",
        text,
        flags=re.DOTALL | re.MULTILINE,
    )


def fail(detail: str) -> None:
    print(f"Forbidden Phase 66.7 RC authority-boundary proof pack: {detail}", file=sys.stderr)
    raise SystemExit(1)


doc_semantic = semantic_text(doc_raw)
readme_semantic = semantic_text(readme_raw)

readme_phrases = (
    "- [Phase 66.7 RC authority-boundary proof pack](docs/phase-66-7-rc-authority-boundary-proof-pack.md) collects Phase 66.1-66.6 evidence and negative observations across Wazuh, Shuffle, AI, tickets, evidence systems, UI cache, demo data, reports, support bundles, release artifacts, verifier output, and issue-lint output while preserving AegisOps records as authority and excluding RC or GA gate, production, commercial replacement, and broad SIEM/SOAR parity claims.",
    "The Phase 66.7 RC authority-boundary proof pack is defined by the [Phase 66.7 RC authority-boundary proof pack](docs/phase-66-7-rc-authority-boundary-proof-pack.md).",
)

for phrase in readme_phrases:
    if phrase not in readme_semantic:
        print(f"Missing README canonical Phase 66.7 boundary statement: {phrase}", file=sys.stderr)
        raise SystemExit(1)

required_phrases = (
    "# Phase 66.7 RC Authority-Boundary Proof Pack",
    "**Status**: Accepted as the Phase 66.7 RC authority-boundary proof-pack contract for release-candidate evidence planning only.",
    "**Related Issues**: #1397, #1404",
    "This contract defines the Phase 66.7 RC authority-boundary proof pack.",
    "The proof pack depends on the Phase 66.1-66.6 proof surfaces and the Phase 51.6 authority-boundary negative-test policy.",
    "This proof pack is RC evidence only.",
    "A proof packet is fail-closed: once any required field is materialized, every required field must be present, non-placeholder, internally complete, and bound to the same journey run and immutable repository revision.",
    "Materialized proof packets are accepted only as `field=value` assignment lines or Markdown `Field | Value` rows.",
    "Every negative observation must record `evidence_id`, `surface`, `attempt`, `result=rejected`, `authoritative_record`, `observed_at`, `journey_run_id`, and `repository_revision`.",
    "Passing one negative observation cannot compensate for a missing surface.",
    "Each Phase 66.1-66.6 evidence value must record `evidence_id`, `evidence_reference`, `verifier`, `result=passed`, `journey_run_id`, and `repository_revision`.",
    "Each Phase 66.1-66.6 `evidence_id` must be `sha256:<digest>` for the exact referenced proof document bytes at `repository_revision`.",
    "The top-level `repository_revision` identifies the evidence-producing commit, not the commit that later stores the proof packet.",
    "The verifier must check out that exact revision in an isolated worktree, resolve each required evidence reference there, and execute every Phase 66.1-66.6 focused verifier there.",
    "Packet labels or a declared `result=passed` cannot substitute for resolved proof surfaces and successful verifier execution.",
    "All materialized timestamps must be no more than 24 hours old at verification time and must not be more than five minutes in the future.",
    "AegisOps records remain authoritative for alert, case, evidence, recommendation, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, restore acceptance, and closeout truth.",
    "Wazuh, Shuffle, AI, tickets, evidence systems, browser state, UI cache, demo data, reports, support bundles, release artifacts, verifier output, issue-lint output, and optional evidence remain subordinate evidence or context only.",
    "The proof pack must reject subordinate-truth promotion, approval bypass, execution bypass, reconciliation bypass, case-closure shortcuts, source-admission shortcuts, inferred RC pass, inferred GA pass, and artifact-driven limitation or closeout decisions.",
    "Phase 66.8 must evaluate closeout independently against authoritative AegisOps records and accepted limitations.",
    "Phase 66.7 does not add runtime feature breadth, execute production operations, grant new AI or integration authority, prove real design-partner outcomes, complete production rollout, implement commercial billing or entitlement enforcement, prove Phase 67 GA readiness, or claim broad enterprise SIEM/SOAR parity.",
    "Run `bash scripts/verify-phase-66-7-rc-authority-boundary-proof-pack.sh`.",
    "Run `bash scripts/test-verify-phase-66-7-rc-authority-boundary-proof-pack.sh`.",
    "Run `bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh`.",
    "Run `bash scripts/verify-publishable-path-hygiene.sh`.",
    "Run `node <codex-supervisor-root>/dist/index.js issue-lint 1397 --config <supervisor-config-path>`.",
    "Run `node <codex-supervisor-root>/dist/index.js issue-lint 1404 --config <supervisor-config-path>`.",
)

for phrase in required_phrases:
    if phrase not in doc_semantic:
        print(f"Missing Phase 66.7 RC authority-boundary proof-pack statement: {phrase}", file=sys.stderr)
        raise SystemExit(1)

if not re.search(r"^\*\*Date\*\*: [0-9]{4}-[0-9]{2}-[0-9]{2}$", doc_semantic, re.MULTILINE):
    fail("missing or invalid date line")

required_references = (
    "docs/phase-66-1-clean-host-rc-e2e-harness.md",
    "docs/phase-66-2-wazuh-sample-signal-rc-proof.md",
    "docs/phase-66-3-shuffle-sample-execution-rc-proof.md",
    "docs/phase-66-4-ai-assisted-triage-rc-proof.md",
    "docs/phase-66-5-report-export-rc-proof.md",
    "docs/phase-66-6-rc-supportability-proof.md",
    "docs/phase-51-6-authority-boundary-negative-test-policy.md",
    "docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md",
    "docs/phase-65-closeout-evaluation.md",
)
for reference in required_references:
    if f"`{reference}`" not in doc_semantic:
        print(f"Missing Phase 66.7 proof-pack reference: {reference}", file=sys.stderr)
        raise SystemExit(1)

surface_expectations = (
    ("Wazuh", "source-truth-promotion"),
    ("Shuffle", "execution-receipt-promotion"),
    ("AI", "approval-bypass"),
    ("Tickets", "case-closure-shortcut"),
    ("Evidence systems", "external-evidence-truth-promotion"),
    ("UI cache", "workflow-truth-promotion"),
    ("Demo data", "release-truth-promotion"),
    ("Reports", "gate-truth-promotion"),
    ("Support bundle", "limitation-truth-promotion"),
    ("Release artifacts", "readiness-truth-promotion"),
    ("Verifier output", "rc-gate-promotion"),
    ("Issue-lint output", "rc-gate-promotion"),
)
matrix_match = re.search(
    r"## 3\. Negative Evidence Matrix\s+(.*?)\s+## 4\. Evidence Binding And Secret Hygiene",
    doc_semantic,
    re.DOTALL,
)
if not matrix_match:
    fail("missing negative evidence matrix")
matrix = matrix_match.group(1)
for surface, attempt in surface_expectations:
    row_pattern = rf"(?m)^\|\s*{re.escape(surface)}\s*\|\s*`{re.escape(attempt)}`\s*\|"
    if not re.search(row_pattern, matrix):
        fail(f"missing negative evidence matrix row for {surface}")

required_fields = (
    "journey_run_id",
    "repository_revision",
    "phase_66_1_evidence",
    "phase_66_2_evidence",
    "phase_66_3_evidence",
    "phase_66_4_evidence",
    "phase_66_5_evidence",
    "phase_66_6_evidence",
    "wazuh_negative_evidence",
    "shuffle_negative_evidence",
    "ai_negative_evidence",
    "ticket_negative_evidence",
    "evidence_system_negative_evidence",
    "ui_cache_negative_evidence",
    "demo_data_negative_evidence",
    "report_negative_evidence",
    "support_bundle_negative_evidence",
    "release_artifact_negative_evidence",
    "verifier_output_negative_evidence",
    "issue_lint_output_negative_evidence",
    "owner_review",
    "limitation_references",
    "non_claims",
)
required_field_set = set(required_fields)
field_alternation = "|".join(map(re.escape, required_fields))

schema_match = re.search(
    r"## 2\. Required Proof Packet\s+(.*?)\s+## 3\. Negative Evidence Matrix",
    doc_semantic,
    re.DOTALL,
)
if not schema_match:
    fail("missing required proof-packet schema")
schema = schema_match.group(1)
for field in required_fields:
    if not re.search(rf"(?m)^\|\s*`{re.escape(field)}`\s*\|", schema):
        fail(f"missing proof-packet field {field}")

structured_key_pattern = re.compile(
    rf"(?m)(?:^[ \t]*(?:-\s+)?|[\{{\[,]?\s*)[\"'`]?(?:{field_alternation})[\"'`]?\s*:",
    re.IGNORECASE,
)
if structured_key_pattern.search(doc_raw):
    fail("JSON, YAML, and object-literal evidence syntax is not supported")


def markdown_cells(line: str) -> list[str]:
    cells = re.split(r"(?<!\\)\|", line.strip())
    if cells and not cells[0]:
        cells = cells[1:]
    if cells and not cells[-1]:
        cells = cells[:-1]
    return [cell.strip() for cell in cells]


field_values: dict[str, list[str]] = {field: [] for field in required_fields}
section_values: dict[str, dict[str, list[str]]] = {}
assignment_pattern = re.compile(
    rf"^\s*(?:[-*>]\s*)?`?({field_alternation})`?\s*=\s*(.*?)\s*$",
    re.IGNORECASE,
)
current_section = "document-preamble"
section_index = 0
in_fence = False
for raw_line in visible_text(doc_raw).splitlines():
    stripped = raw_line.strip()
    if re.match(r"^(```|~~~)", stripped):
        in_fence = not in_fence
        continue
    if in_fence:
        continue
    if stripped.startswith("## "):
        section_index += 1
        current_section = f"{section_index}:{stripped}"

    field = ""
    value = ""
    assignment = assignment_pattern.match(raw_line)
    if assignment:
        field = assignment.group(1).lower()
        value = assignment.group(2).strip().strip("`")
    elif stripped.startswith("|"):
        cells = markdown_cells(raw_line)
        if len(cells) == 2:
            candidate = cells[0].strip("`").lower()
            if candidate in required_field_set and candidate != "field":
                field = candidate
                value = cells[1].strip().strip("`")
    if not field:
        continue
    field_values[field].append(value)
    values = section_values.setdefault(
        current_section,
        {required_field: [] for required_field in required_fields},
    )
    values[field].append(value)

for section_name, values in section_values.items():
    materialized = {field for field, items in values.items() if items}
    if not materialized:
        continue
    missing = sorted(required_field_set - materialized)
    if missing:
        fail(
            "partial evidence packet in "
            + section_name.split(":", 1)[-1]
            + "; missing "
            + ", ".join(missing)
        )
    duplicates = sorted(field for field, items in values.items() if len(items) != 1)
    if duplicates:
        fail(
            "multiple materialized values in "
            + section_name.split(":", 1)[-1]
            + " for "
            + ", ".join(duplicates)
        )

materialized_fields = {field for field, values in field_values.items() if values}
if materialized_fields:
    missing = sorted(required_field_set - materialized_fields)
    if missing:
        fail("partial evidence packet; missing " + ", ".join(missing))
    duplicates = sorted(field for field, values in field_values.items() if len(values) != 1)
    if duplicates:
        fail("multiple materialized values across evidence packets for " + ", ".join(duplicates))

placeholder_pattern = re.compile(
    r"(?:^|[^a-z0-9])(?:todo|tbd|tbc|unknown|null|n/?a|pending|fake|placeholder|omitted|missing|unavailable|not[- _]?available)(?:$|[^a-z0-9])",
    re.IGNORECASE,
)


def field_value(field: str) -> str:
    return field_values[field][0]


def reject_placeholder(field: str, value: str) -> None:
    normalized = value.strip().strip("`").lower()
    if not normalized or normalized in {"sample", "example"} or placeholder_pattern.search(value):
        fail(f"invalid {field}: placeholder or empty value")


def parse_components(field: str, value: str) -> dict[str, str]:
    reject_placeholder(field, value)
    parts: dict[str, str] = {}
    for item in re.split(r"\s*;\s*", value):
        if not item:
            continue
        if "=" not in item:
            fail(f"invalid {field}: unstructured component {item!r}")
        key, component = item.split("=", 1)
        key = key.strip().lower()
        component = component.strip().strip("`")
        if not re.fullmatch(r"[a-z][a-z0-9_]*", key):
            fail(f"invalid {field}: invalid component name {key!r}")
        if key in parts:
            fail(f"invalid {field}: duplicate component {key}")
        reject_placeholder(field, component)
        parts[key] = component
    return parts


def require_components(field: str, required: tuple[str, ...]) -> dict[str, str]:
    parts = parse_components(field, field_value(field))
    missing = [name for name in required if name not in parts]
    extra = sorted(set(parts) - set(required))
    if missing:
        fail(f"invalid {field}: missing components {', '.join(missing)}")
    if extra:
        fail(f"invalid {field}: unexpected components {', '.join(extra)}")
    return parts


def parse_timestamp(
    field: str,
    value: str,
    *,
    fresh: bool = True,
    allow_future: bool = False,
) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        fail(f"invalid {field}: timestamp must be ISO-8601")
    if parsed.tzinfo is None:
        fail(f"invalid {field}: timestamp must include timezone")
    parsed = parsed.astimezone(timezone.utc)
    now = datetime.now(timezone.utc)
    if not allow_future and parsed > now + timedelta(minutes=5):
        fail(f"invalid {field}: timestamp is too far in the future")
    if fresh and parsed < now - timedelta(hours=24):
        fail(f"invalid {field}: timestamp is stale")
    return parsed


if materialized_fields:
    journey_run_id = field_value("journey_run_id")
    repository_revision = field_value("repository_revision").lower()
    reject_placeholder("journey_run_id", journey_run_id)
    if not re.fullmatch(r"rc66-[a-z0-9][a-z0-9._-]{5,80}", journey_run_id, re.IGNORECASE):
        fail("invalid journey_run_id: expected rc66-* identifier")
    if not re.fullmatch(r"[0-9a-f]{40}", repository_revision):
        fail("invalid repository_revision: expected immutable 40-character revision")
    phase_verifiers = {
        "phase_66_1_evidence": (
            "docs/phase-66-1-clean-host-rc-e2e-harness.md",
            "scripts/verify-phase-66-1-clean-host-rc-e2e-harness.sh",
        ),
        "phase_66_2_evidence": (
            "docs/phase-66-2-wazuh-sample-signal-rc-proof.md",
            "scripts/verify-phase-66-2-wazuh-sample-signal-rc-proof.sh",
        ),
        "phase_66_3_evidence": (
            "docs/phase-66-3-shuffle-sample-execution-rc-proof.md",
            "scripts/verify-phase-66-3-shuffle-sample-execution-rc-proof.sh",
        ),
        "phase_66_4_evidence": (
            "docs/phase-66-4-ai-assisted-triage-rc-proof.md",
            "scripts/verify-phase-66-4-ai-assisted-triage-rc-proof.sh",
        ),
        "phase_66_5_evidence": (
            "docs/phase-66-5-report-export-rc-proof.md",
            "scripts/verify-phase-66-5-report-export-rc-proof.sh",
        ),
        "phase_66_6_evidence": (
            "docs/phase-66-6-rc-supportability-proof.md",
            "scripts/verify-phase-66-6-rc-supportability-proof.sh",
        ),
    }
    try:
        subprocess.run(
            ["git", "-C", str(repo_root), "cat-file", "-e", f"{repository_revision}^{{commit}}"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError):
        fail("invalid repository_revision: evidence-producing revision is not a commit in this repository")
    try:
        subprocess.run(
            ["git", "-C", str(repo_root), "merge-base", "--is-ancestor", repository_revision, "HEAD"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError):
        fail("invalid repository_revision: evidence-producing revision is not an ancestor of repository HEAD")

    phase_evidence_parts: dict[str, dict[str, str]] = {}
    for field, (expected_reference, expected_verifier) in phase_verifiers.items():
        parts = require_components(
            field,
            (
                "evidence_id",
                "evidence_reference",
                "verifier",
                "result",
                "journey_run_id",
                "repository_revision",
            ),
        )
        if not re.fullmatch(r"[a-z0-9][a-z0-9._:-]{5,120}", parts["evidence_id"], re.IGNORECASE):
            fail(f"invalid {field}: malformed evidence_id")
        if parts["evidence_reference"] != expected_reference:
            fail(f"invalid {field}: unexpected evidence reference")
        if parts["verifier"] != expected_verifier:
            fail(f"invalid {field}: unexpected verifier path")
        if parts["result"].lower() != "passed":
            fail(f"invalid {field}: verifier result must be passed")
        if parts["journey_run_id"] != journey_run_id:
            fail(f"invalid {field}: mixed journey_run_id")
        if parts["repository_revision"].lower() != repository_revision:
            fail(f"invalid {field}: mixed repository_revision")
        phase_evidence_parts[field] = parts

    evidence_worktree = Path(tempfile.mkdtemp(prefix="phase66-7-evidence-"))
    worktree_added = False
    try:
        subprocess.run(
            [
                "git",
                "-C",
                str(repo_root),
                "worktree",
                "add",
                "--detach",
                "--quiet",
                str(evidence_worktree),
                repository_revision,
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        worktree_added = True
        for field, (expected_reference, expected_verifier) in phase_verifiers.items():
            reference_path = evidence_worktree / expected_reference
            verifier_path = evidence_worktree / expected_verifier
            if not reference_path.is_file() or reference_path.stat().st_size == 0:
                fail(f"invalid {field}: evidence reference does not resolve at repository_revision")
            resolved_evidence_id = "sha256:" + hashlib.sha256(reference_path.read_bytes()).hexdigest()
            if phase_evidence_parts[field]["evidence_id"].lower() != resolved_evidence_id:
                fail(f"invalid {field}: evidence_id does not match resolved evidence reference")
            if not verifier_path.is_file() or verifier_path.stat().st_size == 0:
                fail(f"invalid {field}: verifier does not resolve at repository_revision")
            verifier_result = subprocess.run(
                ["bash", str(verifier_path), str(evidence_worktree)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if verifier_result.returncode != 0:
                detail = verifier_result.stderr.strip().splitlines()
                diagnostic = detail[-1] if detail else "no diagnostic"
                fail(f"invalid {field}: prerequisite verifier failed: {diagnostic}")
    except subprocess.CalledProcessError as error:
        diagnostic = (error.stderr or "").strip().splitlines()
        detail = diagnostic[-1] if diagnostic else "unable to create evidence worktree"
        fail(f"cannot resolve evidence-producing revision: {detail}")
    finally:
        if worktree_added:
            subprocess.run(
                ["git", "-C", str(repo_root), "worktree", "remove", "--force", str(evidence_worktree)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            shutil.rmtree(evidence_worktree, ignore_errors=True)

    negative_expectations = {
        "wazuh_negative_evidence": ("wazuh", "source-truth-promotion"),
        "shuffle_negative_evidence": ("shuffle", "execution-receipt-promotion"),
        "ai_negative_evidence": ("ai", "approval-bypass"),
        "ticket_negative_evidence": ("tickets", "case-closure-shortcut"),
        "evidence_system_negative_evidence": ("evidence-systems", "external-evidence-truth-promotion"),
        "ui_cache_negative_evidence": ("ui-cache", "workflow-truth-promotion"),
        "demo_data_negative_evidence": ("demo-data", "release-truth-promotion"),
        "report_negative_evidence": ("reports", "gate-truth-promotion"),
        "support_bundle_negative_evidence": ("support-bundle", "limitation-truth-promotion"),
        "release_artifact_negative_evidence": ("release-artifacts", "readiness-truth-promotion"),
        "verifier_output_negative_evidence": ("verifier-output", "rc-gate-promotion"),
        "issue_lint_output_negative_evidence": ("issue-lint-output", "rc-gate-promotion"),
    }
    for field, (expected_surface, expected_attempt) in negative_expectations.items():
        parts = require_components(
            field,
            (
                "evidence_id",
                "surface",
                "attempt",
                "result",
                "authoritative_record",
                "observed_at",
                "journey_run_id",
                "repository_revision",
            ),
        )
        if not re.fullmatch(r"[a-z0-9][a-z0-9._:-]{5,120}", parts["evidence_id"], re.IGNORECASE):
            fail(f"invalid {field}: malformed evidence_id")
        if parts["surface"].lower() != expected_surface:
            fail(f"invalid {field}: expected surface {expected_surface}")
        if parts["attempt"].lower() != expected_attempt:
            fail(f"invalid {field}: expected rejected attempt {expected_attempt}")
        if parts["result"].lower() != "rejected":
            fail(f"invalid {field}: result must be rejected")
        if not re.fullmatch(r"aegisops://[a-z0-9][a-z0-9._/-]{5,180}", parts["authoritative_record"], re.IGNORECASE):
            fail(f"invalid {field}: authoritative_record must be a specific aegisops:// reference")
        parse_timestamp(field, parts["observed_at"])
        if parts["journey_run_id"] != journey_run_id:
            fail(f"invalid {field}: mixed journey_run_id")
        if parts["repository_revision"].lower() != repository_revision:
            fail(f"invalid {field}: mixed repository_revision")

    owner_review = require_components(
        "owner_review",
        ("reviewer", "reviewed_at", "disposition", "follow_up_owner"),
    )
    for identity_field in ("reviewer", "follow_up_owner"):
        identity = owner_review[identity_field]
        if not re.fullmatch(r"[a-z0-9][a-z0-9._@-]{2,80}", identity, re.IGNORECASE):
            fail(f"invalid owner_review: malformed {identity_field}")
        if re.search(r"\b(?:artifact|verifier|issue-lint|bot|automation)\b", identity, re.IGNORECASE):
            fail(f"invalid owner_review: {identity_field} must be accountable")
    if owner_review["disposition"].lower() != "accepted":
        fail("invalid owner_review: disposition must be accepted")
    parse_timestamp("owner_review", owner_review["reviewed_at"])

    limitations = require_components(
        "limitation_references",
        ("ids", "owner", "decision_at", "follow_up_at"),
    )
    if not re.fullmatch(r"lim-[a-z0-9._-]+(?:,lim-[a-z0-9._-]+)*", limitations["ids"], re.IGNORECASE):
        fail("invalid limitation_references: ids must be explicit lim-* identifiers")
    if not re.fullmatch(r"[a-z0-9][a-z0-9._@-]{2,80}", limitations["owner"], re.IGNORECASE):
        fail("invalid limitation_references: owner must be accountable")
    decision_at = parse_timestamp("limitation_references", limitations["decision_at"])
    follow_up_at = parse_timestamp(
        "limitation_references",
        limitations["follow_up_at"],
        fresh=False,
        allow_future=True,
    )
    if follow_up_at <= decision_at:
        fail("invalid limitation_references: follow_up_at must be after decision_at")

    required_non_claims = {
        "rc-evidence-only",
        "not-rc-gate-pass",
        "not-ga",
        "not-production-operations",
        "not-commercial-replacement",
        "not-broad-siem-parity",
        "not-broad-soar-parity",
        "not-subordinate-truth",
    }
    non_claims = {item.strip().lower() for item in field_value("non_claims").split(",") if item.strip()}
    if non_claims != required_non_claims:
        missing = sorted(required_non_claims - non_claims)
        extra = sorted(non_claims - required_non_claims)
        detail = []
        if missing:
            detail.append("missing " + ", ".join(missing))
        if extra:
            detail.append("unexpected " + ", ".join(extra))
        fail("invalid non_claims: " + "; ".join(detail))

sensitive_assignment = re.compile(
    r"(?:^|[;,\s{|])`?(?:password|passwd|secret|client_secret|api_key|access_token|refresh_token|private_key|authorization)`?\s*[:=]\s*(?!\s*(?:redacted|absent|rejected|forbidden|removed)\b)(?:[\"'][^\"'\r\n]{4,}[\"']|[^\s;,|}]{4,})",
    re.IGNORECASE,
)
secret_patterns = (
    re.compile(r"\bauthorization\s*[:=]\s*(?:bearer|basic)\s+[A-Za-z0-9_+./=-]{12,}", re.IGNORECASE),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\b(?:ghp_|github_pat_)[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"[A-Za-z][A-Za-z0-9+.-]*://[^\s/:@]+:[^\s@]+@"),
    re.compile(r"-----(?:BEGIN|END) [A-Z0-9 ._-]*(?:KEY|CERTIFICATE)[A-Z0-9 ._-]*-----", re.IGNORECASE),
)
if any(sensitive_assignment.search(line) for line in doc_raw.splitlines()) or any(
    pattern.search(doc_raw) for pattern in secret_patterns
):
    fail("production secret-looking value detected")

workstation_patterns = (
    re.compile(r"(?:^|[\s`\"'(<:=])/(?:Users|home)/[^\s`\"'()<>/]+/", re.IGNORECASE),
    re.compile(r"(?:^|[\s`\"'(<:=])/(?:root)(?:/|$)", re.IGNORECASE),
    re.compile(r"(?:^|[\s`\"'(<:=])~/(?:[^\s`\"'()<>]+)", re.IGNORECASE),
    re.compile(r"(?:^|[\s`\"'(<:=])[A-Za-z]:[\\/]Users[\\/][^\s`\"'()<>\\/]+[\\/]", re.IGNORECASE),
    re.compile(r"file://(?:[^\s`\"'()<>]*/)?(?:(?:Users|home)/[^\s`\"'()<>/]+|root)/", re.IGNORECASE),
)
if any(pattern.search(doc_raw) for pattern in workstation_patterns):
    fail("workstation-local path detected")

email_pattern = re.compile(
    r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?![A-Za-z0-9.-])"
)
private_assignment = re.compile(
    r"(?:^|[;,\s{|])`?(?:customer[_ -]?(?:name|identifier|private_data|private_payload)|tenant[_ -]?(?:name|identifier)|ticket[_ -]?private[_ -]?content|raw[_ -]?(?:customer|ticket)[_ -]?(?:data|payload|content))`?\s*[:=]\s*(?!\s*(?:redacted|absent|rejected|forbidden|removed)\b)(?:[\"'][^\"'\r\n]{2,}[\"']|[^\s;,|}]{2,})",
    re.IGNORECASE,
)
private_data_claim = re.compile(
    r"\b(?:includes?|contains?|retains?|stores?|embeds?|exports?|captures?|publishes?)\b.{0,60}\b(?:raw customer|customer[- ]private|private ticket|raw ticket|raw payload|customer identifier)",
    re.IGNORECASE,
)
if email_pattern.search(doc_raw) or any(private_assignment.search(line) for line in doc_raw.splitlines()):
    fail("customer-private or ticket-private data detected")
for line in doc_raw.splitlines():
    match = private_data_claim.search(line)
    if match and not re.search(
        r"\b(?:cannot|does not|must not|never|rejects?|forbids?|without|redacts?|removes?)\b",
        line[: match.end()],
        re.IGNORECASE,
    ):
        fail("customer-private or ticket-private data detected")

subordinate_subject = (
    r"(?:this\s+proof(?:\s+pack)?|phase\s+66\.7|proof\s+pack|wazuh|shuffle|ai(?:\s+output)?|tickets?|"
    r"evidence\s+systems?|external\s+evidence|browser\s+state|ui\s+cache|demo\s+data|reports?|"
    r"support\s+bundles?|release\s+artifacts?|verifier\s+output|issue-lint\s+output)"
)
truth_outcome = (
    r"(?:authoritative|(?:workflow|alert|case|evidence|approval|execution|reconciliation|release|gate|"
    r"limitation|readiness|closeout|source)\s+truth|source\s+of\s+truth|rc\s+gate\s+(?:pass|decision))"
)
readiness_outcome = (
    r"(?:rc\s+(?:gate\s+pass|readiness)|release[- ]candidate\s+readiness|ga(?:\s+readiness|\s+gate\s+pass)?|"
    r"general\s+availability|production\s+(?:readiness|rollout|operations)|commercial\s+replacement|"
    r"broad\s+(?:enterprise\s+)?(?:siem|soar)(?:\s+parity)?)"
)
authority_action = (
    r"(?:approv(?:e|es|ed|ing)|execut(?:e|es|ed|ing)|reconcil(?:e|es|ed|ing)|"
    r"clos(?:e|es|ed|ing)(?:\s+the)?\s+cases?|admit(?:s|ted|ting)?|"
    r"releas(?:e|es|ed|ing)|gat(?:e|es|ed|ing)|overrid(?:e|es|den|ing))"
)
claim_patterns = (
    re.compile(
        rf"\b{subordinate_subject}\b.{{0,120}}\b(?:is|are|becomes?|serves?\s+as|acts?\s+as|owns?|defines?|determines?)\b.{{0,80}}\b{truth_outcome}\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b{subordinate_subject}\b.{{0,100}}\b(?:can|could|may|might|will|would|does|do|automatically|independently|directly)\b.{{0,60}}\b{authority_action}\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b{subordinate_subject}\b.{{0,100}}\b(?:proves?|confirms?|establishes?|satisfies?|passes?|grants?|achieves?|certifies?|validates?)\b.{{0,100}}\b{readiness_outcome}\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b{readiness_outcome}\b.{{0,100}}\b(?:is|are|was|were|has\s+been|have\s+been)\s+(?:proven|confirmed|established|satisfied|passed|achieved|validated)\b.{{0,100}}\bby\b.{{0,80}}\b{subordinate_subject}\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b{truth_outcome}\b.{{0,80}}\b(?:is|are|was|were|has\s+been|have\s+been)\s+(?:owned|defined|provided|established|determined|controlled)\b.{{0,80}}\bby\b.{{0,80}}\b{subordinate_subject}\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?:aegisops|phase\s+66\.7|this\s+proof(?:\s+pack)?|proof\s+pack)\b.{{0,80}}\b(?:is|are|becomes?|delivers?|enables?|provides?)\b.{{0,80}}\b{readiness_outcome}\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:approval|execution|reconciliation)\s+bypass\b.{0,50}\b(?:is|are|becomes?|remains?)\s+(?:allowed|accepted|supported|valid)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:case[- ]closure|source[- ]admission)\s+shortcut\b.{0,50}\b(?:is|are|becomes?|remains?)\s+(?:allowed|accepted|supported|valid)\b",
        re.IGNORECASE,
    ),
)
denial_pattern = re.compile(
    r"\b(?:cannot|can't|does\s+not|do\s+not|did\s+not|will\s+not|would\s+not|should\s+not|"
    r"may\s+not|must\s+not|not|never|no\s+longer|reject(?:s|ed|ing)?|forbid(?:s|den|ding)?|"
    r"exclud(?:e|es|ed|ing)|without|remains?\s+subordinate|evidence\s+only)\b",
    re.IGNORECASE,
)


def claim_clauses(text: str):
    normalized = re.sub(r"[`*_#|]", " ", text)
    normalized = re.sub(r"\s+", " ", normalized)
    inherited_subject = ""
    for clause in re.split(
        r"\s*(?:(?<!\d)[.!?](?!\d)|;|\bbut\b|\bhowever\b|\byet\b|\balthough\b|\bthough\b)\s*",
        normalized,
        flags=re.IGNORECASE,
    ):
        clause = clause.strip()
        if not clause:
            continue
        subject_match = re.search(subordinate_subject, clause, re.IGNORECASE)
        if subject_match:
            inherited_subject = subject_match.group(0)
        elif inherited_subject and re.match(r"^(?:it|they|this)\b", clause, re.IGNORECASE):
            clause = re.sub(r"^(?:it|they|this)\b", inherited_subject, clause, flags=re.IGNORECASE)
        yield clause


claim_scan_doc = doc_raw.replace(
    "Phase 66.7 does not add runtime feature breadth, execute production operations, grant new AI or integration authority, prove real design-partner outcomes, complete production rollout, implement commercial billing or entitlement enforcement, prove Phase 67 GA readiness, or claim broad enterprise SIEM/SOAR parity.",
    "",
)
claim_inputs = (
    claim_scan_doc,
    "\n".join(
        line
        for line in readme_raw.splitlines()
        if re.search(r"phase\s+66\.7|authority-boundary\s+proof\s+pack", line, re.IGNORECASE)
    ),
)
for claim_input in claim_inputs:
    for clause in claim_clauses(claim_input):
        for pattern in claim_patterns:
            match = pattern.search(clause)
            if match and not denial_pattern.search(match.group(0)):
                if os.environ.get("PHASE66_7_DEBUG") == "1":
                    print(f"Matched overclaim: {match.group(0)}", file=sys.stderr)
                fail("authority or readiness overclaim detected")

print("Phase 66.7 proof-pack document, evidence schema, secret hygiene, and authority checks pass.")
PY

if [[ "${PHASE66_7_SKIP_PATH_HYGIENE:-0}" != "1" ]]; then
  tmp_dir="$(mktemp -d)"
  trap 'rm -rf "${tmp_dir}"' EXIT
  path_hygiene_stderr="${tmp_dir}/path-hygiene.err"
  if ! bash "${repo_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" >/dev/null 2>"${path_hygiene_stderr}"; then
    cat "${path_hygiene_stderr}" >&2
    echo "Forbidden Phase 66.7 RC authority-boundary proof pack: publishable path hygiene failed" >&2
    exit 1
  fi
fi

echo "Phase 66.7 RC authority-boundary proof-pack contract and focused negative checks pass."
