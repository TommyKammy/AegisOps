#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
repo_root="$(cd "${repo_root}" && pwd -P)"

doc_path="docs/phase-66-closeout-evaluation.md"
absolute_doc_path="${repo_root}/${doc_path}"
readme_path="${repo_root}/README.md"

required_reference_paths=(
  "docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
  "docs/phase-51-6-authority-boundary-negative-test-policy.md"
  "docs/phase-65-closeout-evaluation.md"
  "docs/phase-66-1-clean-host-rc-e2e-harness.md"
  "docs/phase-66-2-wazuh-sample-signal-rc-proof.md"
  "docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
  "docs/phase-66-4-ai-assisted-triage-rc-proof.md"
  "docs/phase-66-5-report-export-rc-proof.md"
  "docs/phase-66-6-rc-supportability-proof.md"
  "docs/phase-66-7-rc-authority-boundary-proof-pack.md"
)

required_verifier_scripts=(
  "scripts/verify-phase-66-1-clean-host-rc-e2e-harness.sh"
  "scripts/test-verify-phase-66-1-clean-host-rc-e2e-harness.sh"
  "scripts/verify-phase-66-2-wazuh-sample-signal-rc-proof.sh"
  "scripts/test-verify-phase-66-2-wazuh-sample-signal-rc-proof.sh"
  "scripts/verify-phase-66-3-shuffle-sample-execution-rc-proof.sh"
  "scripts/test-verify-phase-66-3-shuffle-sample-execution-rc-proof.sh"
  "scripts/verify-phase-66-4-ai-assisted-triage-rc-proof.sh"
  "scripts/test-verify-phase-66-4-ai-assisted-triage-rc-proof.sh"
  "scripts/verify-phase-66-5-report-export-rc-proof.sh"
  "scripts/test-verify-phase-66-5-report-export-rc-proof.sh"
  "scripts/verify-phase-66-6-rc-supportability-proof.sh"
  "scripts/test-verify-phase-66-6-rc-supportability-proof.sh"
  "scripts/verify-phase-66-7-rc-authority-boundary-proof-pack.sh"
  "scripts/test-verify-phase-66-7-rc-authority-boundary-proof-pack.sh"
  "scripts/verify-phase-66-8-rc-closeout-evaluation.sh"
  "scripts/test-verify-phase-66-8-rc-closeout-evaluation.sh"
  "scripts/verify-phase-51-3-pilot-beta-rc-ga-gate-contract.sh"
  "scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh"
  "scripts/verify-maintainability-hotspots.sh"
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

require_file "${absolute_doc_path}" "Phase 66 RC closeout evaluation"
require_file "${readme_path}" "README for Phase 66 closeout link check"

for reference_path in "${required_reference_paths[@]}"; do
  require_file "${repo_root}/${reference_path}" "Phase 66 closeout reference ${reference_path}"
done

for verifier_script in "${required_verifier_scripts[@]}"; do
  require_file "${repo_root}/${verifier_script}" "Phase 66 verifier script ${verifier_script}"
done

python3 - "${absolute_doc_path}" "${readme_path}" <<'PY'
from __future__ import annotations

import html
import re
import sys
from pathlib import Path


doc_path = Path(sys.argv[1])
readme_path = Path(sys.argv[2])
doc_raw = doc_path.read_text(encoding="utf-8")
readme_raw = readme_path.read_text(encoding="utf-8")


def visible_markdown(value: str) -> str:
    return re.sub(r"<!--.*?-->", "", value, flags=re.DOTALL)


def without_fenced_blocks(value: str) -> str:
    visible_lines: list[str] = []
    fence: str | None = None
    for line in value.splitlines():
        marker = re.match(r"^\s*(```+|~~~+)", line)
        if marker:
            current = marker.group(1)[0]
            if fence is None:
                fence = current
            elif fence == current:
                fence = None
            continue
        if fence is None:
            visible_lines.append(line)
    return "\n".join(visible_lines)


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


doc_visible = visible_markdown(doc_raw)
readme_visible = visible_markdown(readme_raw)
doc = without_fenced_blocks(doc_visible)
readme = without_fenced_blocks(readme_visible)

readme_phrases = (
    "- [Phase 66.8 RC closeout evaluation](docs/phase-66-closeout-evaluation.md) records the bounded Phase 66 RC verdict, child outcomes, focused verifier and issue-lint evidence, accepted limitations, subordinate authority posture, and Phase 67 handoff without GA, production rollout, self-service commercial, or broad SIEM/SOAR parity claims.",
    "The Phase 66.8 RC closeout evaluation is defined by the [Phase 66.8 RC closeout evaluation](docs/phase-66-closeout-evaluation.md).",
)
for phrase in readme_phrases:
    if phrase not in readme:
        fail(f"Missing README Phase 66.8 closeout reference: {phrase}")

required_phrases = (
    "# Phase 66 RC Closeout Evaluation",
    "**Status**: Accepted at the bounded Phase 66 release-candidate evidence boundary; Phase 67 prerequisite validation, GA acceptance, production rollout, self-service commercial readiness, and broad SIEM/SOAR parity remain unproven.",
    "**Related Issues**: #1397, #1398, #1399, #1400, #1401, #1402, #1403, #1404, #1405",
    "Phase 66 RC Replacement Readiness is accepted for the repository-owned, bounded release-candidate evidence chain",
    "The accepted verdict is an RC evidence verdict only.",
    "AegisOps records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, and closeout truth.",
    "Phase 66 closeout text, release artifacts, Wazuh signals, Shuffle receipts, AI traces, reports, support bundles, tickets, optional evidence, UI cache, demo data, verifier output, and issue-lint output remain subordinate evidence only.",
    "Phase 66 must reject missing child outcomes, missing verifier or test evidence, missing issue-lint evidence, missing accepted limitations, missing Phase 67 handoff, workstation-local paths, production secrets, customer-private data, inferred GA acceptance, production rollout claims, self-service commercial readiness claims, broad SIEM/SOAR parity claims, verifier-as-truth, and issue-lint-as-truth.",
    "Focused Phase 66 and inherited checks that must pass:",
    "Recorded result on 2026-07-24: every listed Phase 66 verifier and self-test, both inherited Phase 51 boundary verifiers, the maintainability baseline check, and publishable path hygiene passed.",
    "Recorded result on 2026-07-24: issues #1397 through #1405 each reported `execution_ready=yes`, `missing_required=none`, `missing_recommended=none`, `metadata_errors=none`, and `high_risk_blocking_ambiguity=none`.",
    "Each command should report `execution_ready=yes`, `missing_required=none`, `missing_recommended=none`, `metadata_errors=none`, and `high_risk_blocking_ambiguity=none` before Phase 66 is considered fully closed.",
    "Issue-lint output is planning and metadata evidence only. It does not become workflow, release, gate, limitation, closeout, or readiness truth.",
)
for phrase in required_phrases:
    if phrase not in doc:
        fail(f"Missing required Phase 66 closeout term: {phrase}")

required_headings = (
    "## Verdict",
    "## Child Issue Outcomes",
    "## Changed RC Proof Surfaces",
    "## Verifier and Test Evidence",
    "## Issue-Lint Summary",
    "## Accepted Limitations",
    "## Phase 67 Handoff",
    "## Explicit Non-Claims",
)
lines = doc.splitlines()
heading_positions: dict[str, int] = {}
for heading in required_headings:
    matches = [index for index, line in enumerate(lines) if line.strip() == heading]
    if len(matches) != 1:
        fail(f"Expected exactly one Phase 66 closeout section: {heading}")
    heading_positions[heading] = matches[0]
if [heading_positions[heading] for heading in required_headings] != sorted(
    heading_positions.values()
):
    fail("Phase 66 closeout sections are out of order")


def section_text(heading: str, next_heading: str | None) -> str:
    start = heading_positions[heading] + 1
    end = heading_positions[next_heading] if next_heading else len(lines)
    return "\n".join(lines[start:end])


def require_exact_line(section: str, expected: str, description: str) -> None:
    matches = sum(line.strip() == expected for line in section.splitlines())
    if matches != 1:
        fail(f"Expected exactly one {description}: {expected}")


child_outcomes = section_text("## Child Issue Outcomes", "## Changed RC Proof Surfaces")
required_child_rows = (
    "| #1397 | Epic: Phase 66 RC Replacement Readiness | Open until #1405 lands; accepted at the bounded RC evidence boundary when this closeout, focused Phase 66 checks, inherited boundary checks, maintainability, path hygiene, and issue-lint pass. |",
    "| #1398 | Phase 66.1 clean-host RC E2E harness | Closed. `docs/phase-66-1-clean-host-rc-e2e-harness.md` and its focused verifier and self-test define the clean-host journey from setup through report export without GA, production rollout, self-service commercial, or broad SIEM/SOAR parity claims. |",
    "| #1399 | Phase 66.2 Wazuh sample signal RC proof | Closed. `docs/phase-66-2-wazuh-sample-signal-rc-proof.md` and its focused verifier and self-test record reviewed Wazuh-origin signal evidence while preserving Wazuh as subordinate analytic context. |",
    "| #1400 | Phase 66.3 Shuffle sample execution RC proof | Closed. `docs/phase-66-3-shuffle-sample-execution-rc-proof.md` and its focused verifier and self-test record reviewed Shuffle execution evidence while preserving AegisOps delegation and reconciliation authority. |",
    "| #1401 | Phase 66.4 AI-assisted triage RC proof | Closed. `docs/phase-66-4-ai-assisted-triage-rc-proof.md` and its focused verifier and self-test record cited, reviewable AI triage evidence without granting AI approval, execution, reconciliation, or case-closure authority. |",
    "| #1402 | Phase 66.5 report export RC proof | Closed. `docs/phase-66-5-report-export-rc-proof.md` and its focused verifier and self-test record reviewed export evidence while preserving AegisOps records as workflow authority. |",
    "| #1403 | Phase 66.6 RC supportability proof | Closed. `docs/phase-66-6-rc-supportability-proof.md` and its focused verifier and self-test record backup, restore dry-run, upgrade, rollback, support-bundle, redaction, owner-review, and limitation evidence without production-support or GA claims. |",
    "| #1404 | Phase 66.7 RC authority-boundary proof pack | Closed. `docs/phase-66-7-rc-authority-boundary-proof-pack.md` and its focused verifier and self-test collect negative observations across the Phase 66 journey without treating subordinate evidence as authority or accepting an RC or GA gate. |",
    "| #1405 | Phase 66.8 RC closeout evaluation | Open until this document, its focused verifier and self-test, inherited checks, and issue-lint evidence land. |",
)
for row in required_child_rows:
    require_exact_line(child_outcomes, row, "Phase 66 child issue outcome row")

changed_surfaces = section_text(
    "## Changed RC Proof Surfaces", "## Verifier and Test Evidence"
)
required_changed_surfaces = (
    "- `docs/phase-66-1-clean-host-rc-e2e-harness.md`",
    "- `docs/phase-66-2-wazuh-sample-signal-rc-proof.md`",
    "- `docs/phase-66-3-shuffle-sample-execution-rc-proof.md`",
    "- `docs/phase-66-4-ai-assisted-triage-rc-proof.md`",
    "- `docs/phase-66-5-report-export-rc-proof.md`",
    "- `docs/phase-66-6-rc-supportability-proof.md`",
    "- `docs/phase-66-7-rc-authority-boundary-proof-pack.md`",
    "- `docs/phase-66-closeout-evaluation.md`",
    "- `scripts/verify-phase-66-8-rc-closeout-evaluation.sh`",
    "- `scripts/test-verify-phase-66-8-rc-closeout-evaluation.sh`",
    "- `README.md`",
)
for line in required_changed_surfaces:
    require_exact_line(changed_surfaces, line, "Phase 66 changed proof surface")

verifier_evidence = section_text(
    "## Verifier and Test Evidence", "## Issue-Lint Summary"
)
required_verifier_lines = (
    "- `bash scripts/verify-phase-66-1-clean-host-rc-e2e-harness.sh`",
    "- `bash scripts/test-verify-phase-66-1-clean-host-rc-e2e-harness.sh`",
    "- `bash scripts/verify-phase-66-2-wazuh-sample-signal-rc-proof.sh`",
    "- `bash scripts/test-verify-phase-66-2-wazuh-sample-signal-rc-proof.sh`",
    "- `bash scripts/verify-phase-66-3-shuffle-sample-execution-rc-proof.sh`",
    "- `bash scripts/test-verify-phase-66-3-shuffle-sample-execution-rc-proof.sh`",
    "- `bash scripts/verify-phase-66-4-ai-assisted-triage-rc-proof.sh`",
    "- `bash scripts/test-verify-phase-66-4-ai-assisted-triage-rc-proof.sh`",
    "- `bash scripts/verify-phase-66-5-report-export-rc-proof.sh`",
    "- `bash scripts/test-verify-phase-66-5-report-export-rc-proof.sh`",
    "- `bash scripts/verify-phase-66-6-rc-supportability-proof.sh`",
    "- `bash scripts/test-verify-phase-66-6-rc-supportability-proof.sh`",
    "- `bash scripts/verify-phase-66-7-rc-authority-boundary-proof-pack.sh`",
    "- `bash scripts/test-verify-phase-66-7-rc-authority-boundary-proof-pack.sh`",
    "- `bash scripts/verify-phase-66-8-rc-closeout-evaluation.sh`",
    "- `bash scripts/test-verify-phase-66-8-rc-closeout-evaluation.sh`",
    "- `bash scripts/verify-phase-51-3-pilot-beta-rc-ga-gate-contract.sh`",
    "- `bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh`",
    "- `bash scripts/verify-maintainability-hotspots.sh`",
    "- `bash scripts/verify-publishable-path-hygiene.sh`",
)
for line in required_verifier_lines:
    require_exact_line(verifier_evidence, line, "Phase 66 verifier evidence line")

issue_lint = section_text("## Issue-Lint Summary", "## Accepted Limitations")
for issue_number in range(1397, 1406):
    line = (
        f"- `node <codex-supervisor-root>/dist/index.js issue-lint {issue_number} "
        "--config <supervisor-config-path>`"
    )
    require_exact_line(issue_lint, line, "Phase 66 issue-lint evidence line")

accepted_limitations = section_text("## Accepted Limitations", "## Phase 67 Handoff")
required_limitations = (
    "Phase 66 does not collect real beta or design-partner evidence, prove real design-partner success, use Phase 67 to accept or materialize GA, collect production launch evidence, approve production rollout, or establish self-service commercial readiness.",
    "Phase 66 does not provide broad enterprise SIEM/SOAR parity, commercial billing, entitlement enforcement, a customer portal, HA/SLA proof, MSSP operations, compliance certification, production support operations, or new runtime feature breadth.",
    "Phase 66 does not promote Wazuh signals, Shuffle receipts, AI output, reports, support bundles, tickets, optional evidence, UI cache, demo data, release artifacts, verifier output, issue-lint output, or closeout wording into AegisOps workflow, release, gate, limitation, closeout, RC, GA, or commercial replacement truth.",
)
for phrase in required_limitations:
    if phrase not in accepted_limitations:
        fail(f"Missing Phase 66 accepted limitation: {phrase}")

phase67_handoff = section_text("## Phase 67 Handoff", "## Explicit Non-Claims")
required_handoff = (
    "Phase 67 may consume Phase 66 as subordinate GA-prerequisite planning input for the clean-host journey, Wazuh signal evidence, Shuffle execution evidence, AI triage evidence, report export evidence, supportability evidence, authority-boundary observations, verifier coverage, issue-lint coverage, and accepted limitations.",
    "Phase 67 must collect bounded GA-prerequisite evidence independently under `docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md`, using repo-owned evidence and explicit maintainer review; it cannot accept or materialize GA. Any later GA acceptance requires a separately scoped gate bound to current-revision evidence and independent human approval.",
    "Phase 67 must not infer GA gate acceptance from Phase 66 issue closure, proof-file presence, owner assignment, timestamps, reports, receipts, traces, support bundles, negative observations, verifier success, issue-lint success, or this closeout verdict.",
)
for phrase in required_handoff:
    if phrase not in phase67_handoff:
        fail(f"Missing Phase 67 handoff boundary: {phrase}")

explicit_non_claims = section_text("## Explicit Non-Claims", None)
required_non_claims = (
    "This closeout does not claim Phase 67 prerequisite completion, GA readiness, a passed GA gate, real design-partner success, production rollout readiness, self-service commercial readiness, broad enterprise SIEM/SOAR parity, commercial replacement readiness beyond the bounded RC evidence verdict, autonomous remediation, production support readiness, customer portal readiness, HA/SLA readiness, MSSP readiness, or compliance certification.",
    "The Phase 66 verdict does not authorize release, deployment, case closure, action execution, reconciliation, limitation resolution, or gate acceptance. Those decisions remain in the authoritative AegisOps record chain and require the responsible human owner.",
)
for phrase in required_non_claims:
    if phrase not in explicit_non_claims:
        fail(f"Missing Phase 66 explicit non-claim: {phrase}")

phase67_ga_overclaims = (
    re.compile(r"(?i)\bphase\s+67\s+is\s+GA\b"),
    re.compile(
        r"(?i)\bphase\s+67\s+(?:accepts?|materializes?)\s+"
        r"(?:the\s+)?GA(?:\s+gate)?\b"
    ),
)
for pattern in phase67_ga_overclaims:
    if pattern.search(doc_raw):
        fail(
            "Forbidden Phase 66 closeout evaluation: "
            "Phase 67 cannot accept or materialize GA"
        )


def rendered_text(value: str, *, remove_comments: bool = True) -> str:
    if remove_comments:
        value = visible_markdown(value)
    value = html.unescape(value)
    value = re.sub(r"\\([\\`*_{}\[\]()#+.!|<>=~-])", r"\1", value)
    value = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"<[^>\n]+>", " ", value)
    value = re.sub(r"[`*_~]", "", value)
    return value


