#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
repo_root="$(cd "${repo_root}" && pwd -P)"

doc_path="docs/phase-66-6-rc-supportability-proof.md"
absolute_doc_path="${repo_root}/${doc_path}"
readme_path="${repo_root}/README.md"

required_reference_paths=(
  "docs/phase-66-1-clean-host-rc-e2e-harness.md"
  "docs/phase-58-3-backup-command-contract.md"
  "docs/phase-58-4-restore-dry-run-contract.md"
  "docs/phase-58-5-upgrade-rollback-plan-contract.md"
  "docs/phase-58-6-support-bundle-redaction-contract.md"
  "docs/phase-51-6-authority-boundary-negative-test-policy.md"
  "docs/phase-65-closeout-evaluation.md"
)

required_verifier_scripts=(
  "scripts/verify-phase-66-6-rc-supportability-proof.sh"
  "scripts/test-verify-phase-66-6-rc-supportability-proof.sh"
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

require_file "${absolute_doc_path}" "Phase 66.6 RC supportability proof"
require_file "${readme_path}" "README for Phase 66.6 link check"

for reference_path in "${required_reference_paths[@]}"; do
  require_file "${repo_root}/${reference_path}" "Phase 66.6 reference ${reference_path}"
done

for verifier_script in "${required_verifier_scripts[@]}"; do
  require_file "${repo_root}/${verifier_script}" "Phase 66.6 verifier script ${verifier_script}"
done

python3 - "${absolute_doc_path}" "${readme_path}" "${repo_root}" <<'PY'
from __future__ import annotations

import os
import re
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
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
    return re.sub(r"^[ \t]*(```|~~~).*?^[ \t]*\1[ \t]*$", "", text, flags=re.DOTALL | re.MULTILINE)


doc_semantic = semantic_text(doc_raw)
readme_semantic = semantic_text(readme_raw)

readme_phrases = (
    "- [Phase 66.6 RC supportability proof](docs/phase-66-6-rc-supportability-proof.md) defines the reviewed backup, restore dry-run, upgrade, rollback, support-bundle, redaction, owner-review, limitation, and non-claim evidence surface while preserving AegisOps records as workflow, release, gate, limitation, and closeout truth and excluding GA, production support, customer portal, and commercial replacement claims.",
    "The Phase 66.6 RC supportability proof is defined by the [Phase 66.6 RC supportability proof](docs/phase-66-6-rc-supportability-proof.md).",
)

for phrase in readme_phrases:
    if phrase not in readme_semantic:
        print(f"Missing README canonical Phase 66.6 boundary statement: {phrase}", file=sys.stderr)
        raise SystemExit(1)

required_phrases = (
    "# Phase 66.6 RC Supportability Proof",
    "**Status**: Accepted as the Phase 66.6 RC supportability proof contract for release-candidate evidence planning only.",
    "**Related Issues**: #1397, #1403",
    "This contract defines the Phase 66.6 RC supportability proof surface.",
    "The proof depends on the Phase 66.1 clean-host RC E2E harness and the Phase 58 supportability contracts.",
    "This proof is RC evidence only.",
    "A proof packet is fail-closed: once any required field is materialized, every required field must be present, non-placeholder, internally complete, and bound to the same journey run and immutable repository revision.",
    "AegisOps records remain authoritative for workflow, release, gate, restore acceptance, limitation, audit, approval, action request, execution receipt, reconciliation, source admission, and closeout truth.",
    "Backup manifests, restore dry-run output, upgrade plans, rollback plans, support bundles, redaction manifests, owner-review summaries, limitation lists, verifier output, issue-lint output, browser state, UI cache, tickets, and optional evidence remain subordinate evidence.",
    "The proof must reject missing or partial evidence packets, mixed revisions, stale or failed evidence, placeholder values, secret leakage, raw credential leakage, customer-private data, ticket-private content, authorization material, certificate or key material, workstation-local paths, support-bundle-as-truth claims, support-operator authority expansion, live restore claims, live upgrade or rollback claims, inferred RC pass, inferred GA pass, production SLA commitments, 24x7 support claims, customer portal claims, real design-partner support claims, commercial replacement claims, verifier-as-readiness-truth, and issue-lint-as-readiness-truth.",
    "Materialized evidence timestamps must be no more than 24 hours old at verification time and must not be more than five minutes in the future.",
    "Later Phase 66 issues must still prove the RC authority-boundary proof pack and closeout evidence independently.",
    "Run `bash scripts/verify-phase-66-6-rc-supportability-proof.sh`.",
    "Run `bash scripts/test-verify-phase-66-6-rc-supportability-proof.sh`.",
    "Run `bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh`.",
    "Run `bash scripts/verify-publishable-path-hygiene.sh`.",
    "Run `node <codex-supervisor-root>/dist/index.js issue-lint 1397 --config <supervisor-config-path>`.",
    "Run `node <codex-supervisor-root>/dist/index.js issue-lint 1403 --config <supervisor-config-path>`.",
)

for phrase in required_phrases:
    if phrase not in doc_semantic:
        print(f"Missing Phase 66.6 RC supportability proof statement: {phrase}", file=sys.stderr)
        raise SystemExit(1)

required_references = (
    "docs/phase-66-1-clean-host-rc-e2e-harness.md",
    "docs/phase-58-3-backup-command-contract.md",
    "docs/phase-58-4-restore-dry-run-contract.md",
    "docs/phase-58-5-upgrade-rollback-plan-contract.md",
    "docs/phase-58-6-support-bundle-redaction-contract.md",
    "docs/phase-51-6-authority-boundary-negative-test-policy.md",
    "docs/phase-65-closeout-evaluation.md",
)

for reference in required_references:
    if f"`{reference}`" not in doc_semantic:
        print(f"Missing Phase 66.6 required reference citation: {reference}", file=sys.stderr)
        raise SystemExit(1)


def section(text: str, heading: str, next_heading: str) -> str:
    start = text.find(heading)
    if start < 0:
        return ""
    end = text.find(next_heading, start + len(heading))
    return text[start:] if end < 0 else text[start:end]


evidence_section = section(
    doc_semantic,
    "## 2. RC Supportability Evidence",
    "## 3. Evidence Binding And Secret Hygiene",
)

evidence_rows = (
    "| `journey_run_id` | The Phase 66.1 run identifier that observed the supportability evidence set. | Missing, placeholder, or mismatched journey identifiers fail the proof. |",
    "| `repository_revision` | One immutable 40-character repository revision shared by the evidence set. | Mutable branches, tags, abbreviated revisions, or mixed revisions fail the proof. |",
    "| `backup_evidence` | Reviewed backup manifest identity, custody reference, creation timestamp, owner, and completed status. | A manifest alone cannot prove restore success or release readiness. |",
    "| `restore_dry_run_evidence` | Reviewed dry-run identity, source backup reference, target profile, timestamp, operator, and passed result. | Dry-run output cannot prove live restore completion or mutate authoritative records. |",
    "| `upgrade_plan` | Reviewed plan identity, exact before and after versions, target profile, passed preflight reference, and AegisOps evidence links. | Floating versions, missing preflight evidence, or plan-as-release-truth claims fail the proof. |",
    "| `rollback_plan` | Reviewed plan identity, backup reference, accountable rollback owner, trigger, and rollback target. | Missing ownership, vague triggers, or plan-driven substrate mutation fail the proof. |",
    "| `support_bundle` | Reviewed bundle identity, environment class, component versions, doctor summary, backup/restore references, upgrade/rollback references, timestamp, owner, and AegisOps evidence links. | Missing provenance, mixed snapshots, or bundle-as-truth claims fail the proof. |",
    "| `redaction_manifest` | Reviewed manifest identity, passed scan result, all Phase 58.6 redaction families, and explicit subordinate-evidence boundary. | Secret, credential, customer-private, ticket-private, token, header, certificate, or workstation-path leakage fails the proof. |",
    "| `owner_review` | Reviewer, review timestamp, disposition, accepted-risk posture, and follow-up owner. | Missing review, self-approval by an artifact, or unowned follow-up fails the proof. |",
    "| `limitation_references` | Known limitation ids, owner, decision date, and follow-up date for incomplete evidence. | Hidden, missing, or unowned limitations fail the proof. |",
    "| `non_claims` | Explicit `rc-evidence-only`, `not-rc-gate-pass`, `not-ga`, `not-production-support`, `not-customer-portal`, `not-commercial-replacement`, and `not-support-truth` labels. | Missing labels or positive readiness claims fail the proof. |",
)

for row in evidence_rows:
    if row not in evidence_section:
        print(f"Missing Phase 66.6 RC supportability evidence row: {row}", file=sys.stderr)
        raise SystemExit(1)

binding_section = section(
    doc_semantic,
    "## 3. Evidence Binding And Secret Hygiene",
    "## 4. Authority Boundary",
)

binding_phrases = (
    "Every structured evidence value must include the packet's exact `journey_run_id` and `repository_revision`; implicit binding through names, paths, or ticket context is not accepted.",
    "The `backup_evidence` value must include `journey_run_id`, `repository_revision`, `manifest_id`, `custody_reference`, `created_at`, `owner`, and `status=completed`.",
    "Accountable people and groups must use explicit `person:<id>` or `group:<id>` identities; broad operator labels and automated identities are not accepted.",
    "The `restore_dry_run_evidence` value must include `journey_run_id`, `repository_revision`, `dry_run_id`, `evidence_reference`, `backup_reference`, `target_profile`, `created_at`, `operator`, and `result=passed`.",
    "The `upgrade_plan` value must include `journey_run_id`, `repository_revision`, `plan_id`, `evidence_reference`, `version_before`, `version_after`, `target_profile`, `preflight_result`, and `evidence_links`.",
    "The `rollback_plan` value must include `journey_run_id`, `repository_revision`, `plan_id`, `evidence_reference`, `backup_reference`, `rollback_owner`, `rollback_trigger`, and `rollback_target`.",
    "The `support_bundle` value must include `journey_run_id`, `repository_revision`, `bundle_id`, `evidence_reference`, `environment_class`, `component_versions`, `doctor_summary`, `backup_restore_references`, `upgrade_rollback_references`, `created_at`, `owner`, and `evidence_links`.",
    "The `redaction_manifest` value must include `journey_run_id`, `repository_revision`, `manifest_id`, `evidence_reference`, `bundle_reference`, `scan_result=passed`, `secret_values`, `workstation_paths`, `private_payloads`, `ticket_private_content`, `tokens_and_headers`, `certs_and_keys`, `credentials`, `customer_identifiers`, and `authority_boundary=subordinate-evidence-only`.",
    "The `owner_review` value must include `journey_run_id`, `repository_revision`, `reviewer`, `reviewed_references`, `reviewed_at`, `disposition`, `accepted_risk`, and `follow_up_owner`.",
    "The `limitation_references` value must include `journey_run_id`, `repository_revision`, `ids`, `owner`, `decision_date`, and `follow_up_date`.",
)

for phrase in binding_phrases:
    if phrase not in binding_section:
        print(f"Missing Phase 66.6 evidence binding statement: {phrase}", file=sys.stderr)
        raise SystemExit(1)


required_fields = (
    "journey_run_id",
    "repository_revision",
    "backup_evidence",
    "restore_dry_run_evidence",
    "upgrade_plan",
    "rollback_plan",
    "support_bundle",
    "redaction_manifest",
    "owner_review",
    "limitation_references",
    "non_claims",
)

required_field_set = set(required_fields)
field_values: dict[str, list[str]] = {field: [] for field in required_fields}
section_field_values: dict[str, dict[str, list[str]]] = {}
current_section = "document-preamble"
section_index = 0
in_fence = False
assignment_pattern = re.compile(
    r"^\s*(?:[-*>]\s*)?`?(" + "|".join(map(re.escape, required_fields)) + r")`?\s*[:=]\s*(.*?)\s*$",
    re.IGNORECASE,
)
table_pattern = re.compile(r"^\s*\|\s*`?([a-z0-9_]+)`?\s*\|\s*(.*?)\s*\|", re.IGNORECASE)
canonical_evidence_rows = {row.strip() for row in evidence_rows}


def record_field(section_name: str, field: str, value: str) -> None:
    field_values[field].append(value)
    section_values = section_field_values.setdefault(
        section_name,
        {required_field: [] for required_field in required_fields},
    )
    section_values[field].append(value)

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
    match = assignment_pattern.match(raw_line)
    if match:
        record_field(current_section, match.group(1).lower(), match.group(2).strip().strip("`"))
        continue
    match = table_pattern.match(raw_line)
    if match and stripped not in canonical_evidence_rows:
        key = match.group(1).lower()
        if key in required_field_set:
            record_field(current_section, key, match.group(2).strip().strip("`"))

for section_name, section_values in section_field_values.items():
    section_materialized_fields = {field for field, values in section_values.items() if values}
    if not section_materialized_fields:
        continue
    section_missing_fields = sorted(required_field_set - section_materialized_fields)
    if section_missing_fields:
        print(
            "Forbidden Phase 66.6 RC supportability proof: partial evidence packet in "
            + section_name.split(":", 1)[-1]
            + "; missing "
            + ", ".join(section_missing_fields),
            file=sys.stderr,
        )
        raise SystemExit(1)
    duplicate_section_fields = sorted(field for field, values in section_values.items() if len(values) != 1)
    if duplicate_section_fields:
        print(
            "Forbidden Phase 66.6 RC supportability proof: multiple materialized values in "
            + section_name.split(":", 1)[-1]
            + " for "
            + ", ".join(duplicate_section_fields),
            file=sys.stderr,
        )
        raise SystemExit(1)

materialized_fields = {field for field, values in field_values.items() if values}
if materialized_fields:
    missing_fields = sorted(required_field_set - materialized_fields)
    if missing_fields:
        print(
            "Forbidden Phase 66.6 RC supportability proof: partial evidence packet; missing "
            + ", ".join(missing_fields),
            file=sys.stderr,
        )
        raise SystemExit(1)
    duplicate_fields = sorted(field for field, values in field_values.items() if len(values) != 1)
    if duplicate_fields:
        print(
            "Forbidden Phase 66.6 RC supportability proof: multiple materialized values across evidence packets for "
            + ", ".join(duplicate_fields),
            file=sys.stderr,
        )
        raise SystemExit(1)


placeholder_pattern = re.compile(
    r"(?:^|[^a-z0-9])(?:todo|tbd|tbc|unknown|none|null|n/?a|pending|sample|example|fake|placeholder|omitted|missing|unavailable|not[- _]?available)(?:$|[^a-z0-9])",
    re.IGNORECASE,
)


def fail_field(field: str, detail: str) -> None:
    print(f"Forbidden Phase 66.6 RC supportability proof: invalid {field}: {detail}", file=sys.stderr)
    raise SystemExit(1)


def parse_parts(field: str, value: str) -> dict[str, str]:
    parts: dict[str, str] = {}
    for item in re.split(r"\s*;\s*", value.strip().strip("`")):
        if not item:
            continue
        if "=" not in item:
            fail_field(field, f"unstructured component {item!r}")
        key, component_value = item.split("=", 1)
        key = key.strip().lower()
        component_value = component_value.strip().strip("`")
        if not re.fullmatch(r"[a-z][a-z0-9_]*", key):
            fail_field(field, f"invalid component name {key!r}")
        if key in parts:
            fail_field(field, f"duplicate component {key}")
        parts[key] = component_value
    return parts


def require_components(field: str, value: str, required: tuple[str, ...]) -> dict[str, str]:
    parts = parse_parts(field, value)
    missing = [component for component in required if component not in parts]
    if missing:
        fail_field(field, "missing components " + ", ".join(missing))
    for component in required:
        component_value = parts[component].strip()
        if not component_value or placeholder_pattern.search(component_value):
            fail_field(field, f"placeholder component {component}")
    return parts


timestamp_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})$")
evidence_freshness_window = timedelta(hours=24)
allowed_future_skew = timedelta(minutes=5)
date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
immutable_revision_pattern = re.compile(r"^[0-9a-f]{40}$", re.IGNORECASE)
exact_version_pattern = re.compile(
    r"^v?(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(?:\+[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?$"
)
prerelease_label_pattern = re.compile(r"(?<![a-z0-9])(?:alpha|beta|rc)[.-]?\d*(?![a-z0-9])", re.IGNORECASE)
component_version_pattern = re.compile(
    r"^(?P<component>[a-z0-9][a-z0-9._-]*)-(?P<version>v?(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(?:\+[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?)$",
    re.IGNORECASE,
)
reference_pattern = re.compile(
    r"^aegisops://[a-z0-9][a-z0-9._~-]*(?:/[a-z0-9][a-z0-9._~%+-]*)*$",
    re.IGNORECASE,
)
accountable_identity_pattern = re.compile(r"^(?:person|group):[a-z0-9][a-z0-9._-]{2,}$", re.IGNORECASE)
automated_identity_pattern = re.compile(
    r"(?<![a-z0-9])(?:bot|ci|automation|robot|service[-_]?account|github[-_]?actions|workflow|verifier|issue[-_]?lint|artifact)(?![a-z0-9])",
    re.IGNORECASE,
)
broad_identity_pattern = re.compile(
    r"^(?:person|group):(?:operator|operators|team|anyone|on-call|support|admin|administrator)$",
    re.IGNORECASE,
)


