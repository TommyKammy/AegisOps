#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/getting-started/first-user-demo-report-export.md"
readme_path="${repo_root}/README.md"
fixtures_dir="${repo_root}/docs/getting-started/fixtures/first-user-demo-report-export"

required_headings=(
  "# Phase 55.6 First-User Demo Report Export Skeleton"
  "## 1. Purpose"
  "## 2. Export Skeleton Contract"
  "## 3. Demo Journey References"
  "## 4. Secret Hygiene"
  "## 5. Fixture Expectations"
  "## 6. Validation Rules"
  "## 7. Forbidden Claims"
  "## 8. Validation"
  "## 9. Non-Goals"
)

required_phrases=(
  "- **Status**: Accepted as Phase 55.6 first-user demo report export skeleton"
  "- **Date**: 2026-05-03"
  "- **Related Issues**: #1175, #1178, #1181"
  "This skeleton defines demo-labeled report export output for the Phase 55 guided first-user journey only."
  "Demo report export output is demo evidence only."
  'Every exported artifact must carry the labels `demo-only`, `first-user-rehearsal`, and `not-production-truth`.'
  "AegisOps control-plane records remain authoritative for alert, case, evidence, recommendation, action review, execution receipt, reconciliation, audit, limitation, release, gate, and closeout truth."
  "Export output, generated files, report metadata, UI state, browser state, verifier output, and issue-lint output cannot become production truth or override authoritative workflow records."
  "The export skeleton must include directly linked demo alert, case, evidence, recommendation, action review, execution receipt, and reconciliation references when those records are available from the demo bundle."
  "Secret values, placeholder credentials, fake secrets, sample credentials, unsigned tokens, TODO values, bearer tokens, API keys, passwords, private keys, session cookies, and customer-specific credentials must not appear in exported output."
  'This skeleton cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md`.'
  'Run `bash scripts/verify-phase-55-6-first-user-report-export-skeleton.sh`.'
  'Run `bash scripts/test-verify-phase-55-6-first-user-report-export-skeleton.sh`.'
  'Run `bash scripts/verify-publishable-path-hygiene.sh`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1181 --config <supervisor-config-path>`.'
)

reference_rows=(
  "Demo alert"
  "Demo case"
  "Demo evidence"
  "Demo recommendation"
  "Demo action review"
  "Demo execution receipt"
  "Demo reconciliation"
)

fixture_expectations=(
  "valid-demo-report-export.json|valid|"
  "unavailable-follow-up-reference.json|valid|"
  "missing-demo-label.json|invalid|missing required demo label"
  "secret-looking-value.json|invalid|secret-looking value in export output"
  "key-secret-looking-value.json|invalid|secret-looking value in export output"
  "commercial-report-claim.json|invalid|demo export claims commercial report breadth"
  "production-truth-claim.json|invalid|demo export claims production truth"
  "authority-override-claim.json|invalid|demo export claims it can override authoritative records"
  "missing-reference-availability.json|invalid|missing demo journey reference"
)

forbidden_claims=(
  "Demo report export is production truth"
  "Demo report export is commercial reporting completeness"
  "Demo report export is audit export completeness"
  "Demo report export is RC proof"
  "Demo report export is GA readiness"
  "Demo report export is commercial readiness"
  "Demo export may include secrets"
  "Demo export may include credentials"
  "Report metadata overrides authoritative records"
  "Generated report files override authoritative records"
)

