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
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path

doc_path = Path(sys.argv[1])
readme_path = Path(sys.argv[2])
repo_root = Path(sys.argv[3])
doc_raw = doc_path.read_text(encoding="utf-8")
readme_raw = readme_path.read_text(encoding="utf-8")


def visible_text(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


markdown_escapable_punctuation = r"""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""
markdown_escape_pattern = re.compile(
    rf"\\([{re.escape(markdown_escapable_punctuation)}])"
)


def normalize_markdown_escapes(text: str) -> str:
    return markdown_escape_pattern.sub(r"\1", text)


class VisibleHTMLTextRenderer(HTMLParser):
    block_tags = {
        "address",
        "article",
        "aside",
        "blockquote",
        "br",
        "dd",
        "div",
        "dl",
        "dt",
        "figcaption",
        "figure",
        "footer",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "hr",
        "li",
        "main",
        "nav",
        "ol",
        "p",
        "pre",
        "section",
        "table",
        "tbody",
        "td",
        "tfoot",
        "th",
        "thead",
        "tr",
        "ul",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.suppressed_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        tag = tag.lower()
        if tag in {"script", "style"}:
            self.suppressed_depth += 1
        elif not self.suppressed_depth and tag in self.block_tags:
            self.parts.append("\n")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag.lower() in {"script", "style"}:
            self.suppressed_depth -= 1

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style"} and self.suppressed_depth:
            self.suppressed_depth -= 1
        elif not self.suppressed_depth and tag in self.block_tags:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.suppressed_depth:
            self.parts.append(data)


def rendered_text(text: str) -> str:
    parser = VisibleHTMLTextRenderer()
    parser.feed(visible_text(text))
    parser.close()
    rendered = re.sub(r"[^\S\r\n]", " ", html.unescape("".join(parser.parts)))
    return normalize_markdown_escapes(rendered)


rendered_doc_raw = rendered_text(doc_raw)
rendered_readme_raw = rendered_text(readme_raw)
rendered_source_doc_raw = normalize_markdown_escapes(
    re.sub(r"[^\S\r\n]", " ", html.unescape(doc_raw))
)


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
    "Every negative observation must record `evidence_id`, `evidence_reference`, `surface`, `attempt`, `result=rejected`, `authoritative_record`, `observed_at`, `journey_run_id`, and `repository_revision`.",
    "Every negative-observation `evidence_id` must be `sha256:<digest>` for the exact repository-owned JSON manifest bytes at `evidence_reference` and `repository_revision`.",
    "The manifest must contain exactly one matching immutable record for every required negative surface; packet labels, invented AegisOps URIs, or declared rejection results cannot substitute for a resolved record.",
    "The negative-observation manifest uses `schema_version=phase-66-7-negative-evidence/v1` and a `records` array.",
    "Every record contains exactly `field`, `surface`, `attempt`, `result`, `authoritative_record`, `observed_at`, and `journey_run_id`; missing, duplicate, extra, non-string, or packet-mismatched values fail closed.",
    "Passing one negative observation cannot compensate for a missing surface.",
    "Each Phase 66.1-66.6 evidence value must record `evidence_id`, `evidence_reference`, `verifier`, `result=passed`, `journey_run_id`, and `repository_revision`.",
    "Each Phase 66.1-66.6 `evidence_id` must be `sha256:<digest>` for the exact referenced proof document bytes at `repository_revision`.",
    "The top-level `repository_revision` identifies the evidence-producing commit, not the commit that later stores the proof packet.",
    "The verifier must check out that exact revision in an isolated worktree, resolve each required evidence reference there, and execute every Phase 66.1-66.6 focused verifier there.",
    "Packet labels or a declared `result=passed` cannot substitute for resolved proof surfaces and successful verifier execution.",
    "The same isolated worktree must resolve the negative-observation manifest, bind its exact bytes to every negative `evidence_id`, and match every packet observation to one manifest record.",
    "A syntactically valid negative observation without that immutable record fails closed.",
    "Every `owner_review` value must record `artifact_owner`, `reviewer`, `reviewed_at`, `disposition`, and `follow_up_owner`.",
    "Artifact owner and reviewer must be distinct accountable identities.",
    "Every `limitation_references` value must record `evidence_id`, `evidence_reference`, `ids`, `owner`, `decision_at`, and `follow_up_at`.",
    "The limitation manifest uses `schema_version=phase-66-7-limitations/v1` and a `limitations` array.",
    "The isolated worktree must resolve the limitation manifest and match every packet limitation to an accepted repository-owned record.",
    "Observation, review, and decision timestamps must be no more than 24 hours old at verification time and must not be more than five minutes in the future.",
    "Scheduled limitation follow-up timestamps are exempt from the five-minute future-skew limit, but must be after `decision_at` and no more than 90 days after it.",
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
if structured_key_pattern.search(normalize_markdown_escapes(doc_raw)):
    fail("JSON, YAML, and object-literal evidence syntax is not supported")

proof_field_pattern = re.compile(
    rf"\b(?:{field_alternation})\b",
    re.IGNORECASE,
)
raw_html_tag = re.compile(
    r"<\s*/?\s*[a-z][a-z0-9:-]*(?:\s+[^<>]*?)?\s*/?\s*>",
    re.IGNORECASE,
)


class RawHTMLProofFieldDetector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.frames: list[tuple[str, list[str]]] = []
        self.found = False
        self.suppressed_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        tag = tag.lower()
        if tag in {"script", "style"}:
            self.suppressed_depth += 1
        self.frames.append((tag, []))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del tag, attrs

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        matching_index = next(
            (
                index
                for index in range(len(self.frames) - 1, -1, -1)
                if self.frames[index][0] == tag
            ),
            None,
        )
        if matching_index is not None:
            for _, parts in self.frames[matching_index:]:
                if proof_field_pattern.search(
                    normalize_markdown_escapes("".join(parts))
                ):
                    self.found = True
            del self.frames[matching_index:]
        if tag in {"script", "style"} and self.suppressed_depth:
            self.suppressed_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.suppressed_depth:
            return
        for _, parts in self.frames:
            parts.append(data)

    def contains_proof_field(self) -> bool:
        return self.found or any(
            proof_field_pattern.search(normalize_markdown_escapes("".join(parts)))
            for _, parts in self.frames
        )


visible_doc_raw = normalize_markdown_escapes(visible_text(doc_raw))
html_detection_raw = re.sub(
    r"(?P<ticks>`+)[^`\n]*?(?P=ticks)",
    "",
    visible_doc_raw,
)
html_detector = RawHTMLProofFieldDetector()
html_detector.feed(html_detection_raw)
html_detector.close()
if html_detector.contains_proof_field():
    fail("raw HTML evidence syntax is not supported")
for raw_line in html_detection_raw.splitlines():
    if (
        raw_html_tag.search(raw_line)
        and proof_field_pattern.search(rendered_text(raw_line))
    ):
        fail("raw HTML evidence syntax is not supported")


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
for raw_line in rendered_doc_raw.splitlines():
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


max_follow_up_horizon = timedelta(days=90)


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

    negative_manifest_reference = "evidence/phase-66-7/negative-observations.json"
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
    negative_evidence_parts: dict[str, dict[str, str]] = {}
    for field, (expected_surface, expected_attempt) in negative_expectations.items():
        parts = require_components(
            field,
            (
                "evidence_id",
                "evidence_reference",
                "surface",
                "attempt",
                "result",
                "authoritative_record",
                "observed_at",
                "journey_run_id",
                "repository_revision",
            ),
        )
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", parts["evidence_id"], re.IGNORECASE):
            fail(f"invalid {field}: evidence_id must be sha256:<digest>")
        if parts["evidence_reference"] != negative_manifest_reference:
            fail(f"invalid {field}: unexpected evidence reference")
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
        negative_evidence_parts[field] = parts

    limitation_manifest_reference = "evidence/phase-66-7/limitations.json"
    limitations = require_components(
        "limitation_references",
        ("evidence_id", "evidence_reference", "ids", "owner", "decision_at", "follow_up_at"),
    )
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", limitations["evidence_id"], re.IGNORECASE):
        fail("invalid limitation_references: evidence_id must be sha256:<digest>")
    if limitations["evidence_reference"] != limitation_manifest_reference:
        fail("invalid limitation_references: unexpected evidence reference")
    if not re.fullmatch(r"lim-[a-z0-9._-]+(?:,lim-[a-z0-9._-]+)*", limitations["ids"]):
        fail("invalid limitation_references: ids must be explicit lim-* identifiers")
    limitation_ids = limitations["ids"].split(",")
    if len(set(limitation_ids)) != len(limitation_ids):
        fail("invalid limitation_references: ids must not contain duplicates")
    if not re.fullmatch(r"[a-z0-9][a-z0-9._@-]{2,80}", limitations["owner"], re.IGNORECASE):
        fail("invalid limitation_references: owner must be accountable")
    if re.search(
        r"\b(?:artifact|verifier|issue-lint|bot|automation)\b",
        limitations["owner"],
        re.IGNORECASE,
    ):
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
    if follow_up_at > decision_at + max_follow_up_horizon:
        fail(
            "invalid limitation_references: follow_up_at must be no more than "
            "90 days after decision_at"
        )

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

        negative_manifest_path = evidence_worktree / negative_manifest_reference
        if not negative_manifest_path.is_file() or negative_manifest_path.stat().st_size == 0:
            fail("negative evidence reference does not resolve at repository_revision")
        resolved_negative_evidence_id = (
            "sha256:" + hashlib.sha256(negative_manifest_path.read_bytes()).hexdigest()
        )
        for field, parts in negative_evidence_parts.items():
            if parts["evidence_id"].lower() != resolved_negative_evidence_id:
                fail(f"invalid {field}: evidence_id does not match resolved evidence reference")
        try:
            negative_manifest = json.loads(negative_manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            fail("negative evidence reference must contain valid UTF-8 JSON")
        if not isinstance(negative_manifest, dict) or set(negative_manifest) != {
            "schema_version",
            "records",
        }:
            fail("negative evidence manifest must contain only schema_version and records")
        if negative_manifest["schema_version"] != "phase-66-7-negative-evidence/v1":
            fail("negative evidence manifest has unsupported schema_version")
        records = negative_manifest["records"]
        if not isinstance(records, list):
            fail("negative evidence manifest records must be an array")
        records_by_field: dict[str, dict[str, str]] = {}
        record_keys = {
            "field",
            "surface",
            "attempt",
            "result",
            "authoritative_record",
            "observed_at",
            "journey_run_id",
        }
        for record in records:
            if not isinstance(record, dict) or set(record) != record_keys:
                fail("negative evidence manifest record has invalid fields")
            field = record["field"]
            if not isinstance(field, str) or field in records_by_field:
                fail("negative evidence manifest contains invalid or duplicate field")
            if not all(isinstance(value, str) for value in record.values()):
                fail(f"negative evidence manifest record {field} must contain string values")
            records_by_field[field] = record
        if set(records_by_field) != set(negative_expectations):
            fail("negative evidence manifest must contain exactly one record for every required surface")
        for field, parts in negative_evidence_parts.items():
            expected_record = {
                "field": field,
                "surface": parts["surface"],
                "attempt": parts["attempt"],
                "result": parts["result"],
                "authoritative_record": parts["authoritative_record"],
                "observed_at": parts["observed_at"],
                "journey_run_id": parts["journey_run_id"],
            }
            if records_by_field[field] != expected_record:
                fail(f"invalid {field}: resolved negative evidence record does not match packet")

        limitation_manifest_path = evidence_worktree / limitation_manifest_reference
        if not limitation_manifest_path.is_file() or limitation_manifest_path.stat().st_size == 0:
            fail("limitation evidence reference does not resolve at repository_revision")
        resolved_limitation_evidence_id = (
            "sha256:" + hashlib.sha256(limitation_manifest_path.read_bytes()).hexdigest()
        )
        if limitations["evidence_id"].lower() != resolved_limitation_evidence_id:
            fail("invalid limitation_references: evidence_id does not match resolved evidence reference")
        try:
            limitation_manifest = json.loads(limitation_manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            fail("limitation evidence reference must contain valid UTF-8 JSON")
        if not isinstance(limitation_manifest, dict) or set(limitation_manifest) != {
            "schema_version",
            "limitations",
        }:
            fail("limitation manifest must contain only schema_version and limitations")
        if limitation_manifest["schema_version"] != "phase-66-7-limitations/v1":
            fail("limitation manifest has unsupported schema_version")
        limitation_records = limitation_manifest["limitations"]
        if not isinstance(limitation_records, list):
            fail("limitation manifest limitations must be an array")
        limitations_by_id: dict[str, dict[str, str]] = {}
        limitation_record_keys = {
            "id",
            "owner",
            "disposition",
            "decision_at",
            "follow_up_at",
        }
        for record in limitation_records:
            if not isinstance(record, dict) or set(record) != limitation_record_keys:
                fail("limitation manifest record has invalid fields")
            if not all(isinstance(value, str) for value in record.values()):
                fail("limitation manifest records must contain string values")
            limitation_id = record["id"]
            if (
                not re.fullmatch(r"lim-[a-z0-9._-]+", limitation_id)
                or limitation_id in limitations_by_id
            ):
                fail("limitation manifest contains invalid or duplicate id")
            if record["disposition"].lower() != "accepted":
                fail(f"limitation manifest record {limitation_id} must be accepted")
            record_decision_at = parse_timestamp(
                f"limitation manifest record {limitation_id}",
                record["decision_at"],
            )
            record_follow_up_at = parse_timestamp(
                f"limitation manifest record {limitation_id}",
                record["follow_up_at"],
                fresh=False,
                allow_future=True,
            )
            if record_follow_up_at <= record_decision_at:
                fail(
                    f"limitation manifest record {limitation_id} follow_up_at "
                    "must be after decision_at"
                )
            if record_follow_up_at > record_decision_at + max_follow_up_horizon:
                fail(
                    f"limitation manifest record {limitation_id} follow_up_at "
                    "must be no more than 90 days after decision_at"
                )
            limitations_by_id[limitation_id] = record
        for limitation_id in limitation_ids:
            record = limitations_by_id.get(limitation_id)
            if record is None:
                fail(
                    f"invalid limitation_references: limitation {limitation_id} "
                    "does not resolve at repository_revision"
                )
            expected_record = {
                "id": limitation_id,
                "owner": limitations["owner"],
                "disposition": "accepted",
                "decision_at": limitations["decision_at"],
                "follow_up_at": limitations["follow_up_at"],
            }
            if record != expected_record:
                fail(
                    f"invalid limitation_references: resolved limitation record "
                    f"{limitation_id} does not match packet"
                )
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

    owner_review = require_components(
        "owner_review",
        ("artifact_owner", "reviewer", "reviewed_at", "disposition", "follow_up_owner"),
    )
    for identity_field in ("artifact_owner", "reviewer", "follow_up_owner"):
        identity = owner_review[identity_field]
        if not re.fullmatch(r"[a-z0-9][a-z0-9._@-]{2,80}", identity, re.IGNORECASE):
            fail(f"invalid owner_review: malformed {identity_field}")
        if re.search(r"\b(?:artifact|verifier|issue-lint|bot|automation)\b", identity, re.IGNORECASE):
            fail(f"invalid owner_review: {identity_field} must be accountable")
    if owner_review["artifact_owner"].casefold() == owner_review["reviewer"].casefold():
        fail("invalid owner_review: artifact_owner and reviewer must be distinct")
    if owner_review["disposition"].lower() != "accepted":
        fail("invalid owner_review: disposition must be accepted")
    parse_timestamp("owner_review", owner_review["reviewed_at"])

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

redaction_marker = re.compile(r"(?:redacted|absent|rejected|forbidden|removed)", re.IGNORECASE)
sensitive_assignment = re.compile(
    r"(?:^|[;,\s{|])`?(?:password|passwd|secret(?:[ _-]*key)?|client[ _-]*secret|"
    r"x[ _-]*api[ _-]*key|api[ _-]*key|access[ _-]*token|refresh[ _-]*token|"
    r"private[ _-]*key|"
    r"authorization)`?\s*[:=]\s*(?P<value>[^;,|}\r\n]+)",
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
def assignment_contains_forbidden_value(pattern: re.Pattern, line: str) -> bool:
    for match in pattern.finditer(line):
        value = match.group("value").strip()
        if len(value) >= 2 and (value[0], value[-1]) in {
            ("`", "`"),
            ('"', '"'),
            ("'", "'"),
        }:
            value = value[1:-1].strip()
        if not redaction_marker.fullmatch(value):
            return True
    return False


secret_hygiene_inputs = (rendered_doc_raw, rendered_source_doc_raw)
if any(
    any(
        assignment_contains_forbidden_value(sensitive_assignment, line)
        for line in hygiene_input.splitlines()
    )
    or any(pattern.search(hygiene_input) for pattern in secret_patterns)
    for hygiene_input in secret_hygiene_inputs
):
    fail("production secret-looking value detected")

wsl_windows_home_segment = "Users"
workstation_patterns = (
    re.compile(r"(?:^|[\s`\"'(<:=])/(?:Users|home)/[^\s`\"'()<>/]+/", re.IGNORECASE),
    re.compile(r"(?:^|[\s`\"'(<:=])/(?:root)(?:/|$)", re.IGNORECASE),
    re.compile(
        r"(?:^|[\s`\"'(<:=])/mnt/[a-z]/"
        + wsl_windows_home_segment
        + r"/[^\s`\"'()<>/]+/",
        re.IGNORECASE,
    ),
    re.compile(
        r"file:(?://(?:localhost)?/|/+)mnt/[a-z]/"
        + wsl_windows_home_segment
        + r"/[^\s`\"'()<>/]+/",
        re.IGNORECASE,
    ),
    re.compile(r"(?:^|[\s`\"'(<:=])~/(?:[^\s`\"'()<>]+)", re.IGNORECASE),
    re.compile(r"(?:^|[\s`\"'(<:=])[A-Za-z]:[\\/]Users[\\/][^\s`\"'()<>\\/]+[\\/]", re.IGNORECASE),
    re.compile(r"file://(?:[^\s`\"'()<>]*/)?(?:(?:Users|home)/[^\s`\"'()<>/]+|root)/", re.IGNORECASE),
)
if any(
    pattern.search(hygiene_input)
    for hygiene_input in secret_hygiene_inputs
    for pattern in workstation_patterns
):
    fail("workstation-local path detected")

email_pattern = re.compile(
    r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?![A-Za-z0-9.-])"
)
private_assignment = re.compile(
    r"(?:^|[;,\s{|])`?(?:customer[_ -]?(?:name|identifier|private_data|private_payload)|tenant[_ -]?(?:name|identifier)|ticket[_ -]?private[_ -]?content|raw[_ -]?(?:customer|ticket)[_ -]?(?:data|payload|content))`?\s*[:=]\s*(?P<value>[^;,|}\r\n]+)",
    re.IGNORECASE,
)
private_data_object = (
    r"(?:(?:unredacted|raw|private)\s+(?:customer|ticket)\s+"
    r"(?:data|payload|content|information|records?)|"
    r"(?:customer|ticket)(?:[- ]private)?\s+"
    r"(?:data|payload|content|information|records?|identifiers?)|"
    r"raw\s+payload|customer\s+identifier)"
)
private_data_claim = re.compile(
    r"\b(?:includes?|contains?|retains?|stores?|embeds?|exports?|captures?|publishes?)\b"
    rf".{{0,60}}?\b(?P<object>{private_data_object})",
    re.IGNORECASE,
)
private_data_passive_claim = re.compile(
    rf"\b(?P<object>{private_data_object})\b.{{0,40}}?\b"
    r"(?:is|are|was|were|has\s+been|have\s+been)\s+"
    r"(?P<negated>not\s+)?"
    r"(?:included|contained|retained|stored|embedded|exported|captured|published)\b",
    re.IGNORECASE,
)
private_claim_safe_qualifier = re.compile(
    r"\b(?:absent|no|redacted|removed)\s*$",
    re.IGNORECASE,
)
if any(
    email_pattern.search(hygiene_input)
    or any(
        assignment_contains_forbidden_value(private_assignment, line)
        for line in hygiene_input.splitlines()
    )
    for hygiene_input in secret_hygiene_inputs
):
    fail("customer-private or ticket-private data detected")
private_denial_boundary = (
    r"(?:[.!?,;]|\b(?:and|or|but|however|yet|although|though|while|whereas|"
    r"because|since|then|before|after)\b)"
)
private_claim_denial = re.compile(
    rf"\b(?:cannot|can't|does\s+not|do\s+not|did\s+not|will\s+not|would\s+not|"
    rf"should\s+not|may\s+not|must\s+not|never)\b"
    rf"(?:(?!{private_denial_boundary}).){{0,60}}$",
    re.IGNORECASE,
)
for line in rendered_doc_raw.splitlines():
    for match in private_data_claim.finditer(line):
        claim_prefix = line[match.start() : match.start("object")]
        if private_claim_safe_qualifier.search(claim_prefix):
            continue
        if not private_claim_denial.search(line[: match.start()]):
            fail("customer-private or ticket-private data detected")
    for match in private_data_passive_claim.finditer(line):
        qualifier_prefix = line[max(0, match.start("object") - 30) : match.start("object")]
        if private_claim_safe_qualifier.search(qualifier_prefix) or match.group("negated"):
            continue
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
    r"general\s+availability|production(?:\s+(?:readiness|rollout|operations)|[- ](?:ready|grade|capable))|"
    r"(?:ready|fit|suitable)\s+for\s+production|"
    r"ready\s+to\s+(?:deploy|operate|run|ship)\s+(?:in|to)\s+production|"
    r"commercial\s+replacement|"
    r"broad\s+(?:enterprise\s+)?(?:siem|soar)(?:\s+parity)?)"
)
authority_action = (
    r"(?:approv(?:e|es|ed|ing)|execut(?:e|es|ed|ing)|reconcil(?:e|es|ed|ing)|"
    r"clos(?:e|es|ed|ing)\s+(?:(?:a|an|the|one|any|this|that|each|every)\s+)?"
    r"(?:(?:single|individual|specific|given|open|selected|current)\s+)?cases?|"
    r"admit(?:s|ted|ting)?|"
    r"releas(?:e|es|ed|ing)|gat(?:e|es|ed|ing)|overrid(?:e|es|den|ing))"
)
direct_authority_action = (
    r"(?:approv(?:es|ed|ing)|execut(?:es|ed|ing)|reconcil(?:es|ed|ing)|"
    r"clos(?:es|ed|ing)\s+(?:(?:a|an|the|one|any|this|that|each|every)\s+)?"
    r"(?:(?:single|individual|specific|given|open|selected|current)\s+)?cases?|"
    r"admit(?:s|ted|ting)|"
    r"releas(?:es|ed|ing)|gat(?:es|ed|ing)|overrid(?:es|den|ing))"
)
authority_possession_verb = (
    r"(?:has|have|had|holds?|held|receives?|received|possesses?|possessed|"
    r"retains?|retained|retaining|keeps?|kept|maintains?|maintained|"
    r"obtains?|obtained|acquires?|acquired|"
    r"is\s+granted|are\s+granted|was\s+granted|were\s+granted|"
    r"is\s+given|are\s+given|was\s+given|were\s+given)"
)
claim_patterns = (
    re.compile(
        rf"\b{subordinate_subject}\b.{{0,120}}\b(?:is|are|becomes?|serves?\s+as|acts?\s+as|owns?|defines?|determines?)\b.{{0,80}}\b{truth_outcome}\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b{subordinate_subject}\b.{{0,100}}\b"
        rf"(?:can|could|may|might|will|would|must|should|shall|does|do|"
        rf"has\s+to|have\s+to|needs?\s+to|ought\s+to|"
        rf"automatically|independently|directly)\b.{{0,60}}\b{authority_action}\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b{subordinate_subject}\b\s+(?:(?:automatically|independently|directly)\s+)?{direct_authority_action}\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b{subordinate_subject}\b.{{0,80}}\b"
        rf"(?:is|are|was|were|has\s+been|have\s+been|becomes?|remains?|can(?:not)?\s+be|"
        rf"could(?:\s+not)?\s+be|may(?:\s+not)?\s+be|might(?:\s+not)?\s+be|"
        rf"will(?:\s+not)?\s+be|would(?:\s+not)?\s+be|must(?:\s+not)?\s+be|"
        rf"should(?:\s+not)?\s+be)\s+"
        rf"(?:(?:not|never|fully|explicitly|independently|directly)\s+)*"
        rf"(?:permitted|allowed|authorized|empowered|entitled|required|obligated|mandated)\s+"
        rf"(?:by\s+[a-z0-9._@/-]+\s+)?to\s+"
        rf"(?:(?:automatically|independently|directly)\s+)?{authority_action}\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b{subordinate_subject}\b.{{0,80}}\b"
        rf"{authority_possession_verb}\s+"
        rf"(?:(?:the|full|explicit|independent|direct|delegated)\s+)*"
        rf"(?:permission|authorization|authority|power|right)\s+to\s+"
        rf"(?:(?:automatically|independently|directly)\s+)?{authority_action}\b",
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
denial_scope_boundary = (
    rf"(?:[,;]|\b(?:and|or|but|however|yet|although|though|while|whereas|because|since)\b)\s*"
    rf"(?:(?:{subordinate_subject}|it|they|this)\b\s*)?"
    r"(?:can|could|may|might|will|would|must|should|shall|does|do|"
    r"has\s+to|have\s+to|needs?\s+to|ought\s+to|"
    rf"is|are|{authority_possession_verb}|"
    r"automatically|independently|directly|"
    r"becomes?|serves?|acts?|"
    r"owns?|defines?|determines?|proves?|confirms?|establishes?|satisfies?|passes?|"
    r"grants?|achieves?|certifies?|validates?|delivers?|enables?|provides?)\b"
)
denied_claim_target = (
    rf"(?:{authority_action}|{truth_outcome}|{readiness_outcome}|"
    r"proven|confirmed|established|satisfied|passed|achieved|validated|"
    r"owned|defined|provided|determined|controlled|allowed|accepted|supported|valid)"
)
scoped_denial_pattern = re.compile(
    rf"\b(?:cannot|can't|does\s+not|do\s+not|did\s+not|will\s+not|would\s+not|should\s+not|"
    rf"may\s+not|must\s+not|shall\s+not|not|never|no\s+longer|"
    rf"reject(?:s|ed|ing)?|forbid(?:s|den|ding)?|"
    rf"exclud(?:e|es|ed|ing)|without|remains?\s+subordinate|evidence\s+only)\b"
    rf"(?:(?!{denial_scope_boundary}).){{0,120}}\b{denied_claim_target}\b",
    re.IGNORECASE,
)


def claim_clauses(text: str):
    normalized = re.sub(r"[`*_#|]", " ", text)
    normalized = re.sub(r"\s+", " ", normalized)
    inherited_subject = ""
    parts = re.split(
        r"\s*((?<!\d)[.!?](?!\d)|;|\bbut\b|\bhowever\b|\byet\b|\balthough\b|\bthough\b)\s*",
        normalized,
        flags=re.IGNORECASE,
    )
    elision_boundaries = {";", "but", "however", "yet", "although", "though"}
    verb_led_continuation = re.compile(
        rf"^(?:can|could|may|might|will|would|must|should|shall|does|do|cannot|can't|"
        rf"does\s+not|do\s+not|did\s+not|will\s+not|would\s+not|should\s+not|"
        rf"may\s+not|must\s+not|shall\s+not|has\s+to|have\s+to|needs?\s+to|ought\s+to|"
        rf"automatically|independently|directly|"
        rf"is|are|{authority_possession_verb}|becomes?|serves?|acts?|owns?|defines?|determines?|"
        rf"proves?|confirms?|establishes?|satisfies?|passes?|grants?|achieves?|"
        rf"certifies?|validates?|delivers?|enables?|provides?|"
        rf"{direct_authority_action})\b",
        re.IGNORECASE,
    )
    for index in range(0, len(parts), 2):
        clause = parts[index]
        boundary = parts[index - 1].lower() if index else ""
        clause = clause.strip()
        if not clause:
            continue
        subject_match = re.search(subordinate_subject, clause, re.IGNORECASE)
        if subject_match:
            inherited_subject = subject_match.group(0)
        elif inherited_subject and re.match(r"^(?:it|they|this)\b", clause, re.IGNORECASE):
            clause = re.sub(r"^(?:it|they|this)\b", inherited_subject, clause, flags=re.IGNORECASE)
        elif (
            inherited_subject
            and boundary in elision_boundaries
            and verb_led_continuation.match(clause)
        ):
            clause = f"{inherited_subject} {clause}"
        yield clause


claim_scan_doc = rendered_doc_raw.replace(
    "Phase 66.7 does not add runtime feature breadth, execute production operations, grant new AI or integration authority, prove real design-partner outcomes, complete production rollout, implement commercial billing or entitlement enforcement, prove Phase 67 GA readiness, or claim broad enterprise SIEM/SOAR parity.",
    "",
)
claim_inputs = (
    claim_scan_doc,
    "\n".join(
        line
        for line in rendered_readme_raw.splitlines()
        if re.search(r"phase\s+66\.7|authority-boundary\s+proof\s+pack", line, re.IGNORECASE)
    ),
)
for claim_input in claim_inputs:
    for clause in claim_clauses(claim_input):
        for pattern in claim_patterns:
            match = pattern.search(clause)
            if match and not scoped_denial_pattern.search(match.group(0)):
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
