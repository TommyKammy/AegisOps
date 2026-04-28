#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/adr/0003-phase-49-service-decomposition-boundaries.md"

required_headings=(
  "# ADR-0003: Phase 49 Service Decomposition Boundaries and Migration Order"
  "## 1. Context"
  "## 2. Decision"
  "## 3. Decision Drivers"
  "## 4. Options Considered"
  "## 5. Rationale"
  "## 6. Consequences"
  "## 7. Implementation Impact"
  "## 8. Security Impact"
  "## 9. Rollback / Exit Strategy"
  "## 10. Validation"
  "## 11. Non-Goals"
  "## 12. Approval"
)

required_phrases=(
  "- **Status**: Accepted"
  "- **Date**: 2026-04-29"
  "- **Related Issues**: #918, #919, #920, #921, #922, #923, #924, #925"
  "AegisOpsControlPlaneService remains the public facade for Phase 49.0 behavior-preserving decomposition work."
  "The first implementation issue must not start before this ADR is merged."
  "We will preserve the existing public facade while extracting internal collaborators."
  "The target service boundaries are:"
  "- Intake and triage boundary"
  "- Case mutation and evidence linkage boundary"
  "- Advisory and AI trace lifecycle boundary"
  "- Action and reconciliation orchestration boundary"
  "- Runtime, restore, and readiness diagnostics boundary"
  "The migration order is:"
  "1. #919 ADR and verification gate"
  "2. #920 intake and triage extraction"
  "3. #921 case mutation and evidence linkage extraction"
  "4. #922 advisory and AI trace lifecycle extraction"
  "5. #923 action and reconciliation orchestration extraction"
  "6. #924 runtime, restore, and readiness diagnostics extraction"
  "7. #925 hotspot baseline refresh and validation closeout"
  "Every extraction slice must keep the facade behavior-preserving and add focused regression coverage for its boundary."
  "This ADR does not change approval, execution, reconciliation, assistant, ticket, ML, endpoint, network, browser, optional-evidence, secrets, or write-capable authority."
  "No production code extraction is approved by this ADR."
  "No commercial readiness capability is added."
  "Tickets, assistant output, ML, endpoint evidence, network evidence, browser state, receipts, and optional extension status remain subordinate context and do not become workflow truth."
  "Run \`bash scripts/verify-phase-49-service-decomposition-adr.sh\`."
  "Run \`bash scripts/test-verify-phase-49-service-decomposition-adr.sh\`."
  "Run \`node <codex-supervisor-root>/dist/index.js issue-lint 919 --config <supervisor-config-path>\`."
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Phase 49 service decomposition ADR: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fq -- "${heading}" "${doc_path}"; then
    echo "Missing Phase 49 service decomposition ADR heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${doc_path}"; then
    echo "Missing Phase 49 service decomposition ADR statement: ${phrase}" >&2
    exit 1
  fi
done

echo "Phase 49 service decomposition ADR is present and fixes boundaries, migration order, behavior preservation, and authority non-goals."
