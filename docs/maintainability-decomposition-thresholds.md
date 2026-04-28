# AegisOps Maintainability Decomposition Thresholds and Backlog Triggers

This document converts the recent `service.py` refactor experience into a lightweight rule for when AegisOps should open another maintainability backlog instead of waiting for responsibility concentration to become obvious only in hindsight.

It supplements `docs/architecture.md`, `docs/control-plane-service-internal-boundaries.md`, `docs/templates/issue-template.md`, and `docs/templates/pull-request-review-checklist.md`.

This guidance is maintainability policy only. It does not approve new runtime behavior, new product scope, or authority-boundary changes.

## 1. Purpose

AegisOps now has enough recent refactor history to define a repo-owned decomposition threshold instead of relying on intuition or line-count anxiety alone.

The rule needs to stay lightweight, but it must still help future roadmap planning and PR review answer one concrete question consistently:

- should we continue extending the hotspot in place for one more narrow issue; or
- should we open another maintainability refactor backlog before the next expansion lands?

Line count alone is not enough for that call.
In practical review terms, line count alone is not enough because the real pressure comes from responsibility concentration and boundary mixing.

AegisOps hotspots become risky because one module starts carrying too many reviewed responsibilities, too many authority-bearing paths, and too much coupled regression surface at the same time.

## 2. Recent Refactor Signals

The current rule is grounded in three recent repository checkpoints.

### 2.1 `#592`: backlog trigger became obvious after Phase 28 growth

`#592` opened the post-Phase 28 maintainability refactor backlog when the repository still worked functionally, but the change surface had become too concentrated in a small set of files.

The Epic called out:

- `control-plane/aegisops_control_plane/service.py` as the dominant hotspot;
- mixed ownership of endpoint evidence, subordinate MISP attachment, action review, case promotion, assistant workflow, and reconciliation entrypoints inside one class;
- large test modules whose size and churn made focused review harder; and
- CI maintainability pressure from duplicated validation structure.

The important lesson from `#592` is that backlog creation should start before runtime behavior degrades. Concentrated responsibility, test mass, and change friction are already enough.

### 2.2 `#610`: one backlog was not enough once the next concentration point was still obvious

`#610` reopened the maintainability question immediately after `#592` because the first round reduced several hotspots but still left the next concentration points obvious in the host checkout.

That Epic explicitly called out:

- `control-plane/aegisops_control_plane/service.py` as the remaining dominant orchestration hotspot;
- `control-plane/aegisops_control_plane/restore_readiness.py` as the next large boundary module; and
- operator read surfaces, detection lifecycle flows, restore/readiness logic, and assistant workflow responsibilities that still remained too concentrated.

The lesson from `#610` is that AegisOps should open another backlog when the next hotspot is already clear after the previous extraction set lands. Waiting for another feature wave to intensify it adds risk without adding clarity.

### 2.3 `#633`: hotspot extraction was still justified even after prior backlog work

`#633` then decomposed the next authority-bearing `service.py` hotspot cluster after the post-`#610` refactors still left one coherent write-path concentration inside the public facade.

That issue focused on:

- the remaining `record_case_*` family;
- manual fallback or escalation write logic;
- approval-decision handling; and
- action-policy evaluation helpers that still lived too close together inside `service.py`.

The lesson from `#633` is that a hotspot remains backlog-worthy when the remaining cluster is still authority-bearing, still cohesive enough to extract safely, and still large enough that future roadmap work would keep landing in the same file.

## 3. Signals That Count Toward a Decomposition Threshold

Future maintainability calls should evaluate the hotspot against the following signals together.

The current checklist is: responsibility count, authority-path mixing, optional-extension mixing, regression-test coupling, and operator-surface overlap.

### 3.1 Responsibility count

Responsibility count asks how many distinct reviewed concerns one file or class owns.

The signal is present when a single hotspot simultaneously owns several of the following:

- runtime or auth boundary behavior;
- operator-facing read surfaces;
- casework mutation paths;
- assistant or advisory assembly;
- action-governance or reconciliation logic;
- readiness, backup, restore, or export behavior;
- source-admission or evidence-ingest logic; or
- internal policy helpers shared across those paths.

If the same module has to be explained to reviewers as multiple named clusters, that is already pressure toward decomposition.

### 3.2 Authority-path mixing

Authority-path mixing asks whether the hotspot combines read-only shaping with authority-bearing or lifecycle-bearing mutations.

This signal is especially important in AegisOps because modules become harder to review when they mix:

- advisory assembly with approval or execution governance;
- runtime/auth checks with business workflow mutations;
- detection intake with authoritative case or reconciliation linking; or
- restore/readiness operations with current live workflow behavior.

When one file mixes several authority paths, refactors become higher-risk and later feature work becomes easier to broaden accidentally.

### 3.3 Optional-extension mixing

Optional-extension mixing asks whether reviewed optional or subordinate capabilities have accumulated inside a core orchestration hotspot instead of staying visibly subordinate.

Examples from recent history include endpoint evidence augmentation, subordinate MISP flows, assistant workflow assembly, and restore/readiness growth.

This matters because optional or subordinate slices can quietly turn one core module into the repository’s default landing zone for unrelated future work.

### 3.4 Regression-test coupling

Regression-test coupling asks whether proving one behavior now requires touching or re-reading too much unrelated coverage.

This signal is present when:

- one implementation hotspot maps to a broad, hard-to-split test mass;
- narrow refactors require coordinated edits across unrelated test families;
- one behavior change forces the reviewer to re-evaluate many older contracts in one pass; or
- the same hotspot keeps appearing in focused regression suites for otherwise different features.