security_source = re.sub(r"<!--(.*?)-->", r"\1", doc_raw, flags=re.DOTALL)
rendered = rendered_text(security_source, remove_comments=False)
normalized = re.sub(r"[ \t]+", " ", rendered)

secret_patterns = (
    re.compile(
        r"(?i)\bauthorization\s*(?::|=)?\s*bearer\s+([A-Za-z0-9._~+/=-]{12,})"
    ),
    re.compile(
        r"(?i)\b(?:api[\s_-]*key|access[\s_-]*token|refresh[\s_-]*token|"
        r"session[\s_-]*token|client[\s_-]*secret|password|passwd|secret|token)"
        r"\s*(?::|=|->|\bis\b|\bequals\b)\s*([^\s,;|]+)"
    ),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
)


def safe_secret_value(value: str) -> bool:
    candidate = value.strip("`'\".,()[]{}")
    lowered = candidate.lower()
    return (
        not candidate
        or candidate.startswith("<")
        or candidate.startswith("${")
        or candidate.startswith("$")
        or lowered in {"redacted", "masked", "placeholder", "example", "none", "unset"}
        or lowered.startswith(("redacted-", "example-", "placeholder-"))
    )


for pattern in secret_patterns:
    for match in pattern.finditer(normalized):
        if match.lastindex and safe_secret_value(match.group(1)):
            continue
        fail("Forbidden Phase 66 closeout evaluation: production secret-looking value detected")