def require_timestamp(field: str, name: str, value: str) -> datetime:
    if not timestamp_pattern.fullmatch(value):
        fail_field(field, f"{name} must be an RFC3339 timestamp")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        fail_field(field, f"{name} must be an RFC3339 timestamp")


def require_stable_version(field: str, name: str, value: str) -> None:
    if not exact_version_pattern.fullmatch(value) or prerelease_label_pattern.search(value):
        fail_field(field, f"{name} must be an exact stable version")


def require_accountable_identity(field: str, name: str, value: str) -> None:
    if (
        not accountable_identity_pattern.fullmatch(value)
        or automated_identity_pattern.search(value)
        or broad_identity_pattern.fullmatch(value)
    ):
        fail_field(field, f"{name} must identify an accountable person or group")


def require_packet_binding(
    field: str,
    parts: dict[str, str],
    journey_run_id: str,
    repository_revision: str,
) -> None:
    if parts["journey_run_id"] != journey_run_id:
        fail_field(field, "journey_run_id must match the proof packet")
    if parts["repository_revision"].lower() != repository_revision:
        fail_field(field, "repository_revision must match the proof packet")


def require_date(field: str, name: str, value: str) -> date:
    if not date_pattern.fullmatch(value):
        fail_field(field, f"{name} must be an ISO date")
    try:
        return date.fromisoformat(value)
    except ValueError:
        fail_field(field, f"{name} must be an ISO date")


