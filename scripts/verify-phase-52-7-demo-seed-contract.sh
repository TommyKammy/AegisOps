#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/deployment/demo-seed-contract.md"
readme_path="${repo_root}/README.md"
fixtures_dir="${repo_root}/docs/deployment/fixtures/demo-seed"

required_headings=(
  "# Phase 52.7 Demo Seed Contract"
  "## 1. Purpose"
  "## 2. Authority Boundary"
  "## 3. Seed Record Contract"
  "## 4. Demo Labels"
  "## 5. Reset Behavior"
  "## 6. Production Exclusion Rules"
  "## 7. Fixture Expectations"
  "## 8. Validation Rules"
  "## 9. Forbidden Claims"
  "## 10. Validation"
  "## 11. Non-Goals"
)

required_phrases=(
  "- **Status**: Accepted"
  "- **Date**: 2026-05-01"
  "- **Related Issues**: #1063, #1065, #1070"
  "This contract defines demo seed records and demo/prod separation expectations for the executable first-user stack only. It does not implement the full first-user UI journey, production data import, Wazuh product profiles, Shuffle product profiles, release-candidate behavior, general-availability behavior, or runtime behavior."
  "Demo seed output is workflow rehearsal evidence only."
  "Demo records, demo labels, fixture provenance, reset output, fake secrets, sample credentials, demo source state, and operator-facing seed summaries are not production truth, gate truth, customer evidence, approval truth, execution truth, or reconciliation truth."
  "AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, release, gate, and closeout truth."
  'This contract cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md`.'
  "| Record type | Required demo fields | Presentation rule | Production exclusion |"
  "| Label | Required value | Validation rule |"
  "| Reset boundary | Required behavior | Rejection rule |"
  'Reset selectors must be structured as `{"bundle":"phase-52-7-demo-seed","labels":["demo-only","first-user-rehearsal","not-production-truth"]}` or an equivalent object with the same bundle and label constraints.'
  "| Fixture | Expected validity | Required rejection |"
  'Run `bash scripts/verify-phase-52-7-demo-seed-contract.sh`.'
  'Run `bash scripts/test-verify-phase-52-7-demo-seed-contract.sh`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1178 --config <supervisor-config-path>`.'
)

record_types=(
  "Demo Wazuh alert"
  "Demo analytic signal"
  "Demo AegisOps alert"
  "Demo alert"
  "Demo case"
  "Demo evidence"
  "Demo recommendation"
  "Demo action review"
  "Demo action request"
  "Demo approval"
  "Demo execution receipt"
  "Demo reconciliation"
  "Demo reconciliation note"
)

labels=(
  "demo-only"
  "first-user-rehearsal"
  "not-production-truth"
)

reset_boundaries=(
  "Selector scope"
  "Production guard"
  "Failure cleanup"
)

fixture_expectations=(
  "valid-demo-seed.json|valid|"
  "missing-label.json|invalid|missing required demo label"
  "destructive-reset.json|invalid|reset deletes production records"
  "production-claim.json|invalid|demo record claims production truth"
)

forbidden_claims=(
  "Demo data is production truth"
  "Demo record is production truth"
  "Demo seed output is gate truth"
  "Demo reset may delete production records"
  "Demo labels are optional"
  "Fake credentials are valid credentials"
  "Sample credentials are valid credentials"
  "Demo source state is customer evidence"
  "Demo approval is approval truth"
  "Demo execution receipt is execution truth"
  "Demo reconciliation note is reconciliation truth"
  "This contract implements production data import"
  "This contract implements Wazuh product profiles"
  "This contract implements Shuffle product profiles"
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
  echo "Missing Phase 52.7 demo seed contract: ${doc_path}" >&2
  exit 1
fi

doc_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${doc_path}"
)"

for heading in "${required_headings[@]}"; do
  if ! grep -Fxq -- "${heading}" <<<"${doc_rendered_markdown}"; then
    echo "Missing Phase 52.7 demo seed contract heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" <<<"${doc_rendered_markdown}"; then
    echo "Missing Phase 52.7 demo seed contract statement: ${phrase}" >&2
    exit 1
  fi
done

