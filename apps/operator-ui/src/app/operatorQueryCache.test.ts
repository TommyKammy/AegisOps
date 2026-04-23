import { renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  getOperatorQuerySnapshot,
  loadOperatorQuery,
  resetOperatorQueryCacheForTests,
  useOperatorQueryLoader,
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

  it("retains the last successful data when a forced reread fails", async () => {
    const key = "alerts/detail/alert-789";
    const initialData = { id: "alert-789", source: "cached-success" };
    const forcedRequest = createDeferred<typeof initialData>();

    await expect(
      loadOperatorQuery({
        key,
        queryFn: async () => initialData,
      }),
    ).resolves.toEqual(initialData);

    const forcedPromise = loadOperatorQuery({
      force: true,
      key,
      queryFn: () => forcedRequest.promise,
    });

    expect(getOperatorQuerySnapshot<typeof initialData>(key)).toEqual({
      data: null,
      error: null,
      loading: true,
      refreshing: false,
    });

    forcedRequest.reject(new Error("authoritative reread failed"));
    await expect(forcedPromise).resolves.toEqual(initialData);

    expect(getOperatorQuerySnapshot<typeof initialData>(key)).toEqual({
      data: initialData,
      error: expect.objectContaining({
        message: "authoritative reread failed",
      }),
      loading: false,
      refreshing: false,
    });
  });

  it("drops stale data when retainStaleOnError is disabled", async () => {
    const key = "alerts/detail/alert-999";
    const initialData = { id: "alert-999", source: "cached-success" };
    const forcedRequest = createDeferred<typeof initialData>();

    await expect(
      loadOperatorQuery({
        key,
        queryFn: async () => initialData,
      }),
    ).resolves.toEqual(initialData);

    const forcedPromise = loadOperatorQuery({
      force: true,
      key,
      queryFn: () => forcedRequest.promise,
      retainStaleOnError: false,
    });

    forcedRequest.reject(new Error("authoritative reread failed"));
    await expect(forcedPromise).rejects.toThrow("authoritative reread failed");

    expect(getOperatorQuerySnapshot<typeof initialData>(key)).toEqual({
      data: null,
      error: expect.objectContaining({
        message: "authoritative reread failed",
      }),
      loading: false,
      refreshing: false,
    });
  });

  it("skips mount rereads when cached data exists and refetchOnMount is disabled", async () => {
    const key = "alerts/detail/alert-skip";
    const cachedData = { id: "alert-skip", source: "cached-success" };
    const queryFn = vi.fn().mockResolvedValue({
      id: "alert-skip",
      source: "unexpected-reread",
    });

    await expect(
      loadOperatorQuery({
        key,
        queryFn: async () => cachedData,
      }),
    ).resolves.toEqual(cachedData);

    renderHook(() =>
      useOperatorQueryLoader({
        key,
        policy: {
          refetchOnMount: false,
          retainStaleOnError: true,
        },
        queryFn,
      }),
    );

    expect(queryFn).not.toHaveBeenCalled();
    expect(getOperatorQuerySnapshot<typeof cachedData>(key)).toEqual({
      data: cachedData,
      error: null,
      loading: false,
      refreshing: false,
    });
  });

  it("keeps explicit refresh tokens authoritative even when refetchOnMount is disabled", async () => {
    const key = "alerts/detail/alert-refresh";
    const cachedData = { id: "alert-refresh", source: "cached-success" };
    const refreshedData = { id: "alert-refresh", source: "authoritative-reread" };
    const queryFn = vi.fn().mockResolvedValue(refreshedData);

    await expect(
      loadOperatorQuery({
        key,
        queryFn: async () => cachedData,
      }),
    ).resolves.toEqual(cachedData);

    const { rerender } = renderHook(
      ({ refreshToken }: { refreshToken?: number }) =>
        useOperatorQueryLoader({
          force: false,
          key,
          policy: {
            refetchOnMount: false,
            retainStaleOnError: true,
          },
          queryFn,
          refreshToken,
        }),
      { initialProps: {} as { refreshToken?: number } },
    );

    expect(queryFn).not.toHaveBeenCalled();
    rerender({ refreshToken: 1 });

    await waitFor(() => {
      expect(queryFn).toHaveBeenCalledTimes(1);
    });

    await waitFor(() => {
      expect(getOperatorQuerySnapshot<typeof refreshedData>(key)).toEqual({
        data: refreshedData,
        error: null,
        loading: false,
        refreshing: false,
      });
    });
  });
});