paragraphs = [
    re.sub(r"\s+", " ", paragraph).strip()
    for paragraph in re.split(r"\n\s*\n", rendered)
    if paragraph.strip()
]
table_cells = [
    cell.strip()
    for line in rendered.splitlines()
    if "|" in line
    for cell in line.split("|")
    if cell.strip()
]
sentences = [
    sentence.strip()
    for sentence in re.split(r"(?<=[.!?])\s+|[;\n]+", rendered)
    if sentence.strip()
]
clauses: list[str] = []
subject_boundary = (
    r"(?:phase\s+66|aegisops|this\s+closeout|the\s+verdict|it\b|they\b|"
    r"verifier|issue-lint|wazuh|shuffle|ai\s+output|reports?|support\s+bundles?)"
)
for segment in paragraphs + table_cells + sentences:
    clauses.extend(
        clause.strip()
        for clause in re.split(
            rf"\b(?:but|however|although|yet|whereas)\b|"
            rf"\band\b(?=\s+{subject_boundary})|"
            rf",\s*(?={subject_boundary})|[.!?;]+",
            segment,
            flags=re.IGNORECASE,
        )
        if clause.strip()
    )

denial_pattern = re.compile(
    r"(?i)\b(?:does?\s+not|do\s+not|must\s+not|cannot|can['’]?t|"
    r"without(?:\s+\w+){0,3}|not\s+(?:claim|prove|establish|accept|approve|"
    r"authorize|grant|become|infer|promote|provide)|"
    r"reject(?:s|ed|ing)?|exclud(?:e|es|ed|ing)|"
    r"remain(?:s)?\s+(?:unproven|out\s+of\s+scope)|"
    r"(?:is|are)\s+not|no\s+(?:ga|production|commercial|self-service|broad))\b"
)