for record_type in "${record_types[@]}"; do
  if ! grep -Eq "^\| ${record_type} \| [^|[:space:]][^|]* \| [^|[:space:]][^|]* \| [^|[:space:]][^|]* \|$" <<<"${doc_rendered_markdown}"; then
    echo "Missing complete Phase 52.7 seed record row: ${record_type}" >&2
    exit 1
  fi
done

for label in "${labels[@]}"; do
  if ! grep -Eq "^\| \`${label}\` \| [^|[:space:]][^|]* \| [^|[:space:]][^|]* \|$" <<<"${doc_rendered_markdown}"; then
    echo "Missing complete Phase 52.7 demo label row: ${label}" >&2
    exit 1
  fi
done

for reset_boundary in "${reset_boundaries[@]}"; do
  if ! grep -Eq "^\| ${reset_boundary} \| [^|[:space:]][^|]* \| [^|[:space:]][^|]* \|$" <<<"${doc_rendered_markdown}"; then
    echo "Missing complete Phase 52.7 reset boundary row: ${reset_boundary}" >&2
    exit 1
  fi
done

contains_forbidden_outside_forbidden_section() {
  local claim="$1"

  awk -v claim="${claim}" '
    BEGIN { claim_lower = tolower(claim) }
    /^## 9\. Forbidden Claims$/ { in_forbidden_claims = 1; next }
    /^## / && in_forbidden_claims { in_forbidden_claims = 0 }
    !in_forbidden_claims && index(tolower($0), claim_lower) { found = 1 }
    END { exit(found ? 0 : 1) }
  ' "${doc_path}"
}

for claim in "${forbidden_claims[@]}"; do
  if contains_forbidden_outside_forbidden_section "${claim}"; then
    echo "Forbidden Phase 52.7 demo seed contract claim: ${claim}" >&2
    exit 1
  fi
done

path_token_boundary="(^|[[:space:]'\"\`(<{=])"
path_token_chars="[^[:space:]'\"\` )>}|]"
home_absolute_path="/(Users|home)/${path_token_chars}+"
windows_user_path="[A-Za-z]:[\\\\/]Users[\\\\/]${path_token_chars}*"
local_path_token="(${home_absolute_path}|${windows_user_path})"

if grep -REq "(${path_token_boundary}${local_path_token}|file:///?${local_path_token})" "${doc_path}" "${fixtures_dir}" 2>/dev/null; then
  echo "Forbidden Phase 52.7 demo seed contract: workstation-local absolute path detected" >&2
  exit 1
fi

python3 - "${fixtures_dir}" "${fixture_expectations[@]}" <<'PY'
from collections import Counter
import json
import pathlib
import sys

fixtures_dir = pathlib.Path(sys.argv[1])
expectations = [item.split("|", 2) for item in sys.argv[2:]]

if not fixtures_dir.is_dir():
    print(f"Missing Phase 52.7 demo seed fixtures directory: {fixtures_dir}", file=sys.stderr)
    sys.exit(1)

required_labels = {"demo-only", "first-user-rehearsal", "not-production-truth"}
truth_surfaces = {
    "production",
    "gate",
    "customer_evidence",
    "approval",
    "execution",
    "reconciliation",
    "closeout",
}


def has_non_empty_string(record, field):
    return isinstance(record.get(field), str) and bool(record.get(field).strip())


def has_field(record, field):
    return field in record


