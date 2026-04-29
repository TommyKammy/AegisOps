#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/adr/0004-phase-50-maintainability-hotspot-map-and-migration-order.md"

required_headings=(
  "# ADR-0004: Phase 50 Maintainability Hotspot Map and Migration Order"
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
  "- **Related Issues**: #946, #947"
  "Phase 49.0 completed the behavior-preserving \`AegisOpsControlPlaneService\` decomposition sequence governed by ADR-0003."
  "ADR-0003 remains authoritative for the Phase 49.0 facade-preservation contract and for the closeout ceiling recorded in \`docs/maintainability-hotspot-baseline.txt\`."
  "Phase 50 is a follow-on maintainability backlog. It must lower or fence the remaining hotspots after the ADR-0003 closeout ceiling instead of treating the ceiling as permission for new responsibility growth."
  "The first Phase 50 implementation issue must not start before this ADR is merged."
  "We will run Phase 50 as ordered, behavior-preserving hotspot reduction after the ADR-0003 closeout."
  "The Phase 50 target hotspots are:"
  "- \`control-plane/aegisops_control_plane/service.py\`"
  "- restore validation"
  "- HTTP surface"
  "- assistant, detection, and operator inspection second-hotspot risk"
  "- operator-ui route tests"
  "The migration order is:"
  "1. #947 Phase 50 maintainability ADR and verifier gate"
  "2. \`service.py\` facade ceiling reduction or fencing"
  "3. restore validation boundary extraction and snapshot-consistency proof"
  "4. HTTP surface routing and auth-boundary review split"
  "5. assistant, detection, and operator inspection second-hotspot risk reduction"
  "6. operator-ui route test decomposition"
  "7. hotspot baseline refresh and Phase 50 validation closeout"
  "The child issues are not parallelizable unless a later accepted ADR or issue update explicitly changes the dependency order."
  "The Phase 50 baseline refresh may only happen after the implementation slices prove the hotspots have actually been lowered or fenced."
  "Option A is selected because it follows \`docs/maintainability-decomposition-thresholds.md\` while respecting the ADR-0003 closeout state."
  "Later Phase 50 implementation slices must preserve production behavior, public service entrypoints, runtime configuration, and authority semantics unless a separate accepted ADR and scoped issue explicitly allow a change."
  "The restore validation slice must prove snapshot-consistent reads or explicit rejection of mixed-snapshot results, and failed paths must leave no orphan record, partial durable write, or half-restored state."
  "The HTTP surface slice must preserve trusted-boundary behavior and must not trust raw forwarded headers, host, proto, tenant, user-id, or client-supplied identity hints unless a trusted proxy or boundary has authenticated and normalized them."
  "The assistant, detection, and operator inspection slice must keep advisory output, detection evidence, and inspection projections subordinate to directly linked authoritative control-plane records."
  "The operator-ui route test slice must reduce test hotspot pressure without introducing new operator capability, approval behavior, execution behavior, or routing authority."
  "This ADR does not change approval, execution, reconciliation, assistant, ticket, ML, endpoint, network, browser, optional-evidence, secrets, restore, readiness, or write-capable authority."
  "No production code extraction is approved by this ADR."
  "No commercial readiness capability is added."
  "Tickets, assistant output, ML, endpoint evidence, network evidence, browser state, receipts, optional extension status, Wazuh, Shuffle, and Zammad remain subordinate context and do not become workflow truth."
  "Run \`bash scripts/verify-phase-50-maintainability-adr.sh\`."
  "Run \`bash scripts/test-verify-phase-50-maintainability-adr.sh\`."
  "Run \`bash scripts/verify-maintainability-hotspots.sh\`."
  "Run \`node <codex-supervisor-root>/dist/index.js issue-lint 947 --config <supervisor-config-path>\`."
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Phase 50 maintainability ADR: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fq -- "${heading}" "${doc_path}"; then
    echo "Missing Phase 50 maintainability ADR heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${doc_path}"; then
    echo "Missing Phase 50 maintainability ADR statement: ${phrase}" >&2
    exit 1
  fi
done

echo "Phase 50 maintainability ADR is present and fixes hotspots, migration order, behavior preservation, authority non-goals, and validation commands."
