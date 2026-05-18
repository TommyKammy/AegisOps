#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"

doc_path="docs/phase-62-closeout-evaluation.md"
absolute_doc_path="${repo_root}/${doc_path}"
readme_path="${repo_root}/README.md"

require_phrase() {
  local file="$1"
  local phrase="$2"
  local description="$3"

  if ! grep -Fq -- "${phrase}" "${file}"; then
    echo "Missing ${description}: ${phrase}" >&2
    exit 1
  fi
}

if [[ ! -s "${absolute_doc_path}" ]]; then
  echo "Missing Phase 62 closeout evaluation: ${doc_path}" >&2
  exit 1
fi

if [[ ! -s "${readme_path}" ]]; then
  echo "Missing README for Phase 62 closeout link check: README.md" >&2
  exit 1
fi

require_phrase "${readme_path}" "- [Phase 62.8 closeout evaluation](docs/phase-62-closeout-evaluation.md)" "README canonical cross-phase boundary bullet"
require_phrase "${readme_path}" "The Phase 62.8 closeout evaluation is defined by the [Phase 62.8 closeout evaluation](docs/phase-62-closeout-evaluation.md)." "README Product positioning reference"

required_phrases=()
while IFS= read -r phrase; do
  required_phrases+=("${phrase}")
done <<'EOF_PHRASE'
# Phase 62 Closeout Evaluation
**Status**: Accepted as Minimum SOAR Replacement Breadth before Phase 63 evidence expansion, Phase 66 RC proof, Beta, RC, GA, and commercial replacement-readiness claims.
**Related Issues**: #1314, #1315, #1316, #1317, #1318, #1319, #1320, #1321, #1322
Phase 62 is accepted as the Minimum SOAR Replacement Breadth slice for reviewed automation catalog, per-action policy, per-action receipt and reconciliation, Shuffle workflow mapping, manual fallback, demo/test simulator, and action catalog UI workflows.
AegisOps records remain authoritative for case, evidence, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, and closeout truth.
Shuffle workflow state, simulator state, ticket state, UI cache, browser state, AI output, source-native state, verifier output, and issue-lint output remain subordinate context and cannot approve, execute, reconcile, close, gate, or claim readiness by themselves.
Phase 62 must reject missing child evidence, missing verifier output, missing issue-lint summary, downstream workflow truth claims, simulator production truth claims, Controlled Write or Hard Write default enablement claims, broad SOAR marketplace claims, Phase 63 evidence expansion claims, Phase 66 RC proof claims, Beta/RC/GA/commercial-readiness claims, production secrets, and workstation-local paths.
This closeout does not claim Phase 63 evidence expansion is complete, Phase 66 RC proof is complete, AegisOps is Beta, RC, GA, self-service commercially ready, or a commercial replacement for every SIEM/SOAR capability.
| #1314 | Epic: Phase 62 Minimum SOAR Replacement Breadth | Open until #1322 lands; accepted when this closeout, focused verifiers, focused backend/UI tests, authority-boundary checks, publishable path hygiene, and issue-lint pass. |
| #1315 | Phase 62.1 reviewed automation catalog contract | Closed. `docs/phase-62-reviewed-automation-catalog-contract.md`, validation notes, focused verifier, and backend contract tests prove the bounded default Read, Notify, and Soft Write catalog without direct Shuffle launch, marketplace expansion, or write-authority overclaim. |
| #1316 | Phase 62.2 per-action policy registry | Closed. `control-plane/aegisops/control_plane/actions/action_policy_registry.py`, focused policy tests, and service persistence tests prove reviewed requester, reviewer, scope, idempotency, protected-target, and expiry checks for catalog actions. |
| #1317 | Phase 62.3 per-action reconciliation contract | Closed. `docs/phase-62-3-per-action-reconciliation-contract.md`, validation notes, registry metadata, focused tests, and verifier prove expected receipt fields, correlation fields, and reconciliation outcomes while rejecting downstream-only success. |
| #1318 | Phase 62.4 Shuffle workflow mapping for catalog | Closed. Delegation, Shuffle adapter, policy registry, and service persistence tests prove reviewed catalog actions map through AegisOps delegation without direct workflow launch, ticket-state authority, or callback-only reconciliation. |
| #1319 | Phase 62.5 manual fallback for every action | Closed. `docs/phase-62-5-manual-fallback-contract.md`, validation notes, fallback registry requirements, Phase 54 fallback preservation, and authority-boundary checks prove fallback owner, operator note, affected action, blocked reason, expected evidence, and follow-up posture without approval, execution, or reconciliation bypass. |
| #1320 | Phase 62.6 automation simulator for demo/test mode | Closed. `docs/phase-62-6-automation-simulator-contract.md`, validation notes, simulator registry requirements, focused tests, and receipt validation prove demo/test-only simulator output with synthetic or sanitized data and no production receipt or reconciliation truth. |
| #1321 | Phase 62.7 action catalog UI | Closed. `apps/operator-ui/src/app/operatorConsolePages/actionCatalogPages.tsx`, route wiring, and `apps/operator-ui/src/app/OperatorRoutes.actionCatalog.testSuite.tsx` render reviewed catalog posture from backend records while keeping UI cache, browser state, simulator output, ticket state, and automation substrate status subordinate. |
| #1322 | Phase 62.8 Phase 62 closeout evaluation | Open until this document and focused closeout verifier land. |
Reviewed automation catalog validation rejects missing owner, missing action family, missing approval posture, missing receipt expectation, missing reconciliation expectation, missing role boundary, missing idempotency posture, missing limitation, direct ad-hoc Shuffle launch, downstream-truth promotion, broad SOAR marketplace overclaim, Controlled Write default enablement, and Hard Write default enablement.
Per-action policy validation rejects missing reviewed policy, requester role drift, reviewer role drift, expired policy, missing idempotency key, target-scope misuse, protected-target misuse, approval bypass, and policy-derived authority overclaim.
Per-action reconciliation validation rejects downstream success without an AegisOps-bound receipt, missing receipt fields, correlation mismatch, stale receipt, duplicate receipt, wrong correlation, and reconciliation truth derived only from workflow or ticket status.
Shuffle mapping validation rejects direct workflow launch, unmapped catalog action delegation, workflow-state approval or execution truth, ticket-state case truth, and callback-only reconciliation.
Manual fallback validation rejects missing fallback owner, missing operator note, missing affected action, unsupported fallback state, missing expected evidence, fallback approval bypass, fallback execution proof, fallback receipt validation, and fallback case closure.
Simulator validation rejects non-demo/test mode, unsupported action, missing demo/test label, missing production exclusion, live secret references, customer-private data, simulator receipt truth, simulator reconciliation truth, and production-ready simulator claims.
Action catalog UI tests reject UI-cache authority, browser-state authority, simulator-output truth, downstream-ticket truth, Controlled Write default controls, Hard Write default controls, and missing backend record binding.
Path hygiene rejects workstation-local absolute paths in publishable docs, scripts, tests, prompts, and validation output.
`bash scripts/verify-phase-62-1-reviewed-automation-catalog-contract.sh`
`bash scripts/verify-phase-62-2-action-policy-registry.sh`
`bash scripts/verify-phase-62-3-per-action-reconciliation-contract.sh`
`bash scripts/verify-phase-62-4-shuffle-workflow-mapping.sh`
`bash scripts/verify-phase-62-5-manual-fallback-contract.sh`
`bash scripts/verify-phase-62-6-automation-simulator-contract.sh`
`bash scripts/verify-phase-62-8-closeout-evaluation.sh`
`bash scripts/test-verify-phase-62-8-closeout-evaluation.sh`
`bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh`
`bash scripts/verify-publishable-path-hygiene.sh`
`python3 -m unittest control-plane.tests.test_phase62_action_policy_registry`
`npm run test --workspace @aegisops/operator-ui -- OperatorRoutes.test.tsx`
`npm run typecheck --workspace @aegisops/operator-ui`
`node <codex-supervisor-root>/dist/index.js issue-lint 1314 --config <supervisor-config-path>`
`node <codex-supervisor-root>/dist/index.js issue-lint 1315 --config <supervisor-config-path>`
`node <codex-supervisor-root>/dist/index.js issue-lint 1316 --config <supervisor-config-path>`
`node <codex-supervisor-root>/dist/index.js issue-lint 1317 --config <supervisor-config-path>`
`node <codex-supervisor-root>/dist/index.js issue-lint 1318 --config <supervisor-config-path>`
`node <codex-supervisor-root>/dist/index.js issue-lint 1319 --config <supervisor-config-path>`
`node <codex-supervisor-root>/dist/index.js issue-lint 1320 --config <supervisor-config-path>`
`node <codex-supervisor-root>/dist/index.js issue-lint 1321 --config <supervisor-config-path>`
`node <codex-supervisor-root>/dist/index.js issue-lint 1322 --config <supervisor-config-path>`
Each command should report `execution_ready=yes`, `missing_required=none`, `metadata_errors=none`, and no blocking high-risk ambiguity before Phase 62 is considered fully closed.
Phase 62 does not implement Phase 63 evidence expansion, Phase 66 RC proof, Beta readiness, RC readiness, GA readiness, self-service commercial readiness, or commercial replacement readiness.
Phase 63 can consume Phase 62 automation evidence as subordinate SOAR-breadth input only.
Phase 66 can consume Phase 62 as one RC evidence input for minimum SOAR replacement breadth.
Phase 62 closeout is release and planning evidence only.
EOF_PHRASE

