#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/deployment/demo-reset-mode-separation.md"
readme_path="${repo_root}/README.md"
fixtures_dir="${repo_root}/docs/deployment/fixtures/demo-reset-mode-separation"

required_headings=(
  "# Phase 55.4 Demo Reset and Mode Separation"
  "## 1. Purpose"
  "## 2. Demo Reset Contract"
  "## 3. Mode Separation"
  "## 4. Reset Safety Rules"
  "## 5. Fixture Expectations"
  "## 6. Validation Rules"
  "## 7. Forbidden Claims"
  "## 8. Validation"
  "## 9. Non-Goals"
)

required_phrases=(
  "- **Status**: Accepted as Phase 55.4 demo reset and mode separation contract"
  "- **Date**: 2026-05-03"
  "- **Related Issues**: #1175, #1178, #1179"
  "This contract defines repeatable demo reset behavior and demo/live mode separation for the Phase 55 guided first-user journey only."
  'Demo reset targets only records that are explicitly labeled with `demo-only`, `first-user-rehearsal`, and `not-production-truth` and bound to the reviewed demo fixture bundle.'
  "Live records, production records, audit records, unlabeled records, imported customer records, and non-demo workflow truth must remain unchanged after every demo reset attempt."
  "Demo mode is explicit rehearsal mode. Live mode is authoritative workflow mode."
  "Reset output, UI state, browser state, logs, verifier output, issue-lint output, and demo labels cannot override authoritative AegisOps live records or production truth."
  "Demo reset must be repeatable by stable demo identifiers and must not append duplicate authoritative records."
  "A failed or rejected demo reset must leave durable live and non-demo state unchanged."
  "Reset reported as backup/restore supportability must fail because this slice does not implement backup, restore, support bundle, or production cleanup behavior."
  'Run `bash scripts/verify-phase-55-4-demo-reset-mode-separation.sh`.'
  'Run `bash scripts/test-verify-phase-55-4-demo-reset-mode-separation.sh`.'
  'Run `bash scripts/verify-publishable-path-hygiene.sh`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1179 --config <supervisor-config-path>`.'
)

fixture_expectations=(
  "valid-repeatable-demo-reset.json|valid|"
  "delete-live-record.json|invalid|demo reset deletes live records"
  "mutate-production-truth.json|invalid|demo reset mutates production truth"
  "unlabeled-record-reset.json|invalid|demo reset targets unlabeled records"
  "backup-restore-claim.json|invalid|reset reported as backup/restore supportability"
)