type_requirements = {
    "demo-wazuh-alert": {
        "presentation": "demo-only Wazuh alert rehearsal",
        "non_empty": ("id", "fixture_provenance", "demo_source_family", "wazuh_alert_id"),
        "present": ("reviewed_at",),
    },
    "demo-analytic-signal": {
        "presentation": "demo-only analytic signal rehearsal",
        "non_empty": ("id", "linked_demo_wazuh_alert_id", "signal_name", "signal_disposition"),
        "present": (),
    },
    "demo-aegisops-alert": {
        "presentation": "demo-only AegisOps alert rehearsal",
        "non_empty": ("id", "linked_demo_signal_id", "control_plane_alert_id", "alert_state"),
        "present": ("reviewed_at",),
    },
    "demo-alert": {
        "presentation": "demo-only alert rehearsal",
        "non_empty": ("id", "fixture_provenance", "demo_source_family"),
        "present": ("reviewed_at",),
    },
    "demo-case": {
        "presentation": "demo-only case rehearsal",
        "non_empty": ("id", "linked_demo_alert_id", "rehearsal_status"),
        "present": ("analyst_owner",),
    },
    "demo-evidence": {
        "presentation": "demo-only evidence rehearsal",
        "non_empty": ("id", "linked_demo_case_id", "fixture_path", "provenance_note"),
        "present": (),
    },
    "demo-recommendation": {
        "presentation": "demo-only recommendation rehearsal",
        "non_empty": ("id", "linked_demo_case_id", "recommended_action", "recommendation_basis"),
        "present": (),
    },
    "demo-action-review": {
        "presentation": "demo-only action review rehearsal",
        "non_empty": ("id", "linked_demo_recommendation_id", "review_decision", "review_boundary"),
        "present": (),
    },
    "demo-action-request": {
        "presentation": "demo-only action rehearsal",
        "non_empty": ("id", "linked_demo_case_id", "requested_action"),
        "present": ("non_production_scope",),
    },
    "demo-approval": {
        "presentation": "demo-only approval rehearsal",
        "non_empty": ("id", "linked_demo_action_request_id"),
        "present": ("reviewer_placeholder",),
    },
    "demo-execution-receipt": {
        "presentation": "demo-only execution rehearsal",
        "non_empty": ("id", "linked_demo_action_review_id", "mocked_executor_note"),
        "present": (),
    },
    "demo-reconciliation-note": {
        "presentation": "demo-only reconciliation rehearsal",
        "non_empty": ("id", "linked_demo_execution_receipt_id", "outcome_placeholder"),
        "present": (),
    },
    "demo-reconciliation": {
        "presentation": "demo-only reconciliation rehearsal",
        "non_empty": ("id", "linked_demo_execution_receipt_id", "reconciliation_result", "outcome_placeholder"),
        "present": (),
    },
}

required_record_types = {
    "demo-wazuh-alert",
    "demo-analytic-signal",
    "demo-aegisops-alert",
    "demo-case",
    "demo-evidence",
    "demo-recommendation",
    "demo-action-review",
    "demo-execution-receipt",
    "demo-reconciliation",
}

required_linkages = {
    "demo-analytic-signal": ("linked_demo_wazuh_alert_id", "demo-wazuh-alert"),
    "demo-aegisops-alert": ("linked_demo_signal_id", "demo-analytic-signal"),
    "demo-case": ("linked_demo_alert_id", "demo-aegisops-alert"),
    "demo-evidence": ("linked_demo_case_id", "demo-case"),
    "demo-recommendation": ("linked_demo_case_id", "demo-case"),
    "demo-action-review": ("linked_demo_recommendation_id", "demo-recommendation"),
    "demo-action-request": ("linked_demo_case_id", "demo-case"),
    "demo-approval": ("linked_demo_action_request_id", "demo-action-request"),
    "demo-execution-receipt": ("linked_demo_action_review_id", "demo-action-review"),
    "demo-reconciliation": ("linked_demo_execution_receipt_id", "demo-execution-receipt"),
    "demo-reconciliation-note": ("linked_demo_execution_receipt_id", "demo-execution-receipt"),
}