def require_aegisops_reference(field: str, name: str, value: str) -> set[str]:
    reference_value = value
    if reference_value.lower().startswith("passed:"):
        reference_value = reference_value[len("passed:") :]
    references = [reference for reference in re.split(r"[\s,]+", reference_value) if reference]
    if not references or any(not reference_pattern.fullmatch(reference) for reference in references):
        fail_field(field, f"{name} must include a direct AegisOps evidence reference")
    if len(references) != len(set(references)):
        fail_field(field, f"{name} must not contain duplicate evidence references")
    return set(references)


def require_single_aegisops_reference(field: str, name: str, value: str) -> str:
    references = require_aegisops_reference(field, name, value)
    if len(references) != 1:
        fail_field(field, f"{name} must contain exactly one evidence reference")
    return next(iter(references))


if materialized_fields:
    journey_run_id = field_values["journey_run_id"][0]
    revisions = {value.lower() for value in field_values["repository_revision"]}
    if len(revisions) != 1 or not immutable_revision_pattern.fullmatch(next(iter(revisions))):
        fail_field("repository_revision", "expected one immutable 40-character revision")
    repository_revision = next(iter(revisions))
    try:
        revision_check = subprocess.run(
            ["git", "-C", str(repo_root), "cat-file", "-e", f"{repository_revision}^{{commit}}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        fail_field("repository_revision", "revision cannot be resolved in the target repository")
    if revision_check.returncode != 0:
        fail_field("repository_revision", "revision does not resolve to a commit in the target repository")

    for field, values in field_values.items():
        for value in values:
            if not value or placeholder_pattern.search(value):
                fail_field(field, "missing or placeholder value")

    backup_references: set[str] = set()
    restore_backup_references: set[str] = set()
    rollback_backup_references: set[str] = set()
    restore_target_profiles: set[str] = set()
    upgrade_target_profiles: set[str] = set()
    restore_evidence_references: set[str] = set()
    upgrade_evidence_references: set[str] = set()
    rollback_evidence_references: set[str] = set()
    bundle_evidence_references: set[str] = set()
    redaction_evidence_references: set[str] = set()
    bundle_backup_restore_references: set[str] = set()
    bundle_upgrade_rollback_references: set[str] = set()
    redaction_bundle_references: set[str] = set()
    owner_review_references: set[str] = set()
    backup_created_at: datetime | None = None
    restore_created_at: datetime | None = None
    bundle_created_at: datetime | None = None
    reviewed_at: datetime | None = None

    for value in field_values["backup_evidence"]:
        parts = require_components(
            "backup_evidence",
            value,
            ("journey_run_id", "repository_revision", "manifest_id", "custody_reference", "created_at", "owner", "status"),
        )
        require_packet_binding("backup_evidence", parts, journey_run_id, repository_revision)
        backup_references.add(
            require_single_aegisops_reference("backup_evidence", "custody_reference", parts["custody_reference"])
        )
        backup_created_at = require_timestamp("backup_evidence", "created_at", parts["created_at"])
        require_accountable_identity("backup_evidence", "owner", parts["owner"])
        if parts["status"].lower() != "completed":
            fail_field("backup_evidence", "status must be completed")

    for value in field_values["restore_dry_run_evidence"]:
        parts = require_components(
            "restore_dry_run_evidence",
            value,
            ("journey_run_id", "repository_revision", "dry_run_id", "evidence_reference", "backup_reference", "target_profile", "created_at", "operator", "result"),
        )
        require_packet_binding("restore_dry_run_evidence", parts, journey_run_id, repository_revision)
        restore_evidence_references.add(
            require_single_aegisops_reference(
                "restore_dry_run_evidence", "evidence_reference", parts["evidence_reference"]
            )
        )
        restore_backup_references.add(
            require_single_aegisops_reference(
                "restore_dry_run_evidence", "backup_reference", parts["backup_reference"]
            )
        )
        restore_target_profiles.add(parts["target_profile"])
        restore_created_at = require_timestamp("restore_dry_run_evidence", "created_at", parts["created_at"])
        require_accountable_identity("restore_dry_run_evidence", "operator", parts["operator"])
        if parts["result"].lower() != "passed":
            fail_field("restore_dry_run_evidence", "result must be passed")

    for value in field_values["upgrade_plan"]:
        parts = require_components(
            "upgrade_plan",
            value,
            ("journey_run_id", "repository_revision", "plan_id", "evidence_reference", "version_before", "version_after", "target_profile", "preflight_result", "evidence_links"),
        )
        require_packet_binding("upgrade_plan", parts, journey_run_id, repository_revision)
        upgrade_evidence_references.add(
            require_single_aegisops_reference("upgrade_plan", "evidence_reference", parts["evidence_reference"])
        )
        require_stable_version("upgrade_plan", "version_before", parts["version_before"])
        require_stable_version("upgrade_plan", "version_after", parts["version_after"])
        normalized_version_before = parts["version_before"].lower().removeprefix("v")
        normalized_version_after = parts["version_after"].lower().removeprefix("v")
        if normalized_version_before == normalized_version_after:
            fail_field("upgrade_plan", "version_before and version_after must differ")
        upgrade_target_profiles.add(parts["target_profile"])
        if not parts["preflight_result"].lower().startswith("passed:"):
            fail_field("upgrade_plan", "preflight_result must be passed with evidence")
        require_aegisops_reference("upgrade_plan", "preflight_result", parts["preflight_result"])
        require_aegisops_reference("upgrade_plan", "evidence_links", parts["evidence_links"])

    for value in field_values["rollback_plan"]:
        parts = require_components(
            "rollback_plan",
            value,
            ("journey_run_id", "repository_revision", "plan_id", "evidence_reference", "backup_reference", "rollback_owner", "rollback_trigger", "rollback_target"),
        )
        require_packet_binding("rollback_plan", parts, journey_run_id, repository_revision)
        rollback_evidence_references.add(
            require_single_aegisops_reference("rollback_plan", "evidence_reference", parts["evidence_reference"])
        )
        rollback_backup_references.add(
            require_single_aegisops_reference("rollback_plan", "backup_reference", parts["backup_reference"])
        )
        require_accountable_identity("rollback_plan", "rollback_owner", parts["rollback_owner"])
        trigger_match = re.fullmatch(
            r"(?:failed|rejected|threshold-breached):(aegisops://[^\s,]+)",
            parts["rollback_trigger"],
            re.IGNORECASE,
        )
        if trigger_match is None or not reference_pattern.fullmatch(trigger_match.group(1)):
            fail_field(
                "rollback_plan",
                "rollback_trigger must identify actionable failed, rejected, or threshold-breached evidence",
            )
        require_single_aegisops_reference("rollback_plan", "rollback_target", parts["rollback_target"])

    if (
        len(backup_references) != 1
        or restore_backup_references != backup_references
        or rollback_backup_references != backup_references
    ):
        fail_field(
            "recovery_binding",
            "backup references must match across backup evidence, restore dry-run evidence, and rollback plan",
        )
    if len(restore_target_profiles) != 1 or upgrade_target_profiles != restore_target_profiles:
        fail_field("target_profile_binding", "restore and upgrade target profiles must match")
    if backup_created_at is None or restore_created_at is None or restore_created_at < backup_created_at:
        fail_field("recovery_timeline", "restore evidence cannot predate backup evidence")

    for value in field_values["support_bundle"]:
        parts = require_components(
            "support_bundle",
            value,
            (
                "journey_run_id",
                "repository_revision",
                "bundle_id",
                "evidence_reference",
                "environment_class",
                "component_versions",
                "doctor_summary",
                "backup_restore_references",
                "upgrade_rollback_references",
                "created_at",
                "owner",
                "evidence_links",
            ),
        )
        require_packet_binding("support_bundle", parts, journey_run_id, repository_revision)
        bundle_evidence_references.add(
            require_single_aegisops_reference("support_bundle", "evidence_reference", parts["evidence_reference"])
        )
        bundle_created_at = require_timestamp("support_bundle", "created_at", parts["created_at"])
        require_aegisops_reference("support_bundle", "doctor_summary", parts["doctor_summary"])
        bundle_backup_restore_references.update(
            require_aegisops_reference(
                "support_bundle", "backup_restore_references", parts["backup_restore_references"]
            )
        )
        bundle_upgrade_rollback_references.update(
            require_aegisops_reference(
                "support_bundle", "upgrade_rollback_references", parts["upgrade_rollback_references"]
            )
        )
        require_aegisops_reference("support_bundle", "evidence_links", parts["evidence_links"])
        require_accountable_identity("support_bundle", "owner", parts["owner"])
        component_names: set[str] = set()
        component_entries = [entry.strip() for entry in parts["component_versions"].split(",")]
        if not component_entries or any(not entry for entry in component_entries):
            fail_field("support_bundle", "component_versions must be exact stable versions")
        for entry in component_entries:
            match = component_version_pattern.fullmatch(entry)
            if match is None:
                fail_field("support_bundle", "component_versions must be exact stable versions")
            component_name = match.group("component").lower()
            if component_name in component_names:
                fail_field("support_bundle", f"duplicate component version for {component_name}")
            component_names.add(component_name)
            require_stable_version("support_bundle", "component_versions", match.group("version"))

    if restore_created_at is None or bundle_created_at is None or bundle_created_at < restore_created_at:
        fail_field("support_bundle_timeline", "support bundle cannot predate restore evidence")
    if backup_references & restore_evidence_references:
        fail_field("support_bundle", "backup and restore evidence references must be distinct")
    if upgrade_evidence_references & rollback_evidence_references:
        fail_field("support_bundle", "upgrade and rollback evidence references must be distinct")
    if bundle_backup_restore_references != backup_references | restore_evidence_references:
        fail_field(
            "support_bundle",
            "backup_restore_references must match the packet backup and restore evidence",
        )
    if bundle_upgrade_rollback_references != upgrade_evidence_references | rollback_evidence_references:
        fail_field(
            "support_bundle",
            "upgrade_rollback_references must match the packet upgrade and rollback evidence",
        )

    redaction_components = (
        "journey_run_id",
        "repository_revision",
        "manifest_id",
        "evidence_reference",
        "bundle_reference",
        "scan_result",
        "secret_values",
        "workstation_paths",
        "private_payloads",
        "ticket_private_content",
        "tokens_and_headers",
        "certs_and_keys",
        "credentials",
        "customer_identifiers",
        "authority_boundary",
    )
    redaction_states = {"redacted", "absent", "passed"}
    for value in field_values["redaction_manifest"]:
        parts = require_components("redaction_manifest", value, redaction_components)
        require_packet_binding("redaction_manifest", parts, journey_run_id, repository_revision)
        redaction_evidence_references.add(
            require_single_aegisops_reference(
                "redaction_manifest", "evidence_reference", parts["evidence_reference"]
            )
        )
        redaction_bundle_references.add(
            require_single_aegisops_reference(
                "redaction_manifest", "bundle_reference", parts["bundle_reference"]
            )
        )
        if parts["scan_result"].lower() != "passed":
            fail_field("redaction_manifest", "scan_result must be passed")
        for name in redaction_components[6:-1]:
            if parts[name].lower() not in redaction_states:
                fail_field("redaction_manifest", f"{name} must be redacted, absent, or passed")
        if parts["authority_boundary"].lower() != "subordinate-evidence-only":
            fail_field("redaction_manifest", "authority_boundary must be subordinate-evidence-only")
    if redaction_bundle_references != bundle_evidence_references:
        fail_field("redaction_manifest", "redaction bundle_reference must match the support bundle")
    if redaction_evidence_references & bundle_evidence_references:
        fail_field("redaction_manifest", "redaction and support bundle evidence references must be distinct")

    for value in field_values["owner_review"]:
        parts = require_components(
            "owner_review",
            value,
            ("journey_run_id", "repository_revision", "reviewer", "reviewed_references", "reviewed_at", "disposition", "accepted_risk", "follow_up_owner"),
        )
        require_packet_binding("owner_review", parts, journey_run_id, repository_revision)
        require_accountable_identity("owner_review", "reviewer", parts["reviewer"])
        require_accountable_identity("owner_review", "follow_up_owner", parts["follow_up_owner"])
        owner_review_references.update(
            require_aegisops_reference("owner_review", "reviewed_references", parts["reviewed_references"])
        )
        reviewed_at = require_timestamp("owner_review", "reviewed_at", parts["reviewed_at"])
        if bundle_created_at is None or reviewed_at < bundle_created_at:
            fail_field("owner_review_timeline", "owner review cannot predate support bundle")
        if parts["disposition"].lower() not in {"accepted", "accepted-with-follow-up", "rejected"}:
            fail_field("owner_review", "unsupported disposition")
    if owner_review_references != bundle_evidence_references | redaction_evidence_references:
        fail_field("owner_review", "reviewed_references must match the support bundle and redaction manifest")
    evidence_timestamps = (backup_created_at, restore_created_at, bundle_created_at, reviewed_at)
    if any(timestamp is None for timestamp in evidence_timestamps):
        fail_field("evidence_freshness", "all evidence timestamps must be present")
    verification_time = datetime.now(timezone.utc)
    if any(timestamp > verification_time + allowed_future_skew for timestamp in evidence_timestamps if timestamp):
        fail_field("evidence_freshness", "evidence timestamp is in the future")
    if any(verification_time - timestamp > evidence_freshness_window for timestamp in evidence_timestamps if timestamp):
        fail_field("evidence_freshness", "evidence exceeds the 24-hour freshness window")

    for value in field_values["limitation_references"]:
        parts = require_components(
            "limitation_references",
            value,
            ("journey_run_id", "repository_revision", "ids", "owner", "decision_date", "follow_up_date"),
        )
        require_packet_binding("limitation_references", parts, journey_run_id, repository_revision)
        require_accountable_identity("limitation_references", "owner", parts["owner"])
        decision_date = require_date("limitation_references", "decision_date", parts["decision_date"])
        follow_up_date = require_date("limitation_references", "follow_up_date", parts["follow_up_date"])
        if follow_up_date < decision_date:
            fail_field("limitation_references", "follow_up_date cannot predate decision_date")

    required_non_claims = {
        "rc-evidence-only",
        "not-rc-gate-pass",
        "not-ga",
        "not-production-support",
        "not-customer-portal",
        "not-commercial-replacement",
        "not-support-truth",
    }
    for value in field_values["non_claims"]:
        labels = {label for label in re.split(r"[\s,;]+", value.lower()) if label}
        missing_labels = sorted(required_non_claims - labels)
        if missing_labels:
            fail_field("non_claims", "missing labels " + ", ".join(missing_labels))


credential_assignment_pattern = re.compile(
    r"(?<![A-Za-z0-9])(?:[A-Za-z0-9][A-Za-z0-9_-]*[_-])?(?:password|passwd|secret(?:[_ -]?(?:key|access[_ -]?key))?|api[_ -]?key|access[_ -]?token|token|client[_ -]?secret|private[_ -]?key)\s*[:=]\s*(?P<value>[^\r\n]*)$",
    re.IGNORECASE,
)
redaction_marker = r"\[REDACTED(?::[a-z0-9-]+)?\]"
safe_redaction_value_pattern = re.compile(
    rf"^(?:{redaction_marker}|`{redaction_marker}`|\"{redaction_marker}\"|'{redaction_marker}')[.,;:]?$",
    re.IGNORECASE,
)

for credential_line in doc_raw.splitlines():
    assignment = credential_assignment_pattern.search(credential_line)
    if assignment and not safe_redaction_value_pattern.fullmatch(assignment.group("value").strip()):
        print("Forbidden Phase 66.6 RC supportability proof: production secret-looking value detected", file=sys.stderr)
        raise SystemExit(1)

secret_patterns = (
    re.compile(r"\bauthorization\s*:\s*(?:bearer|basic)\s+[A-Za-z0-9_+./=-]{12,}", re.IGNORECASE),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\b(?:ghp_|github_pat_)[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"[A-Za-z][A-Za-z0-9+.-]*://[^\s/:@]+:[^\s@]+@"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", re.IGNORECASE),
    re.compile(
        r"-----BEGIN (?:(?:(?:TRUSTED|X\.?509) )?CERTIFICATE(?: REQUEST)?|NEW CERTIFICATE REQUEST)-----",
        re.IGNORECASE,
    ),
    re.compile(r"^\s*\|\s*`?(?:password|passwd|secret|token|api[_ -]?key|private[_ -]?key)`?\s*\|\s*`?[^\s`|<>]{4,}", re.IGNORECASE | re.MULTILINE),
)

for pattern in secret_patterns:
    if pattern.search(doc_raw):
        print("Forbidden Phase 66.6 RC supportability proof: production secret-looking value detected", file=sys.stderr)
        raise SystemExit(1)

workstation_patterns = (
    re.compile(r"(?:^|[\s`\"'(<])/(?:Users|home)/[^\s`\"'()<>/]+/", re.IGNORECASE),
    re.compile(r"(?:^|[\s`\"'(<])[A-Za-z]:[\\/]Users[\\/][^\s`\"'()<>\\/]+[\\/]", re.IGNORECASE),
    re.compile(r"file://(?:[^\s`\"'()<>]*/)?(?:Users|home)/[^\s`\"'()<>/]+/", re.IGNORECASE),
)

for pattern in workstation_patterns:
    if pattern.search(doc_raw):
        print("Forbidden Phase 66.6 RC supportability proof: workstation-local path detected", file=sys.stderr)
        raise SystemExit(1)

private_data_pattern = re.compile(
    r"\b(?:include(?:s|d|ing)?|contain(?:s|ed|ing)?|retain(?:s|ed|ing)?|store(?:s|d|ing)?|embed(?:s|ded|ding)?|export(?:s|ed|ing)?|capture(?:s|d|ing)?|carr(?:y|ies|ied|ying)|publish(?:es|ed|ing)?)\b.{0,50}\b(?:raw\s+customer|customer[- ]private|unredacted\s+customer|private\s+ticket|raw\s+ticket|private\s+support\s+note|raw\s+payload)",
    re.IGNORECASE,
)
private_assignment_pattern = re.compile(
    r"^\s*(?:[-*>]\s*)?`?(?:customer[_ -]?private(?:[_ -]?(?:data|payload))?|ticket[_ -]?private[_ -]?content|raw[_ -]?(?:customer|ticket)[_ -]?(?:data|payload|content)?)`?\s*[:=|]\s*(?!\s*(?:redacted|absent|rejected|forbidden|removed|none)\b)\S+",
    re.IGNORECASE,
)
customer_identifier_assignment_pattern = re.compile(
    r"^\s*(?:<!--\s*)?(?:[-*>]\s*)?`?(?:(?:customer|tenant)(?:[_ -]?account)?[_ -]?(?:id|identifier|name|email|host(?:name)?)|account[_ -]?(?:id|identifier|name)|email(?:[_ -]?address)?)`?\s*[:=|]\s*(?P<value>.*?)(?:\s*-->)?\s*$",
    re.IGNORECASE,
)
safe_private_value_pattern = re.compile(
    rf"^(?:{redaction_marker}|`{redaction_marker}`|\"{redaction_marker}\"|'{redaction_marker}'|redacted|absent|rejected|forbidden|removed|none)[.,;:]?$",
    re.IGNORECASE,
)
email_value_pattern = re.compile(r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?![A-Za-z0-9.-])")


def split_semantic_clauses(text: str) -> list[str]:
    return [
        clause.strip()
        for clause in re.split(
            r"\s*(?:;|\bbut\b|\bhowever\b|\byet\b|\bwhile\b|\balthough\b|\bthough\b|\band\b)\s*",
            text,
            flags=re.IGNORECASE,
        )
        if clause.strip()
    ]


def private_predicate_is_negated(clause: str, match: re.Match[str]) -> bool:
    predicate_prefix = clause[: match.start()]
    if re.search(
        r"\b(?:no|zero)\s+(?:raw\s+customer|customer[- ]private|unredacted\s+customer|private\s+ticket|raw\s+ticket|private\s+support\s+note|raw\s+payload)",
        match.group(0),
        re.IGNORECASE,
    ):
        return True
    return bool(
        re.search(
            r"(?:cannot|can't|must\s+not|does\s+not|do\s+not|did\s+not|will\s+not|should\s+not|never|forbidden\s+to|without)\s*$",
            predicate_prefix,
            re.IGNORECASE,
        )
    )

for line in doc_raw.splitlines():
    if private_assignment_pattern.search(line):
        print("Forbidden Phase 66.6 RC supportability proof: customer-private or ticket-private data detected", file=sys.stderr)
        raise SystemExit(1)
    identifier_assignment = customer_identifier_assignment_pattern.search(line)
    if identifier_assignment and not safe_private_value_pattern.fullmatch(identifier_assignment.group("value").strip()):
        print("Forbidden Phase 66.6 RC supportability proof: customer-private or ticket-private data detected", file=sys.stderr)
        raise SystemExit(1)
    if email_value_pattern.search(line):
        print("Forbidden Phase 66.6 RC supportability proof: customer-private or ticket-private data detected", file=sys.stderr)
        raise SystemExit(1)
    for private_clause in split_semantic_clauses(line):
        private_match = private_data_pattern.search(private_clause)
        if private_match and not private_predicate_is_negated(private_clause, private_match):
            print("Forbidden Phase 66.6 RC supportability proof: customer-private or ticket-private data detected", file=sys.stderr)
            raise SystemExit(1)


subordinate_subject = (
    r"(?:this\s+proof|phase\s+66\.6|supportability\s+proof|support\s+artifacts?|support\s+bundles?|bundle\s+output|"
    r"backup\s+(?:evidence|manifests?)|restore\s+dry[- ]run(?:\s+output)?|upgrade\s+plans?|rollback\s+plans?|"
    r"redaction\s+manifests?|owner[- ]review\s+summaries|limitation\s+lists?|verifier\s+output|issue-lint\s+output)"
)
broad_readiness_subject = (
    r"(?:this\s+proof|supportability\s+proof|support\s+artifacts?|support\s+bundles?|bundle\s+output|"
    r"backup\s+(?:evidence|manifests?)|restore\s+dry[- ]run(?:\s+output)?|upgrade\s+plans?|rollback\s+plans?|"
    r"redaction\s+manifests?|owner[- ]review\s+summaries|limitation\s+lists?|verifier\s+output|issue-lint\s+output)"
)
claim_verb = r"(?:proves?|confirms?|establishes?|satisfies?|passes?|grants?|achieves?|guarantees?|certifies?|validates?|demonstrates?)"
readiness_outcome = (
    r"\b(?:rc\s+(?:gate|pass|readiness)|release[- ]candidate\s+(?:gate|pass|readiness)|ga(?:\s+readiness|\s+gate|\s+pass)?|"
    r"general\s+availability|production\s+(?:readiness|support|sla)|24x7\s+support|customer\s+portal|"
    r"real\s+design[- ]partner|commercial\s+replacement|live\s+(?:restore|upgrade|rollback)(?:\s+completion)?)\b"
)
truth_outcome = (
    r"(?:(?:workflow|release|gate|restore|limitation|audit|readiness|closeout|approval|execution|reconciliation)\s+truth|"
    r"source\s+of\s+(?:workflow|release|gate|restore|limitation|audit|readiness|closeout)\s+truth)"
)
authority_action = r"(?:approves?|executes?|reconciles?|closes?|releases?|gates?|restores?|mutates?|promotes?|overrides?|replaces?)"
authority_object = r"(?:aegisops\s+records?|workflows?|releases?|gates?|restore\s+acceptance|limitations?|audits?|actions?|cases?|closeout)"
non_negated_predicate_context = (
    r"(?:(?!\b(?:cannot|can't|does\s+not|do\s+not|did\s+not|will\s+not|should\s+not|"
    r"may\s+not|must\s+not|never|no\s+longer)\b).)"
)
readiness_relation_patterns = (
    re.compile(
        rf"^\s*(?:[-:>]\s*)?(?:(?:according\s+to|based\s+on|using|with)\s+)?(?:the\s+|a\s+)?(?P<subject>{broad_readiness_subject})(?P<relation>.{{0,180}})(?P<outcome>{readiness_outcome})",
        re.IGNORECASE,
    ),
    re.compile(
        rf"^\s*(?:[-:>]\s*)?(?P<outcome>{readiness_outcome})(?P<relation>.{{0,180}})(?:the\s+|a\s+)?(?P<subject>{broad_readiness_subject})",
        re.IGNORECASE,
    ),
)
denied_relation_pattern = re.compile(
    r"\b(?:cannot|can't|does\s+not|do\s+not|did\s+not|will\s+not|should\s+not|may\s+not|must\s+not|"
    r"not|never|no(?:\s+longer)?|lacks?|fails?\s+to|without\s+(?:proving|providing|establishing|confirming|demonstrating|certifying|validating)|"
    r"reject(?:s|ed|ing)?|forbid(?:s|den|ding)?|exclud(?:e|es|ed|ing)|"
    r"den(?:y|ies|ied|ying)|disclaim(?:s|ed|ing)?)\b",
    re.IGNORECASE,
)


def readiness_relation_is_denied(relation: str) -> bool:
    predicate_scope = relation.rsplit(",", 1)[-1]
    return bool(denied_relation_pattern.search(predicate_scope))

claim_patterns = (
    re.compile(
        subordinate_subject
        + r"\s+"
        + non_negated_predicate_context
        + r"{0,120}\b"
        + claim_verb
        + r"\b.{0,140}"
        + readiness_outcome,
        re.IGNORECASE,
    ),
    re.compile(
        subordinate_subject
        + r"\s+"
        + non_negated_predicate_context
        + r"{0,120}\b(?:is|are|becomes?|serves?\s+as)\b"
        + r"(?:(?!\b(?:not|never)\b).){0,80}"
        + truth_outcome,
        re.IGNORECASE,
    ),
    re.compile(
        subordinate_subject
        + r"\s+"
        + r"(?:(?:now|already|independently|directly|automatically|effectively|itself)\s+){0,4}"
        + r"(?:(?:can|may|will|does)\s+)?"
        + authority_action
        + r"\b.{0,100}"
        + authority_object,
        re.IGNORECASE,
    ),
    re.compile(
        readiness_outcome
        + non_negated_predicate_context
        + r"{0,100}\b(?:is|are|was|were|be|been)\s+(?:proven|confirmed|established|satisfied|passed|granted|certified|validated)\b"
        + non_negated_predicate_context
        + r"{0,100}\bby\b.{0,100}"
        + subordinate_subject,
        re.IGNORECASE,
    ),
    re.compile(
        truth_outcome
        + non_negated_predicate_context
        + r"{0,80}\b(?:is|are|was|were|be|been)\s+(?:provided|established|owned|controlled|defined)\b"
        + non_negated_predicate_context
        + r"{0,80}\bby\b.{0,80}"
        + subordinate_subject,
        re.IGNORECASE,
    ),
)
support_authority_pattern = re.compile(
    r"\bsupport\s+(?:collaborator|reviewer|bundle\s+owner|agent|analyst)\b.{0,80}\b(?:is|becomes?|acts?\s+as|can|may|has\s+authority\s+to)\b(?:(?!\b(?:not|never)\b).){0,80}\b(?:operator|approver|administrator|substrate\s+operator|backend\s+authority|approve|execute|reconcile|close|release|gate|restore|mutate)\b",
    re.IGNORECASE,
)


def claim_clauses(text: str):
    normalized = re.sub(r"[`*_#|]", " ", text)
    normalized = re.sub(r"\s+", " ", normalized)
    for sentence in re.split(r"(?<=[.!?])\s+", normalized):
        inherited_subject = ""
        for clause in split_semantic_clauses(sentence):
            clause = clause.strip()
            if clause:
                yield clause
                subject_match = re.search(subordinate_subject, clause, re.IGNORECASE)
                if subject_match:
                    inherited_subject = subject_match.group(0)
                elif inherited_subject:
                    inherited_clause = re.sub(r"^(?:it|they)\s+", "", clause, flags=re.IGNORECASE)
                    yield f"{inherited_subject} {inherited_clause}"


claim_inputs = (doc_raw, "\n".join(line for line in readme_raw.splitlines() if re.search(r"phase\s+66\.6|supportability\s+proof", line, re.IGNORECASE)))
for claim_input in claim_inputs:
    for clause in claim_clauses(claim_input):
        broad_readiness_claims = [
            match
            for pattern in readiness_relation_patterns
            if (match := pattern.search(clause)) and not readiness_relation_is_denied(match.group("relation"))
        ]
        matched_claims = [index for index, pattern in enumerate(claim_patterns) if pattern.search(clause)]
        matched_support_authority = bool(support_authority_pattern.search(clause))
        if matched_support_authority or matched_claims or broad_readiness_claims:
            if os.environ.get("PHASE66_6_DEBUG") == "1":
                print(
                    f"Matched clause (support_authority={matched_support_authority}, patterns={matched_claims}, broad_readiness={[match.groupdict() for match in broad_readiness_claims]}): {clause}",
                    file=sys.stderr,
                )
            print("Forbidden Phase 66.6 RC supportability proof: authority or readiness overclaim detected", file=sys.stderr)
            raise SystemExit(1)

print("Phase 66.6 proof document, evidence schema, secret hygiene, and authority checks pass.")
PY

if [[ "${PHASE66_6_SKIP_PATH_HYGIENE:-0}" != "1" ]]; then
  tmp_dir="$(mktemp -d)"
  trap 'rm -rf "${tmp_dir}"' EXIT
  path_hygiene_stderr="${tmp_dir}/path-hygiene.err"
  if ! bash "${repo_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" >/dev/null 2>"${path_hygiene_stderr}"; then
    cat "${path_hygiene_stderr}" >&2
    echo "Forbidden Phase 66.6 RC supportability proof: publishable path hygiene failed" >&2
    exit 1
  fi
fi

echo "Phase 66.6 RC supportability proof contract and focused negative checks pass."