for segment in paragraphs + table_cells + sentences:
    lowered_segment = re.sub(r"\s+", " ", segment).lower()
    if not denial_pattern.search(lowered_segment):
        continue
    if re.search(
        r"(?i)(?:"
        r"\b(?:but|yet|and|however)\b\s*"
        r"(?:(?:phase\s+66|aegisops|this\s+closeout|the\s+verdict|it|they)\s+)?"
        r"|(?:,|;)\s*"
        r"(?:phase\s+66|aegisops|this\s+closeout|the\s+verdict|it|they)\s+"
        r")"
        r"(?:is|are|has\s+(?:achieved|established)|can|passes?|accepts?|approves?)"
        r"\b.{0,80}\b(?:ga|general\s+availability|production\s+rollout|"
        r"self-service\s+commercial|commercial\s+replacement|"
        r"broad(?:\s+enterprise)?\s+(?:siem|soar))\b",
        lowered_segment,
    ):
        fail(
            "Forbidden Phase 66 closeout evaluation contradictory readiness "
            f"claim: {segment.strip()}"
        )

for clause in clauses:
    lowered = re.sub(r"\s+", " ", clause).lower()
    if denial_pattern.search(lowered):
        contradiction = re.search(
            r"(?i)\b(?:but|yet|and)\s+(?:it\s+|they\s+)?"
            r"(?:is|are|has\s+(?:achieved|established)|can)\b.{0,80}"
            r"\b(?:ga|production\s+rollout|self-service\s+commercial|"
            r"commercial\s+replacement|broad(?:\s+enterprise)?\s+(?:siem|soar))\b",
            lowered,
        )
        if contradiction:
            fail(
                "Forbidden Phase 66 closeout evaluation contradictory readiness "
                f"claim: {clause.strip()}"
            )
        continue

    forbidden_claims = (
        (
            r"\b(?:phase\s+66|aegisops|this\s+closeout|the\s+verdict)\b"
            r".{0,100}\b(?:ga|general\s+availability)\b.{0,80}"
            r"\b(?:ready|readiness|accepted|passes?|passed|proves?|proven|"
            r"satisfies?|approved|complete)\b"
        ),
        (
            r"\b(?:phase\s+66|aegisops|this\s+closeout|the\s+verdict|it|they)\b"
            r".{0,80}\b(?:is|are|becomes?|has\s+(?:achieved|established)|"
            r"proves?|meets?|passes?|accepts?|approves?|qualifies?)\b.{0,80}"
            r"\b(?:ga(?:\s+(?:ready|readiness|gate))?|general\s+availability|"
            r"generally\s+available|ready\s+for\s+(?:ga|general\s+availability)|"
            r"ready\s+for\s+production\s+rollout|production\s+rollout\s+readiness|"
            r"self-service\s+commercial\s+readiness|commercial\s+replacement\s+readiness|"
            r"broad(?:\s+enterprise)?\s+(?:siem|soar|siem/soar)\s+parity)\b"
        ),
        (
            r"\b(?:ga|general\s+availability)\b.{0,80}"
            r"\b(?:gate|readiness)\b.{0,50}"
            r"\b(?:is|was|has\s+been)?\s*"
            r"(?:accepted|passed|approved|proven|complete|achieved|established)\b"
        ),
        (
            r"\b(?:ga\s+readiness|ga\s+gate|general\s+availability|"
            r"production\s+rollout(?:\s+readiness)?|"
            r"self-service\s+commercial\s+readiness|commercial\s+replacement\s+readiness|"
            r"broad(?:\s+enterprise)?\s+(?:siem|soar|siem/soar)\s+parity)\b"
            r".{0,50}\b(?:is|was|has\s+been)?\s*"
            r"(?:ready|accepted|passed|approved|proven|complete|achieved|established)\b"
        ),
        (
            r"\b(?:ready\s+for\s+(?:ga|general\s+availability|production\s+rollout)|"
            r"generally\s+available)\b"
        ),
        (
            r"\b(?:phase\s+66|aegisops|this\s+closeout|the\s+verdict)\b"
            r".{0,100}\bproduction\b.{0,60}"
            r"\b(?:rollout|deployment|support|launch)\b.{0,50}"
            r"\b(?:ready|readiness|accepted|approved|proven|complete)\b"
        ),
        (
            r"\b(?:self-service\s+commercial|commercial\s+replacement|"
            r"broad(?:\s+enterprise)?\s+(?:siem|soar|siem/soar))\b.{0,80}"
            r"\b(?:ready|readiness|parity|achieved|established|proven|complete)\b"
        ),
        (
            r"\b(?:verifier|issue-lint)(?:\s+output|\s+success)?\b.{0,60}"
            r"\b(?:is|becomes?|serves?\s+as|establishes?|proves?|passes?|accepts?)\b"
            r".{0,60}"
            r"\b(?:authoritative|truth|readiness|rc|ga|gate|release|closeout|"
            r"workflow|limitation)\b"
        ),
        (
            r"\b(?:wazuh(?:\s+signals?)?|shuffle(?:\s+receipts?)?|ai(?:\s+output|\s+traces?)?|"
            r"reports?|support\s+bundles?|tickets?|ui\s+cache|demo\s+data|"
            r"release\s+artifacts?)\b.{0,80}"
            r"\b(?:is|are|becomes?|serve(?:s)?\s+as)\b.{0,60}"
            r"\b(?:authoritative|truth|approval|execution|reconciliation|gate|readiness)\b"
        ),
        (
            r"\b(?:closeout\s+text|release\s+artifacts?|wazuh(?:\s+signals?)?|"
            r"shuffle(?:\s+receipts?)?|ai(?:\s+output|\s+traces?)?|reports?|"
            r"support\s+bundles?|tickets?|optional\s+evidence|ui\s+cache|demo\s+data|"
            r"verifier(?:\s+output)?|issue-lint(?:\s+output)?)\b.{0,80}"
            r"\b(?:can|may|is\s+allowed\s+to|has\s+authority\s+to)\b.{0,60}"
            r"\b(?:approve|execute|reconcile|close|accept|resolve|authorize|deploy|release)\b"
        ),
        (
            r"\b(?:issue\s+closure|proof-file\s+presence|verifier\s+success|"
            r"issue-lint\s+success)\b.{0,80}"
            r"\b(?:proves?|accepts?|passes?|establishes?)\b.{0,60}"
            r"\b(?:rc|ga|gate|readiness)\b"
        ),
    )
    for pattern in forbidden_claims:
        if re.search(pattern, lowered, flags=re.IGNORECASE):
            fail(
                "Forbidden Phase 66 closeout evaluation readiness or authority claim: "
                f"{clause.strip()}"
            )

    if (
        re.search(r"\b(?:raw|unredacted|customer[-\s]private)\b", lowered)
        and re.search(
            r"\b(?:customer|ticket|alert|log|chat|payload|export|record|data)\b",
            lowered,
        )
        and re.search(
            r"\b(?:includes?|contains?|embeds?|carries?|records?|publishes?|stores?)\b",
            lowered,
        )
    ):
        fail("Forbidden Phase 66 closeout evaluation: customer-private data detected")

