import { beforeEach, describe, expect, it } from "vitest";
import {
  getOperatorQuerySnapshot,
  loadOperatorQuery,
  resetOperatorQueryCacheForTests,
} from "./operatorQueryCache";

function createDeferred<T>() {
  let rejectPromise: (error: unknown) => void = () => {};
  let resolvePromise: (value: T) => void = () => {};
  const promise = new Promise<T>((resolve, reject) => {
    resolvePromise = resolve;
    rejectPromise = reject;
  });

  return {
    promise,
    reject(error: unknown) {
      rejectPromise(error);
    },
    resolve(value: T) {
      resolvePromise(value);
    },
  };
}

describe("operatorQueryCache", () => {
  beforeEach(() => {
    resetOperatorQueryCacheForTests();
  });

  it("keeps the latest forced reread result authoritative when an older request resolves later", async () => {
    const key = "alerts/detail/alert-123";
    const olderRequest = createDeferred<{ id: string; source: string }>();
    const newerRequest = createDeferred<{ id: string; source: string }>();

    const olderPromise = loadOperatorQuery({
      key,
      queryFn: () => olderRequest.promise,
    });

    const newerPromise = loadOperatorQuery({
      force: true,
      key,
      queryFn: () => newerRequest.promise,
    });

    newerRequest.resolve({ id: "alert-123", source: "authoritative-reread" });
    await expect(newerPromise).resolves.toEqual({
      id: "alert-123",
      source: "authoritative-reread",
    });

    olderRequest.resolve({ id: "alert-123", source: "stale-initial-read" });
    await expect(olderPromise).resolves.toEqual({
      id: "alert-123",
      source: "stale-initial-read",
    });

    expect(getOperatorQuerySnapshot<{ id: string; source: string }>(key)).toEqual({
      data: { id: "alert-123", source: "authoritative-reread" },
      error: null,
      loading: false,
      refreshing: false,
    });
  });

  it("ignores stale forced-reread predecessors that fail after a newer response succeeds", async () => {
    const key = "alerts/detail/alert-456";
    const olderRequest = createDeferred<{ id: string; source: string }>();
    const newerRequest = createDeferred<{ id: string; source: string }>();

    const olderPromise = loadOperatorQuery({
      key,
      queryFn: () => olderRequest.promise,
    });

    const newerPromise = loadOperatorQuery({
      force: true,
      key,
      queryFn: () => newerRequest.promise,
    });

    newerRequest.resolve({ id: "alert-456", source: "authoritative-reread" });
    await expect(newerPromise).resolves.toEqual({
      id: "alert-456",
      source: "authoritative-reread",
    });

    olderRequest.reject(new Error("stale request failed"));
    await expect(olderPromise).rejects.toThrow("stale request failed");

    expect(getOperatorQuerySnapshot<{ id: string; source: string }>(key)).toEqual({
      data: { id: "alert-456", source: "authoritative-reread" },
      error: null,
      loading: false,
      refreshing: false,
    });
  });
});
