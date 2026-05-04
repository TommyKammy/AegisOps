import { describe, expect, it } from "vitest";
import { buildOptionalExtensionDefinitionsFromPayload } from "./optionalExtensionVisibility";

function createOptionalExtensionPayload(
  overrides: Partial<Record<"assistant" | "endpoint_evidence" | "network_evidence" | "ml_shadow", unknown>> = {},
) {
  return {
    overall_state: "ready",
    tracked_extensions: 4,
    extensions: {
      assistant: {
        authority_mode: "advisory_only",
        availability: "available",
        enablement: "enabled",
        mainline_dependency: "non_blocking",
        readiness: "ready",
        reason: "bounded_reviewed_summary_provider_available",
      },
      endpoint_evidence: {
        authority_mode: "augmenting_evidence",
        availability: "unavailable",
        enablement: "disabled_by_default",
        mainline_dependency: "non_blocking",
        readiness: "not_applicable",
        reason: "isolated_executor_runtime_not_configured",
      },
      network_evidence: {
        authority_mode: "augmenting_evidence",
        availability: "unavailable",
        enablement: "disabled_by_default",
        mainline_dependency: "non_blocking",
        readiness: "not_applicable",
        reason: "reviewed_network_evidence_extension_not_activated",
      },
      ml_shadow: {
        authority_mode: "shadow_only",
        availability: "unavailable",
        enablement: "disabled_by_default",
        mainline_dependency: "non_blocking",
        readiness: "not_applicable",
        reason: "reviewed_ml_shadow_extension_not_activated",
      },
      ...overrides,
    },
  };
}

describe("optionalExtensionVisibility", () => {
  it("keeps disabled-by-default posture distinct from unavailable", () => {
    const definitions = buildOptionalExtensionDefinitionsFromPayload(
      createOptionalExtensionPayload(),
    );

    expect(definitions).toEqual([
      expect.objectContaining({
        status: "enabled",
        title: "Assistant",
      }),
      expect.objectContaining({
        status: "disabled_by_default",
        title: "Endpoint evidence",
      }),
      expect.objectContaining({
        status: "disabled_by_default",
        title: "Optional network evidence",
      }),
      expect.objectContaining({
        status: "disabled_by_default",
        title: "ML shadow",
      }),
    ]);
  });

  it("fails closed when enablement says enabled but availability is missing", () => {
    const definitions = buildOptionalExtensionDefinitionsFromPayload(
      createOptionalExtensionPayload({
        endpoint_evidence: {
          authority_mode: "augmenting_evidence",
          enablement: "enabled",
          mainline_dependency: "non_blocking",
          readiness: "ready",
          reason: "reviewed_endpoint_extension_binding_missing",
        },
      }),
    );

    expect(definitions).toContainEqual(
      expect.objectContaining({
        status: "unavailable",
        title: "Endpoint evidence",
      }),
    );
  });

  it("keeps degraded posture primary over other optional signals", () => {
    const definitions = buildOptionalExtensionDefinitionsFromPayload(
      createOptionalExtensionPayload({
        ml_shadow: {
          authority_mode: "shadow_only",
          availability: "available",
          enablement: "enabled",
          mainline_dependency: "non_blocking",
          readiness: "degraded",
          reason: "reviewed_ml_shadow_extension_provider_lagging",
        },
      }),
    );

    expect(definitions).toContainEqual(
      expect.objectContaining({
        status: "degraded",
        title: "ML shadow",
      }),
    );
  });

  it("keeps admin-disabled assistant posture distinct from unavailable", () => {
    const definitions = buildOptionalExtensionDefinitionsFromPayload(
      createOptionalExtensionPayload({
        assistant: {
          authority_mode: "advisory_only",
          availability: "unavailable",
          enablement: "disabled",
          mainline_dependency: "non_blocking",
          readiness: "not_applicable",
          reason: "ai_advisory_disabled_by_admin",
        },
      }),
    );

    expect(definitions).toContainEqual(
      expect.objectContaining({
        description: expect.stringContaining("platform-admin AI posture disables"),
        status: "disabled",
        title: "Assistant",
      }),
    );
  });
});
