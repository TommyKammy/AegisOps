#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/adr/0007-phase-50-10-facade-floor-and-external-evidence-guard.md"
baseline_path="${repo_root}/docs/maintainability-hotspot-baseline.txt"

required_headings=(
  "# ADR-0007: Phase 50.10 Facade Floor and External Evidence Guard Contract"
  "## 1. Context"
  "## 2. Decision"
  "## 3. Facade Floor Targets"
  "## 4. External Evidence Guard"
  "## 5. Migration Order"
  "## 6. Validation"
  "## 7. Non-Goals"
  "## 8. Approval"
)

required_phrases=(
  "- **Status**: Accepted"
  "- **Date**: 2026-04-29"
  "- **Related Issues**: #987, #988"
  "- **Depends On**: #980"
  "ADR-0003 remains authoritative for the public facade-preservation exception."
  "ADR-0004 remains authoritative for the Phase 50 ordered hotspot-reduction rule."
  "ADR-0005 remains authoritative for the Phase 50.8 residual helper migration contract and the rule that baseline refreshes require implementation evidence."
  "ADR-0006 remains authoritative for the Phase 50.9 residual facade convergence and projection hotspot guard."
  "\`docs/maintainability-decomposition-thresholds.md\` remains the governing hotspot trigger policy."
  "This ADR does not refresh the baseline because Phase 50.10 implementation evidence does not exist yet."
  "The Phase 50.10 target clusters are:"
  "- MISP and osquery helper cluster"
  "- endpoint evidence helper cluster"
  "- service facade helper cluster"
  "- internal caller rewiring cluster"
  "- closeout and hotspot-baseline guard cluster"
  "Public service entrypoints, runtime behavior, configuration shape, authority semantics, external-evidence response semantics, and durable-state side effects remain unchanged."
  "AegisOps control-plane records remain authoritative workflow truth."
  "Tickets, assistant output, ML, endpoint evidence, network evidence, browser state, receipts, optional extension status, Wazuh, Shuffle, Zammad, operator-facing summaries, badges, counters, projections, and external-evidence adapter output remain subordinate context."
  "The Phase 50.9.6 starting ceiling for \`control-plane/aegisops_control_plane/service.py\` is:"
  "- \`max_lines=3158\`"
  "- \`max_effective_lines=2853\`"
  "- \`max_facade_methods=173\`"
  "- \`phase=50.9.6\`"
  "- \`issue=#980\`"
  "The Phase 50.10 implementation target for \`control-plane/aegisops_control_plane/service.py\` is:"
  "- \`max_lines <= 2900\`"
  "- \`max_effective_lines <= 2650\`"
  "- \`max_facade_methods <= 160\`"
  "A Phase 50.10 closeout may record a lower exception only if it names the unresolved cluster, records the measured line, effective-line, and facade-method counts, and keeps the exception lower than the Phase 50.9.6 ceiling."
  "Any \`service.py\` baseline refresh before Phase 50.10 implementation evidence exists is forbidden."
  "The external-evidence split target is \`control-plane/aegisops_control_plane/external_evidence_boundary.py\`."
  "No \`external_evidence_boundary.py\` hotspot baseline may be recorded before Phase 50.10 implementation evidence exists."
  "An \`external_evidence_boundary.py\` baseline may be recorded only at Phase 50.10 closeout when all of these criteria are true:"
  "- the MISP, osquery, and endpoint evidence helpers have already been split into explicitly owned helper modules or fenced helper clusters;"
  "- the closeout records measured \`external_evidence_boundary.py\` line and effective-line counts after the split;"
  "- the closeout names the unresolved external-evidence responsibility cluster;"
  "- the recorded external-evidence ceiling is lower than the pre-Phase 50.10 measurement of \`max_lines=1083\` and \`max_effective_lines=1033\`;"
  "- the baseline entry names a Phase 50.10 closeout phase and issue;"
  "- the closeout explicitly states why another split would be riskier than accepting the temporary external-evidence hotspot."
  "If those criteria are not all true, the correct result is a follow-up decomposition issue, not a silent external-evidence hotspot exception."
  "External evidence may enrich a reviewed record only when the AegisOps record chain explicitly binds the evidence subject, source, provenance, and linked case or alert context."
  "External evidence must not infer tenant, case, alert, host, repository, account, issue, or environment linkage from names, paths, comments, nearby records, adapter output, or neighboring metadata alone."
  "The Phase 50.10 migration order is:"
  "1. MISP and osquery helper cluster"
  "2. endpoint evidence helper cluster"
  "3. service facade helper cluster"
  "4. internal caller rewiring cluster"
  "5. closeout and hotspot-baseline guard cluster"
  "MISP and osquery helpers must move before endpoint evidence helpers so subordinate enrichment and reviewed host-context attachment stay explicitly bound to AegisOps-owned records."
  "Endpoint evidence helpers must move before service facade helpers so endpoint collection and artifact admission do not widen public service authority."
  "Service facade helpers must move before internal caller rewiring so callers keep using public facade entrypoints until the reviewed internal boundary exists."
  "Internal caller rewiring must move before closeout so any \`external_evidence_boundary.py\` hotspot baseline decision is based on implementation evidence rather than a desired target."
  "Run \`bash scripts/verify-phase-50-10-facade-floor-external-evidence-contract.sh\`."
  "Run \`bash scripts/test-verify-phase-50-10-facade-floor-external-evidence-contract.sh\`."
  "Run \`bash scripts/verify-maintainability-hotspots.sh\`."
  "Run \`node <codex-supervisor-root>/dist/index.js issue-lint 988 --config <supervisor-config-path>\`."
  "No production code extraction is approved by this ADR."
  "No external-evidence module split is approved by this ADR."
  "No approval, execution, reconciliation, assistant, ticket, ML, endpoint, network, browser, optional-evidence, restore, readiness, detection, external-evidence, or operator authority behavior is changed."
  "No deployment, database, migration, credential source, external substrate, HTTP surface, CLI surface, or operator UI behavior is changed."
  "No baseline refresh is approved before Phase 50.10 implementation evidence exists."
  "No subordinate source, operator-facing projection, summary, badge, counter, recommendation, evidence snippet, reconciliation note, or external-evidence adapter output becomes authoritative workflow truth."
  "No exception may raise the Phase 50.9.6 ceiling."
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Phase 50.10 facade floor and external evidence guard contract: ${doc_path}" >&2
  exit 1
fi

if [[ ! -f "${baseline_path}" ]]; then
  echo "Missing maintainability hotspot baseline: ${baseline_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fq -- "${heading}" "${doc_path}"; then
    echo "Missing Phase 50.10 facade floor and external evidence guard contract heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${doc_path}"; then
    echo "Missing Phase 50.10 facade floor and external evidence guard contract statement: ${phrase}" >&2
    exit 1
  fi
done

starting_service_baseline_entry="control-plane/aegisops_control_plane/service.py max_lines=3158 max_effective_lines=2853 max_facade_methods=173 facade_class=AegisOpsControlPlaneService adr_exception=ADR-0003 phase=50.9.6 issue=#980"
closeout_service_baseline_entry="control-plane/aegisops_control_plane/service.py max_lines=3003 max_effective_lines=2704 max_facade_methods=167 facade_class=AegisOpsControlPlaneService adr_exception=ADR-0003 phase=50.10.6 issue=#993"
service_entry="$(grep -E '^control-plane/aegisops_control_plane/service.py[[:space:]]' "${baseline_path}" || true)"
service_entry_count="$(printf '%s\n' "${service_entry}" | sed '/^$/d' | wc -l | tr -d ' ')"
if [[ "${service_entry_count}" -eq 0 ]]; then
  echo "Phase 50.10 contract requires the accepted Phase 50.9.6 service.py hotspot baseline entry." >&2
  exit 1
fi
if [[ "${service_entry_count}" -ne 1 ]]; then
  echo "Phase 50.10 contract requires exactly one service.py hotspot baseline entry." >&2
  exit 1
fi
if [[ "${service_entry}" == "${starting_service_baseline_entry}" ]]; then
  :
elif [[ "${service_entry}" == "${closeout_service_baseline_entry}" ]]; then
  closeout_path="${repo_root}/docs/phase-50-maintainability-closeout.md"
  if [[ ! -f "${closeout_path}" ]]; then
    echo "Phase 50.10 final baseline refresh requires closeout evidence: ${closeout_path}" >&2
    exit 1
  fi
  closeout_required_phrases=(
    "Phase 50.10.6"
    "#993"
    "\`max_lines=3003\`"
    "\`max_effective_lines=2704\`"
    "\`max_facade_methods=167\`"
    "external_evidence_boundary.py lines=216"
    "external_evidence_boundary.py effective_lines=195"
    "external-evidence split does not require a baseline entry"
    "silent re-growth"
    "another decomposition decision"
  )
  for phrase in "${closeout_required_phrases[@]}"; do
    if ! grep -Fq -- "${phrase}" "${closeout_path}"; then
      echo "Phase 50.10 final closeout evidence is missing: ${phrase}" >&2
      exit 1
    fi
  done
else
  echo "Phase 50.10 contract forbids refreshing the service.py baseline before implementation evidence exists." >&2
  exit 1
fi

external_evidence_entry="$(grep -E '^control-plane/aegisops_control_plane/external_evidence_boundary.py[[:space:]]' "${baseline_path}" || true)"
external_evidence_entry_count="$(printf '%s\n' "${external_evidence_entry}" | sed '/^$/d' | wc -l | tr -d ' ')"
if [[ "${external_evidence_entry_count}" -ne 0 ]]; then
  echo "Phase 50.10 contract forbids an external_evidence_boundary.py hotspot baseline before implementation evidence exists." >&2
  exit 1
fi

echo "Phase 50.10 facade floor and external evidence guard contract fixes target ceilings, external-evidence guard criteria, migration order, non-goals, and validation commands."