customer_identifier_pattern = re.compile(
    r"(?i)\b(?:customer|tenant|account)[\s_-]*(?:id|identifier|email|phone)"
    r"\s*(?::|=|->|\bis\b|\bequals\b)\s*([^\s,;|]+)"
)
for match in customer_identifier_pattern.finditer(normalized):
    value = match.group(1).strip("`'\".,()[]{}")
    if value.startswith(("<", "${", "$")) or value.lower().startswith(
        ("redacted", "example", "placeholder")
    ):
        continue
    fail("Forbidden Phase 66 closeout evaluation: customer-private data detected")

for match in re.finditer(
    r"(?i)\b[A-Z0-9._%+-]+@([A-Z0-9.-]+\.[A-Z]{2,})\b", normalized
):
    if match.group(1).lower().endswith(".invalid"):
        continue
    fail("Forbidden Phase 66 closeout evaluation: customer-private data detected")
PY

path_hygiene_stderr="${repo_root}/.tmp-phase66-8-path-hygiene.err"
trap 'rm -f "${path_hygiene_stderr}"' EXIT
if ! bash "${repo_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" \
  >/dev/null 2>"${path_hygiene_stderr}"; then
  cat "${path_hygiene_stderr}" >&2
  echo "Forbidden Phase 66 closeout evaluation absolute path usage detected" >&2
  exit 1
fi

echo "Phase 66.8 RC closeout evaluation contract and focused negative checks pass."