def rejection_reasons(payload):
    reasons = []
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        reasons.append("missing records")
        return reasons

    for record in records:
        record_type = record.get("type")
        if not has_non_empty_string(record, "id"):
            reasons.append("missing stable demo record identifier")
            continue
        requirements = type_requirements.get(record_type)
        if requirements is None:
            reasons.append("missing demo record type contract")
        else:
            for field in requirements["non_empty"]:
                if not has_non_empty_string(record, field):
                    reasons.append(f"missing {record_type} field {field}")
            for field in requirements["present"]:
                if not has_field(record, field):
                    reasons.append(f"missing {record_type} field {field}")
            if record.get("presentation") != requirements["presentation"]:
                reasons.append(f"missing {record_type} presentation")

        labels = set(record.get("labels") or [])
        if not required_labels.issubset(labels):
            reasons.append("missing required demo label")
        if record.get("production_claim") is not False:
            reasons.append("demo record claims production truth")
        if record.get("truth_surfaces") != []:
            reasons.append("demo record claims production truth")
        if record.get("authority") != "demo_rehearsal_only":
            reasons.append("demo record claims production truth")

    records_by_id = {
        record.get("id"): record
        for record in records
        if isinstance(record.get("id"), str) and record.get("id").strip()
    }
    if len(records_by_id) != len(records):
        reasons.append("non-repeatable seed load")

    record_type_counts = Counter(record.get("type") for record in records)
    for required_record_type in sorted(required_record_types):
        required_record_type_count = record_type_counts.get(required_record_type, 0)
        if required_record_type_count == 0:
            reasons.append(f"missing required record family {required_record_type}")
        elif required_record_type_count > 1:
            reasons.append(f"multiple records in required family {required_record_type}")

    for record in records:
        record_type = record.get("type")
        linkage = required_linkages.get(record_type)
        if linkage is None:
            continue
        linkage_field, expected_parent_type = linkage
        parent_id = record.get(linkage_field)
        parent_record = records_by_id.get(parent_id)
        if parent_record is None or parent_record.get("type") != expected_parent_type:
            reasons.append("missing expected record family linkage")

    repeatability = payload.get("repeatability") or {}
    if repeatability.get("load_strategy") != "upsert-demo-records-by-stable-id":
        reasons.append("non-repeatable seed load")
    if repeatability.get("duplicate_behavior") != "replace-demo-record-family-only":
        reasons.append("non-repeatable seed load")
    if not isinstance(repeatability.get("idempotency_key"), str) or not repeatability.get("idempotency_key").strip():
        reasons.append("non-repeatable seed load")

    reset = payload.get("reset") or {}
    if reset.get("deletes_production_records") is not False:
        reasons.append("reset deletes production records")
    if reset.get("scope") != "demo-bundle-only":
        reasons.append("reset deletes production records")
    selector = reset.get("selector")
    selector_labels = set()
    if isinstance(selector, dict) and isinstance(selector.get("labels"), list):
        selector_labels = set(selector.get("labels") or [])
    if (
        not isinstance(selector, dict)
        or selector.get("bundle") != "phase-52-7-demo-seed"
        or not required_labels.issubset(selector_labels)
    ):
        reasons.append("reset deletes production records")

    exclusion = payload.get("production_exclusion") or {}
    if exclusion.get("may_satisfy_production_truth") is not False:
        reasons.append("demo record claims production truth")
    blocked = set(exclusion.get("blocked_truth_surfaces") or [])
    if not truth_surfaces.issubset(blocked):
        reasons.append("demo record claims production truth")

    if payload.get("mode") != "demo":
        reasons.append("missing required demo label")

    return reasons


for fixture, expected_validity, required_rejection in expectations:
    path = fixtures_dir / fixture
    if not path.is_file():
        print(f"Missing Phase 52.7 demo seed fixture: {fixture}", file=sys.stderr)
        sys.exit(1)

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Invalid Phase 52.7 demo seed fixture JSON for {fixture}: {exc}", file=sys.stderr)
        sys.exit(1)

    reasons = rejection_reasons(payload)
    if expected_validity == "valid" and reasons:
        print(
            f"Invalid Phase 52.7 demo seed fixture state for {fixture}: expected valid, got {sorted(set(reasons))}",
            file=sys.stderr,
        )
        sys.exit(1)
    if expected_validity == "invalid":
        if not reasons:
            print(f"Invalid Phase 52.7 demo seed fixture state for {fixture}: expected rejection", file=sys.stderr)
            sys.exit(1)
        if required_rejection not in reasons:
            print(
                f"Invalid Phase 52.7 demo seed fixture state for {fixture}: expected {required_rejection}",
                file=sys.stderr,
            )
            sys.exit(1)
PY

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing README for Phase 52.7 demo seed contract link check: ${readme_path}" >&2
  exit 1
fi

readme_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${readme_path}" | perl -pe 's/`[^`]*`//g'
)"

if ! grep -Eq '\[[^]]+\]\(docs/deployment/demo-seed-contract\.md\)' <<<"${readme_rendered_markdown}"; then
  echo "README must link the Phase 52.7 demo seed contract." >&2
  exit 1
fi

echo "Phase 52.7 demo seed contract verified."