rendered_markdown_without_code_blocks() {
  local markdown_path="$1"

  awk '
    /^[[:space:]]*(```|~~~)/ {
      in_fenced_block = !in_fenced_block
      next
    }
    in_fenced_block { next }
    substr($0, 1, 1) == "\t" { next }
    substr($0, 1, 4) == "    " { next }
    { print }
  ' "${markdown_path}" | perl -0pe 's/<!--.*?-->//gs'
}

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Phase 55.6 first-user demo report export skeleton: ${doc_path}" >&2
  exit 1
fi

doc_rendered_markdown="$(rendered_markdown_without_code_blocks "${doc_path}")"

for heading in "${required_headings[@]}"; do
  if ! grep -Fxq -- "${heading}" <<<"${doc_rendered_markdown}"; then
    echo "Missing Phase 55.6 report export skeleton heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" <<<"${doc_rendered_markdown}"; then
    echo "Missing Phase 55.6 report export skeleton statement: ${phrase}" >&2
    exit 1
  fi
done

for row in "${reference_rows[@]}"; do
  if ! grep -Eq "^\| ${row} \| [^|[:space:]][^|]* \| [^|[:space:]][^|]* \|$" <<<"${doc_rendered_markdown}"; then
    echo "Missing complete Phase 55.6 demo journey reference row: ${row}" >&2
    exit 1
  fi
done

contains_forbidden_outside_forbidden_section() {
  local claim="$1"

  awk -v claim="${claim}" '
    BEGIN { claim_lower = tolower(claim) }
    /^## 7\. Forbidden Claims$/ { in_forbidden_claims = 1; next }
    /^## / && in_forbidden_claims { in_forbidden_claims = 0 }
    !in_forbidden_claims && index(tolower($0), claim_lower) { found = 1 }
    END { exit(found ? 0 : 1) }
  ' "${doc_path}"
}

for claim in "${forbidden_claims[@]}"; do
  if contains_forbidden_outside_forbidden_section "${claim}"; then
    echo "Forbidden Phase 55.6 report export skeleton claim: ${claim}" >&2
    exit 1
  fi
done

path_token_boundary="(^|[[:space:]'\"\`(<{=])"
path_token_chars="[^[:space:]'\"\` )>}|]"
home_absolute_path="/(Users|home)/${path_token_chars}+"
windows_user_path="[A-Za-z]:[\\\\/]Users[\\\\/]${path_token_chars}*"
local_path_token="(${home_absolute_path}|${windows_user_path})"

if grep -REq "(${path_token_boundary}${local_path_token}|file:///?${local_path_token})" "${doc_path}" "${fixtures_dir}" 2>/dev/null; then
  echo "Forbidden Phase 55.6 report export skeleton: workstation-local absolute path detected" >&2
  exit 1
fi

python3 - "${fixtures_dir}" "${fixture_expectations[@]}" <<'PY'
import json
import pathlib
import re
import sys

fixtures_dir = pathlib.Path(sys.argv[1])
expectations = [item.split("|", 2) for item in sys.argv[2:]]
required_labels = {"demo-only", "first-user-rehearsal", "not-production-truth"}
required_references = {
    "demo_alert",
    "demo_case",
    "demo_evidence",
    "demo_recommendation",
    "demo_action_review",
    "demo_execution_receipt",
    "demo_reconciliation",
}
secret_patterns = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"correcthorsebatterystaple",
        r"sk-[A-Za-z0-9_-]{12,}",
        r"ghp_[A-Za-z0-9_]{12,}",
        r"bearer\s+[A-Za-z0-9._-]{12,}",
        r"api[_-]?key\s*[:=]\s*['\"]?[^'\"\s]{8,}",
        r"password\s*[:=]\s*['\"]?[^'\"\s]{8,}",
        r"token\s*[:=]\s*['\"]?[^'\"\s]{8,}",
        r"secret\s*[:=]\s*['\"]?[^'\"\s]{8,}",
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    )
]

if not fixtures_dir.is_dir():
    print(f"Missing Phase 55.6 report export fixtures directory: {fixtures_dir}", file=sys.stderr)
    sys.exit(1)


def walk_strings(value, path=""):
    if isinstance(value, str):
        yield f"{path}: {value}" if path else value
    elif isinstance(value, dict):
        for key, item in value.items():
            next_path = f"{path}.{key}" if path else str(key)
            yield str(key)
            yield from walk_strings(item, next_path)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            next_path = f"{path}[{index}]" if path else f"[{index}]"
            yield from walk_strings(item, next_path)


def reasons_for(payload):
    reasons = []
    labels = set(payload.get("labels") or [])
    if payload.get("report_type") != "first-user-demo-report-export":
        reasons.append("missing required demo label")
    if payload.get("mode") != "demo" or not required_labels.issubset(labels):
        reasons.append("missing required demo label")
    if payload.get("demo_evidence_only") is not True:
        reasons.append("missing required demo label")
    if payload.get("commercial_report_breadth_claim") is not False:
        reasons.append("demo export claims commercial report breadth")
    if payload.get("audit_export_completeness_claim") is not False:
        reasons.append("demo export claims commercial report breadth")
    if payload.get("rc_or_ga_readiness_claim") is not False:
        reasons.append("demo export claims commercial report breadth")
    if payload.get("production_truth_claim") is not False:
        reasons.append("demo export claims production truth")
    authority = payload.get("authority_boundary") or {}
    if authority.get("output_is_production_truth") is not False:
        reasons.append("demo export claims production truth")
    if authority.get("authoritative_record_source") != "aegisops_control_plane":
        reasons.append("demo export claims production truth")
    if authority.get("output_overrides_authoritative_records") is not False:
        reasons.append("demo export claims it can override authoritative records")

    references = payload.get("references")
    if not isinstance(references, dict):
        reasons.append("missing demo journey reference")
    else:
        missing = required_references - set(references)
        if missing:
            reasons.append("missing demo journey reference")
        for name in required_references & set(references):
            ref = references.get(name)
            if not isinstance(ref, dict) or ref.get("available") not in (True, False):
                reasons.append("missing demo journey reference")
                continue
            if ref.get("available") is False:
                continue
            ref_labels = set(ref.get("labels") or [])
            if not required_labels.issubset(ref_labels):
                reasons.append("missing required demo label")
            if ref.get("secret_redaction") != "no-secret-values-exported":
                reasons.append("secret-looking value in export output")

    for text in walk_strings(payload):
        if any(pattern.search(text) for pattern in secret_patterns):
            reasons.append("secret-looking value in export output")
            break
        lowered = text.lower()
        if "production truth" in lowered and "not production truth" not in lowered:
            reasons.append("demo export claims production truth")
        if "commercial report" in lowered and not any(
            marker in lowered for marker in ("not commercial", "no commercial", "outside commercial")
        ):
            reasons.append("demo export claims commercial report breadth")

    return sorted(set(reasons))


for filename, expected_validity, required_reason in expectations:
    fixture_path = fixtures_dir / filename
    if not fixture_path.is_file():
        print(f"Missing Phase 55.6 report export fixture: {fixture_path}", file=sys.stderr)
        sys.exit(1)
    try:
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON in Phase 55.6 report export fixture {filename}: {exc}", file=sys.stderr)
        sys.exit(1)

    reasons = reasons_for(payload)
    if expected_validity == "valid":
        if reasons:
            print(f"Expected valid Phase 55.6 report export fixture {filename}, got: {', '.join(reasons)}", file=sys.stderr)
            sys.exit(1)
    elif not reasons:
        print(f"Expected invalid Phase 55.6 report export fixture {filename}", file=sys.stderr)
        sys.exit(1)
    elif required_reason and required_reason not in reasons:
        print(
            f"Expected Phase 55.6 report export fixture {filename} to fail with {required_reason}, got: {', '.join(reasons)}",
            file=sys.stderr,
        )
        sys.exit(1)

print("Phase 55.6 report export fixtures preserve demo labels, direct references, secret hygiene, and scope boundaries.")
PY

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing README for Phase 55.6 report export skeleton link check: ${readme_path}" >&2
  exit 1
fi

readme_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${readme_path}" | perl -pe 's/`[^`]*`//g'
)"

if ! grep -Eq '\[[^]]+\]\(docs/getting-started/first-user-demo-report-export\.md\)' <<<"${readme_rendered_markdown}"; then
  echo "README must link the Phase 55.6 first-user demo report export skeleton." >&2
  exit 1
fi

echo "Phase 55.6 first-user demo report export skeleton is demo-labeled, secret-clean, and scope-bounded."