for phrase in "${required_phrases[@]}"; do
  require_phrase "${absolute_doc_path}" "${phrase}" "required Phase 62 closeout term in ${doc_path}"
done

path_hygiene_text() {
  local file="$1"

  tr '[:upper:]' '[:lower:]' < "${file}" | sed 's#\\/#/#g'
}

absolute_path_boundary='(^|[[:space:](){}<>;,!?`"'\''"])'
generic_absolute_path_boundary='(^|[[:space:](){}<;,!?`"'\''=])'
macos_home_pattern="/""users/"
linux_home_pattern="/""home/"
root_home_pattern="/""root/"
macos_volume_pattern="/""volumes/"
macos_var_folders_pattern="/""var/folders/"
macos_private_var_folders_pattern="/""private/var/folders/"
temporary_path_pattern="/""tmp/"
private_temporary_path_pattern="/""private/tmp/"
windows_backslash_home_pattern='[a-z]:\\+users\\+'
windows_slash_home_pattern='[a-z]:/'"users"'/'
windows_subsystem_home_pattern="/""mnt/"'[a-z]/'"users/"
unix_local_path_pattern="(${macos_home_pattern}|${linux_home_pattern}|${root_home_pattern}|${macos_volume_pattern}|${macos_var_folders_pattern}|${macos_private_var_folders_pattern}|${temporary_path_pattern}|${private_temporary_path_pattern}|${windows_subsystem_home_pattern})"
local_path_pattern="(${unix_local_path_pattern}|${windows_backslash_home_pattern}|${windows_slash_home_pattern})"
local_path_with_tail="${local_path_pattern}[^[:space:]]*"
file_uri_local_path_pattern="file:(//localhost)?/*${local_path_with_tail}"
generic_unix_absolute_path_pattern="${generic_absolute_path_boundary}/[[:alnum:]_.-]+/[^[:space:]]*"
absolute_path_pattern="(${absolute_path_boundary}${local_path_with_tail}|${file_uri_local_path_pattern})"
assignment_path_boundary='(^|[[:space:](){}<>;,!`"'\''"])'
assignment_prefixed_absolute_path_pattern="${assignment_path_boundary}[^[:space:]/:=?&]+[:=]${local_path_with_tail}"
if path_hygiene_text "${absolute_doc_path}" | grep -Eq -- "${absolute_path_pattern}" || \
   path_hygiene_text "${readme_path}" | grep -Eq -- "${absolute_path_pattern}" || \
   path_hygiene_text "${absolute_doc_path}" | grep -Eq -- "${generic_unix_absolute_path_pattern}" || \
   path_hygiene_text "${readme_path}" | grep -Eq -- "${generic_unix_absolute_path_pattern}" || \
   path_hygiene_text "${absolute_doc_path}" | grep -Eq -- "${assignment_prefixed_absolute_path_pattern}" || \
   path_hygiene_text "${readme_path}" | grep -Eq -- "${assignment_prefixed_absolute_path_pattern}"; then
  echo "Forbidden Phase 62 closeout evaluation: workstation-local absolute path detected" >&2
  exit 1