forbidden_claims=(
  "Demo reset may delete live records"
  "Demo reset may mutate production truth"
  "Unlabeled records may be reset"
  "Demo reset is backup restore supportability"
  "Demo reset is production cleanup"
  "Demo mode is live mode"
  "Live records are demo records"
  "Demo labels override production truth"
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
  echo "Missing Phase 55.4 demo reset and mode separation contract: ${doc_path}" >&2
  exit 1
fi

doc_rendered_markdown="$(rendered_markdown_without_code_blocks "${doc_path}")"

for heading in "${required_headings[@]}"; do
  if ! grep -Fxq -- "${heading}" <<<"${doc_rendered_markdown}"; then
    echo "Missing Phase 55.4 demo reset heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" <<<"${doc_rendered_markdown}"; then
    echo "Missing Phase 55.4 demo reset statement: ${phrase}" >&2
    exit 1
  fi
done

for boundary in "Selector scope" "Repeatability" "Live preservation" "Failure cleanup"; do
  if ! grep -Eq "^\| ${boundary} \| [^|[:space:]][^|]* \| [^|[:space:]][^|]* \|$" <<<"${doc_rendered_markdown}"; then
    echo "Missing complete Phase 55.4 reset boundary row: ${boundary}" >&2
    exit 1
  fi
done

for mode in "Demo" "Live"; do
  if ! grep -Eq "^\| ${mode} \| [^|[:space:]][^|]* \| [^|[:space:]][^|]* \|$" <<<"${doc_rendered_markdown}"; then
    echo "Missing complete Phase 55.4 mode separation row: ${mode}" >&2
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
    echo "Forbidden Phase 55.4 demo reset claim: ${claim}" >&2
    exit 1
  fi
done

path_token_boundary="(^|[[:space:]'\"\`(<{=])"
path_token_chars="[^[:space:]'\"\` )>}|]"
home_absolute_path="/(Users|home)/${path_token_chars}+"
windows_user_path="[A-Za-z]:[\\\\/]Users[\\\\/]${path_token_chars}*"
local_path_token="(${home_absolute_path}|${windows_user_path})"

if grep -REq "(${path_token_boundary}${local_path_token}|file:///?${local_path_token})" "${doc_path}" "${fixtures_dir}" 2>/dev/null; then
  echo "Forbidden Phase 55.4 demo reset contract: workstation-local absolute path detected" >&2
  exit 1
fi

python3 - "${fixtures_dir}" "${fixture_expectations[@]}" <<'PY'
import json
import pathlib
import sys

fixtures_dir = pathlib.Path(sys.argv[1])
expectations = [item.split("|", 2) for item in sys.argv[2:]]
required_labels = {"demo-only", "first-user-rehearsal", "not-production-truth"}

if not fixtures_dir.is_dir():
    print(f"Missing Phase 55.4 demo reset fixtures directory: {fixtures_dir}", file=sys.stderr)
    sys.exit(1)


def record_key(record):
    return record.get("id")


def indexed(records):
    return {
        record_key(record): record
        for record in records
        if isinstance(record, dict) and isinstance(record_key(record), str)
    }


def is_demo_record(record):
    labels = set(record.get("labels") or [])
    return (
        record.get("mode") == "demo"
        and record.get("authority") == "demo_rehearsal_only"
        and required_labels.issubset(labels)
        and record.get("production_claim") is False
        and record.get("truth_surfaces") == []
    )


def is_live_record(record):
    return record.get("mode") == "live" or record.get("authority") == "aegisops_control_plane"


def rejection_reasons(payload):
    reasons = []
    reset = payload.get("reset_contract") or {}
    selector = reset.get("selector")
    selector_labels = set()
    if isinstance(selector, dict) and isinstance(selector.get("labels"), list):
        selector_labels = set(selector.get("labels") or [])

    if payload.get("operation") != "demo-reset" or reset.get("mode") != "demo":
        reasons.append("demo reset targets unlabeled records")
    if reset.get("reported_as") in {"backup-restore", "backup_restore", "supportability", "backup-restore-supportability"}:
        reasons.append("reset reported as backup/restore supportability")
    if (
        not isinstance(selector, dict)
        or selector.get("bundle") != "phase-52-7-demo-seed"
        or not required_labels.issubset(selector_labels)
    ):
        reasons.append("demo reset targets unlabeled records")
    if reset.get("repeatable_by_stable_id") is not True:
        reasons.append("non-repeatable demo reset")
    if reset.get("deletes_live_records") is not False:
        reasons.append("demo reset deletes live records")
    if reset.get("mutates_production_truth") is not False:
        reasons.append("demo reset mutates production truth")

    before = payload.get("before_records")
    after = payload.get("after_records")
    if not isinstance(before, list) or not isinstance(after, list):
        reasons.append("missing reset record snapshot")
        return reasons

    before_by_id = indexed(before)
    after_by_id = indexed(after)
    if len(before_by_id) != len(before) or len(after_by_id) != len(after):
        reasons.append("non-repeatable demo reset")

    demo_before_ids = {
        record["id"]
        for record in before
        if isinstance(record, dict) and isinstance(record.get("id"), str) and is_demo_record(record)
    }
    demo_after_ids = {
        record["id"]
        for record in after
        if isinstance(record, dict) and isinstance(record.get("id"), str) and is_demo_record(record)
    }
    if demo_before_ids != demo_after_ids:
        reasons.append("non-repeatable demo reset")

    for record in before:
        if not isinstance(record, dict) or not isinstance(record.get("id"), str):
            continue
        after_record = after_by_id.get(record["id"])
        if is_live_record(record):
            if after_record is None:
                reasons.append("demo reset deletes live records")
            elif after_record != record:
                reasons.append("demo reset mutates production truth")
        elif not is_demo_record(record):
            if after_record != record:
                reasons.append("demo reset targets unlabeled records")

    for record in after:
        if not isinstance(record, dict) or not isinstance(record.get("id"), str):
            continue
        if record["id"] not in before_by_id:
            if is_live_record(record):
                reasons.append("demo reset mutates production truth")
            elif not is_demo_record(record):
                reasons.append("demo reset targets unlabeled records")
            continue
        if is_live_record(record) and record.get("production_claim") is not True:
            reasons.append("demo reset mutates production truth")
        if record.get("reset_reported_as") in {"backup-restore", "backup_restore", "supportability", "backup-restore-supportability"}:
            reasons.append("reset reported as backup/restore supportability")

    return reasons


for fixture, expected_validity, required_rejection in expectations:
    path = fixtures_dir / fixture
    if not path.is_file():
        print(f"Missing Phase 55.4 demo reset fixture: {fixture}", file=sys.stderr)
        sys.exit(1)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Invalid Phase 55.4 demo reset fixture JSON for {fixture}: {exc}", file=sys.stderr)
        sys.exit(1)

    reasons = rejection_reasons(payload)
    if expected_validity == "valid" and reasons:
        print(
            f"Invalid Phase 55.4 demo reset fixture state for {fixture}: expected valid, got {sorted(set(reasons))}",
            file=sys.stderr,
        )
        sys.exit(1)
    if expected_validity == "invalid":
        if not reasons:
            print(f"Invalid Phase 55.4 demo reset fixture state for {fixture}: expected rejection", file=sys.stderr)
            sys.exit(1)
        if required_rejection not in reasons:
            print(
                f"Invalid Phase 55.4 demo reset fixture state for {fixture}: expected {required_rejection}",
                file=sys.stderr,
            )
            sys.exit(1)
PY

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing README for Phase 55.4 demo reset link check: ${readme_path}" >&2
  exit 1
fi

readme_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${readme_path}" | perl -pe 's/`[^`]*`//g'
)"

if ! grep -Eq '\[[^]]+\]\(docs/deployment/demo-reset-mode-separation\.md\)' <<<"${readme_rendered_markdown}"; then
  echo "README must link the Phase 55.4 demo reset and mode separation contract." >&2
  exit 1
fi

echo "Phase 55.4 demo reset and mode separation contract verified."