Large regression surface alone is not the problem. The problem is when one hotspot keeps dragging multiple test families together.

### 3.5 Operator-surface overlap

Operator-surface overlap asks whether the hotspot owns multiple user-visible or reviewer-visible surfaces whose semantics should remain separate.

Examples include:

- queue and detail reads plus casework mutation;
- assistant context and cited advisory output plus action creation;
- health or readiness surfaces plus restore execution; or
- one file defining both public facade behavior and several separate internal boundary rules.

When operator-surface overlap grows, reviewers lose a clean boundary for reasoning about what a change is allowed to alter.

## 4. Threshold Rule

A hotspot should move to backlog creation when the repository shows all of the following:

1. One module or tightly bound file pair is still the obvious landing zone for the next roadmap slice.
2. At least three of the five signals above are clearly present.
3. One of those signals is either authority-path mixing or operator-surface overlap.
4. The remaining cluster is cohesive enough to describe as one follow-up extraction or one ordered child-issue set.
5. The extraction can preserve the public boundary and reviewed behavior instead of reopening product scope.

The backlog trigger is stronger when the hotspot is already being described in reviews as a "remaining cluster", "next hotspot", "dominant orchestration hotspot", or equivalent language. That vocabulary means the repository has already made the concentration visible.

## 5. In-Place Extension Rule

A hotspot can stay in place for the current issue only when all of the following are true:

1. The change adds one narrow behavior inside an already cohesive responsibility area.
2. The work does not introduce new authority-path mixing.
3. The work does not pull another optional or subordinate slice into the hotspot.
4. Focused regression coverage stays local to one existing test family.
5. Reviewers can still explain the boundary without inventing a new internal decomposition narrative.

If those conditions no longer hold, the safer choice is to open another maintainability refactor backlog instead of normalizing the concentration.

## 6. Practical Backlog Triggers

Open another maintainability refactor backlog when any of the following repo-specific patterns appear:

- `control-plane/aegisops_control_plane/service.py` or a successor facade is still the obvious home for the next distinct workflow slice after the last extraction backlog completed.
- `control-plane/aegisops_control_plane/restore_readiness.py` or another large boundary module starts combining operational surfaces that future issues keep revisiting together.
- a module now requires named responsibility clusters in docs or PR review just to explain why one narrow change is supposedly safe.
- the next roadmap issue would add a new concern to a hotspot that already mixes read shaping, write-path governance, and operational boundary logic.
- multiple focused regression suites now depend on the same hotspot even though the user-visible behaviors are supposed to stay separate.

These triggers are intentionally qualitative but still concrete. They are designed to catch concentration early without turning maintainability review into a formula game.

## 7. Backlog Shape Guidance

When the threshold is crossed, the preferred response is not one giant cleanup issue.

Open either:

- one Epic that sequences the next narrow child issues, as in `#592` and `#610`; or
- one single extraction issue for one clearly isolated remaining cluster, as in `#633`.

The backlog should keep the same AegisOps discipline as the earlier refactors:

- preserve the public facade where possible;
- preserve the reviewed authority model and fail-closed checks;
- keep extraction work separate from feature expansion;
- add focused regression coverage for the extracted seam; and
- describe dependency order when one extraction improves the safety of the next.

## 8. How To Use This In Planning And Review

Future roadmap planning should cite this document when deciding whether a hotspot deserves another maintainability backlog before the next expansion issue is opened.

Pull-request review should cite this document when a supposedly narrow change is actually landing on a module that already crossed the decomposition threshold.

If a reviewer can point to the threshold rule and the backlog triggers above, the repo should prefer explicit backlog creation over "one more change" reasoning.

## 9. How To Interpret Verifier Output

The maintainability hotspot verifier is `scripts/verify-maintainability-hotspots.sh`.
Its focused regression test is `scripts/test-verify-maintainability-hotspots.sh`.

The verifier is a responsibility-growth guard, not a line-count-only gate.
It reports a candidate only when a tracked control-plane Python module is both large enough to be review-heavy and carries several responsibility signals such as runtime or auth boundary handling, operator surfaces, casework mutation, assistant or advisory assembly, action or reconciliation governance, readiness or restore behavior, and source or evidence admission.

Known current candidates are recorded in `docs/maintainability-hotspot-baseline.txt`.
If the verifier reports only known baseline entries, maintainers should treat the output as a reminder that those files remain reviewed hotspots and should not absorb unrelated responsibility growth without a decomposition decision.

Baseline entries may also record Phase closeout ceilings such as `max_lines`, `max_effective_lines`, and `max_facade_methods`.
Those ceilings are not success targets; they are ADR-documented exception limits for known hotspots that remain above the long-term threshold after an accepted extraction sequence.
If a known hotspot exceeds a recorded ceiling, the verifier fails because the facade or successor hotspot has grown beyond the reviewed closeout state.
The expected response is to lower the hotspot through another decomposition issue or update the governing ADR before accepting the growth.

If the verifier fails with a new candidate, reviewers should use the threshold rule above before extending the file further.
The expected response is either a narrow justification that the current change stays inside one cohesive responsibility or a follow-up maintainability backlog that preserves public behavior while extracting the next coherent cluster.

If the verifier fails because a baseline entry is stale, update the baseline only after confirming the listed file no longer crosses the responsibility-growth threshold.
That stale-baseline failure is a cleanup prompt, not permission to redefine the threshold around a summary field or convenience projection.
