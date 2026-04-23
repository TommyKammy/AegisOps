import { useNavigate } from "react-router-dom";
import { vi } from "vitest";

export function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    headers: {
      "Content-Type": "application/json",
    },
    status,
  });
}

export function createOptionalExtensionPayload(
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

export function createReadinessResponse(
  optionalExtensionsOverrides?: Partial<Record<"assistant" | "endpoint_evidence" | "network_evidence" | "ml_shadow", unknown>>,
) {
  return {
    metrics: {
      optional_extensions: createOptionalExtensionPayload(optionalExtensionsOverrides),
    },
    status: "ready",
  };
}

export function createAuthorizedFetch(
  handlers: Record<string, unknown>,
  sessionOverride?: {
    identity: string;
    provider: string;
    roles: string[];
    subject: string;
  },
) {
  return vi.fn<typeof fetch>().mockImplementation((input) => {
    const url = String(input);

    if (url.startsWith("/api/operator/session")) {
      return Promise.resolve(
        jsonResponse(
          sessionOverride ?? {
            identity: "analyst@example.com",
            provider: "authentik",
            roles: ["Analyst"],
            subject: "operator-7",
          },
        ),
      );
    }

    const match = Object.entries(handlers).find(([prefix]) => url.startsWith(prefix));
    if (match) {
      return Promise.resolve(jsonResponse(match[1]));
    }

    if (url.startsWith("/diagnostics/readiness")) {
      return Promise.resolve(jsonResponse(createReadinessResponse()));
    }

    return Promise.reject(new Error(`Unexpected fetch: ${url}`));
  });
}

export function createDeferredResponse() {
  let rejectPromise: (error: unknown) => void = () => {};
  let resolvePromise: (response: Response) => void = () => {};
  const promise = new Promise<Response>((resolve, reject) => {
    resolvePromise = resolve;
    rejectPromise = reject;
  });

  return {
    promise,
    reject(error: unknown) {
      rejectPromise(error);
    },
    resolve(body: unknown, status = 200) {
      resolvePromise(jsonResponse(body, status));
    },
  };
}

export function TestRouteNavigator() {
  const navigate = useNavigate();

  return (
    <>
      <button onClick={() => navigate("/operator/readiness")} type="button">
        Go to readiness
      </button>
      <button onClick={() => navigate("/operator/alerts/alert-123")} type="button">
        Go to alert detail
      </button>
    </>
  );
}