fi

allowed_non_claim_line="This closeout does not claim Phase 63 evidence expansion is complete, Phase 66 RC proof is complete, AegisOps is Beta, RC, GA, self-service commercially ready, or a commercial replacement for every SIEM/SOAR capability."
allowed_non_claim_line_lower="$(printf '%s' "${allowed_non_claim_line}" | tr '[:upper:]' '[:lower:]')"
required_rejection_line="Phase 62 must reject missing child evidence, missing verifier output, missing issue-lint summary, downstream workflow truth claims, simulator production truth claims, Controlled Write or Hard Write default enablement claims, broad SOAR marketplace claims, Phase 63 evidence expansion claims, Phase 66 RC proof claims, Beta/RC/GA/commercial-readiness claims, production secrets, and workstation-local paths."
required_rejection_line_lower="$(printf '%s' "${required_rejection_line}" | tr '[:upper:]' '[:lower:]')"

forbidden_claims=(
  "phase 63 evidence expansion is complete"
  "phase 66 rc proof is complete"
  "aegisops is beta"
  "aegisops is rc"
  "aegisops is ga"
  "aegisops is self-service commercially ready"
  "aegisops is a commercial replacement for every siem/soar capability"
  "phase 62 proves rc readiness"
  "phase 62 proves ga readiness"
  "phase 62 proves commercial replacement readiness"
  "downstream workflow state is aegisops truth"
  "shuffle workflow status is aegisops truth"
  "simulator output is production truth"
  "simulator output is authoritative truth"
  "ticket state closes aegisops cases"
  "ui cache approves actions"
  "browser state executes actions"
  "controlled write is default enabled"
  "controlled write default enablement is complete"
  "hard write is default enabled"
  "hard write default enablement is complete"
  "broad soar marketplace is complete"
  "phase 63 evidence expansion is implemented"
  "phase 66 rc proof is implemented"
  "production secrets are accepted"
  "production secrets are allowed"
  "production secrets are valid"
  "phase 62 accepts production secrets"
  "production secret evidence is accepted"
  "production secret evidence is allowed"
  "production secret evidence is valid"
  "production-secret evidence is accepted"
  "production-secret evidence is allowed"
  "production-secret evidence is valid"
  "phase 62 accepts production secret evidence"
  "phase 62 accepts production-secret evidence"
)

