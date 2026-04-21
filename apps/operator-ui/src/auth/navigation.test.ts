import { describe, expect, it, vi } from "vitest";
import { createWindowLocationRedirector } from "./navigation";

describe("createWindowLocationRedirector", () => {
  it("uses location.replace semantics for auth redirects", () => {
    const location = {
      replace: vi.fn(),
    };

    createWindowLocationRedirector(location).replace("/operator/login");

    expect(location.replace).toHaveBeenCalledWith("/operator/login");
  });
});