forbidden_claim_text() {
  tr '[:upper:]' '[:lower:]' < "${absolute_doc_path}" | \
    grep -Fxv -- "${allowed_non_claim_line_lower}" | \
    grep -Fxv -- "${required_rejection_line_lower}"
}

for forbidden in "${forbidden_claims[@]}"; do
  if forbidden_claim_text | grep -Fq -e "${forbidden}"; then
    echo "Forbidden Phase 62 closeout evaluation claim: ${forbidden}" >&2
    exit 1
  fi
done

if awk -v allowed_non_claim_line="${allowed_non_claim_line_lower}" \
  -v required_rejection_line="${required_rejection_line_lower}" '
  {
    line = tolower($0)
    if (line == allowed_non_claim_line || line == required_rejection_line) {
      next
    }
    negative_context = line ~ /(must reject|must fail|fail closed|fails validation|invalid|must not|cannot|not satisfy|rejects|rejecting|rejected|not valid|does not|do not|is not|not yet|pre-ga|excluded|redacted|forbidden|blocked|without|context only|no[[:space:]])/
    positive_after_separator = line ~ /:[[:space:]]*(phase 62|aegisops|controlled write|hard write|production|prod|live|broad soar|phase 6[36]|downstream workflow|shuffle workflow|simulator output|ticket state|ui cache|browser state)/
    if (negative_context) {
      if (!positive_after_separator) {
        next
      }
    }
    if (line ~ /(^|[^[:alnum:]_])aegisops[[:space:]]+is[[:space:]]+(beta|rc|ga|release candidate|generally available|self-service commercially ready|commercially ready)([^[:alnum:]_]|$)/) {
      found_kind = "release-readiness overclaim"
    }
    if (line ~ /(^|[^[:alnum:]_])aegisops[[:space:]]+is[[:space:]]+generally[[:space:]]+available[[:space:]]*(\(|$)/) {
      found_kind = "release-readiness overclaim"
    }
    if (line ~ /(^|[^[:alnum:]_])aegisops[[:space:]]+(reached|reaches|achieved|achieves|entered|enters|shipped|ships)[[:space:]]+(beta|rc|ga|release candidate|general availability|generally available|self-service commercial readiness|self-service commercially ready|commercial readiness|commercially ready)([^[:alnum:]_]|$)/) {
      found_kind = "release-readiness overclaim"
    }
    if (line ~ /(^|[^[:alnum:]_])aegisops[[:space:]]+(has|have|had)[[:space:]]+(reached|achieved|entered|shipped)[[:space:]]+(beta|rc|ga|release candidate|general availability|generally available|self-service commercial readiness|self-service commercially ready|commercial readiness|commercially ready)([^[:alnum:]_]|$)/) {
      found_kind = "release-readiness overclaim"
    }
    if (line ~ /(^|[^[:alnum:]_])phase 6[36][[:space:]]+(evidence expansion|rc proof)([^.]*[[:space:]])?(is[[:space:]]+)?(fully[[:space:]]+)?(complete|ready|verified|accepted|done|implemented|available|supported|shipped|released)([^[:alnum:]_]|$)/) {
      found_kind = "release-readiness overclaim"
    }
    if (line ~ /(^|[^[:alnum:]_])broad[[:space:]]+soar[[:space:]]+marketplace([^.]*[[:space:]])?(is|are|becomes|became)?([^.]*[[:space:]])?(complete|ready|verified|accepted|done|implemented|available|supported|covered|coverage|shipped|released)([^[:alnum:]_]|$)/) {
      found_kind = "broad SOAR marketplace overclaim"
    }
    if (line ~ /(^|[^[:alnum:]_])phase 62([^.]*[[:space:]])?(proves|ships|includes|validates)[[:space:]]+(rc readiness|ga readiness|commercial replacement readiness)([^[:alnum:]_]|$)/) {
      found_kind = "release-readiness overclaim"
    }
    if (line ~ /(^|[^[:alnum:]_])(controlled write|hard write)([^.]*[[:space:]])?(is|are|becomes|became|defaults?|default actions?|action defaults?|default family|default families)([^.]*[[:space:]])?(enabled|available|active|supported|complete|implemented)([^[:alnum:]_]|$)/) {
      found_kind = "write-default overclaim"
    }
    if (line ~ /(^|[^[:alnum:]_])(default|defaults?|default actions?|action defaults?|default family|default families)([^.]*[[:space:]])?(controlled write|hard write)([^.]*[[:space:]])?(is|are|becomes|became)?([^.]*[[:space:]])?(enabled|available|active|supported|complete|implemented)([^[:alnum:]_]|$)/) {
      found_kind = "write-default overclaim"
    }
    if (line ~ /(^|[^[:alnum:]_])phase 62([^.]*[[:space:]])?(is|are|becomes|became|reached|reaches|achieved|achieves|proves|ships|includes|validates|establishes|satisfies|confirms|certifies)([^.]*[[:space:]])?(beta|rc|ga|release candidate|general availability|generally available|release|commercial|replacement|commercial replacement|self-service commercial)([^.]*[[:space:]])?(ready|readiness|complete|accepted|verified|proven)([^[:alnum:]_]|$)/) {
      found_kind = "release-readiness overclaim"
    }
    if (line ~ /(^|[^[:alnum:]_])phase 62([^.]*[[:space:]])?(has|have|had)[[:space:]]+(become|reached|achieved|entered|shipped|proven)([^.]*[[:space:]])?(beta|rc|ga|release candidate|general availability|generally available|release|commercial|replacement|commercial replacement|self-service commercial)([^.]*[[:space:]])?(ready|readiness|complete|accepted|verified|proven)([^[:alnum:]_]|$)/) {
      found_kind = "release-readiness overclaim"
    }
    if (line ~ /(^|[^[:alnum:]_])phase 62([^.]*[[:space:]])?(readiness|replacement readiness)([^.]*[[:space:]])?(is|are|becomes|became)?([^.]*[[:space:]])?(accepted|complete|ready|verified|proven)([^[:alnum:]_]|$)/) {
      found_kind = "release-readiness overclaim"
    }
    if (line ~ /(^|[^[:alnum:]_])production[- ]secret(s)?([^.]*[[:space:]])?(evidence|material|references?|values?)?([^.]*[[:space:]])?(is|are|becomes|became)?([^.]*[[:space:]])?(accepted|acceptable|allowed|valid|usable|trusted|sufficient)([^[:alnum:]_]|$)/) {
      found_kind = "production-secret overclaim"
    }
    if (line ~ /(^|[^[:alnum:]_])(production|prod|live)[- ]?secrets?[[:space:]]+(are|is|count as|counts as|may be|can be|remain|stays|accepted as|treated as|allowed as)[[:space:]]+([^.]*[^[:alnum:]_])?(valid|trusted|accepted|allowed|ready|verified|sufficient)([^[:alnum:]_]|$)/) {
      found_kind = "production-secret overclaim"
    }
    if (line ~ /(^|[^[:alnum:]_])(production|prod|live)[- ]?secrets?[[:space:]]+(are|is|may be|can be|could be|will be|should be|must be)[[:space:]]+used([[:space:]]+(for|as|in)[^.]*|[^[:alnum:]_]|$)/) {
      found_kind = "production-secret overclaim"
    }
    if (line ~ /(^|[^[:alnum:]_])phase 62([^.]*[[:space:]])?(accepts|allows|trusts|validates|proves|ships|includes|uses)([^.]*[[:space:]])?production[- ]secret(s)?([^[:alnum:]_]|$)/) {
      found_kind = "production-secret overclaim"
    }
    if (line ~ /(^|[^[:alnum:]_])(downstream workflow|shuffle workflow|workflow|simulator output|ticket state|ui cache|browser state)([[:space:]]+(state|status|output|cache))?([^.]*[[:space:]])?(is|are|becomes|became|counts as|serves as|acts as|represents)?([^.]*[[:space:]])?(aegisops|production|authoritative|approval|execution|reconciliation|case|workflow)?[[:space:]]*(truth|authority|authoritative|source of truth)([^[:alnum:]_]|$)/) {
      found_kind = "subordinate-surface authority overclaim"
    }
    if (line ~ /(^|[^[:alnum:]_])(ui cache|browser state|ticket state|simulator output|downstream workflow|shuffle workflow)([[:space:]]+(state|status|output|cache))?([^.]*[[:space:]])?(approves|authorizes|executes|reconciles|closes|gates|validates)([^[:alnum:]_]|$|[[:space:]])/) {
      found_kind = "subordinate-surface authority overclaim"
    }
  }
  END {
    if (found_kind != "") {
      print "Forbidden Phase 62 closeout evaluation claim: " found_kind > "/dev/stderr"
      exit 0
    }
    exit 1
  }
' "${absolute_doc_path}"; then
  exit 1
fi

echo "Phase 62 closeout evaluation verifier passes."
