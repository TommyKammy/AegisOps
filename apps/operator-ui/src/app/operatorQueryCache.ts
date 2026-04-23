import { useEffect, useSyncExternalStore } from "react";

interface QueryPolicy {
  refetchOnMount: boolean;
  retainStaleOnError: boolean;
}

interface QueryState<T> {
  data: T | null;
  error: Error | null;
  loading: boolean;
  refreshing: boolean;
}

interface CacheEntry<T> {
  inFlight: Promise<T> | null;
  listeners: Set<() => void>;
  requestVersion: number;
  state: QueryState<T>;
}

interface LoadQueryArgs<T> {
  force?: boolean;
  key: string;
  queryFn: () => Promise<T>;
  retainStaleOnError?: boolean;
}

const DEFAULT_QUERY_STATE = {
  data: null,
  error: null,
  loading: true,
  refreshing: false,
};

const queryCache = new Map<string, CacheEntry<unknown>>();

function getOrCreateEntry<T>(key: string): CacheEntry<T> {
  const existing = queryCache.get(key) as CacheEntry<T> | undefined;
  if (existing) {
    return existing;
  }

  const created: CacheEntry<T> = {
    inFlight: null,
    listeners: new Set(),
    requestVersion: 0,
    state: DEFAULT_QUERY_STATE,
  };
  queryCache.set(key, created as CacheEntry<unknown>);
  return created;
}

function notifyEntry(entry: CacheEntry<unknown>) {
  entry.listeners.forEach((listener) => listener());
}

function shouldRetainDataOnError(error: unknown) {
  if (!(error instanceof Error)) {
    return false;
  }

  return !(
    error.name === "OperatorDataProviderAuthorizationError" ||
    error.name === "OperatorDataProviderContractError"
  );
}

export function buildOperatorQueryKey(parts: unknown[]): string {
  return JSON.stringify(parts);
}

export function subscribeToOperatorQuery(
  key: string,
  listener: () => void,
) {
  const entry = getOrCreateEntry(key);
  entry.listeners.add(listener);

  return () => {
    entry.listeners.delete(listener);
  };
}

export function getOperatorQuerySnapshot<T>(key: string): QueryState<T> {
  return getOrCreateEntry<T>(key).state;
}

export async function loadOperatorQuery<T>({
  force = false,
  key,
  queryFn,
  retainStaleOnError = true,
}: LoadQueryArgs<T>): Promise<T> {
  const entry = getOrCreateEntry<T>(key);
  const previousData = entry.state.data;
  const hasData = previousData !== null;

  if (!force && entry.inFlight !== null) {
    return entry.inFlight;
  }

  const requestVersion = entry.requestVersion + 1;
  entry.requestVersion = requestVersion;

  if (!force && hasData) {
    entry.state = {
      ...entry.state,
      error: null,
      loading: false,
      refreshing: true,
    };
    notifyEntry(entry);
  } else {
    entry.state = {
      data: null,
      error: null,
      loading: true,
      refreshing: false,
    };
    notifyEntry(entry);
  }

  const request = queryFn()
    .then((data) => {
      if (entry.requestVersion !== requestVersion) {
        return data;
      }

      entry.state = {
        data,
        error: null,
        loading: false,
        refreshing: false,
      };
      notifyEntry(entry);
      return data;
    })
    .catch((error: unknown) => {
      const normalizedError =
        error instanceof Error
          ? error
          : new Error("Unknown operator query failure.");

      if (entry.requestVersion !== requestVersion) {
        throw normalizedError;
      }

      if (
        previousData !== null &&
        retainStaleOnError &&
        shouldRetainDataOnError(normalizedError)
      ) {
        entry.state = {
          data: previousData,
          error: normalizedError,
          loading: false,
          refreshing: false,
        };
        notifyEntry(entry);
        return previousData;
      }

      entry.state = {
        data: null,
        error: normalizedError,
        loading: false,
        refreshing: false,
      };
      notifyEntry(entry);
      throw normalizedError;
    })
    .finally(() => {
      if (entry.requestVersion === requestVersion) {
        entry.inFlight = null;
      }
    });

  entry.inFlight = request;
  return request;
}

export function useOperatorQueryState<T>(key: string): QueryState<T> {
  return useSyncExternalStore(
    (listener) => subscribeToOperatorQuery(key, listener),
    () => getOperatorQuerySnapshot<T>(key),
    () => DEFAULT_QUERY_STATE,
  );
}

// `queryFn` should stay stable for a given cache key so renders do not trigger
// redundant rereads for the same authoritative request identity.
export function useOperatorQueryLoader<T>({
  force = false,
  key,
  policy,
  queryFn,
  refreshToken,
}: {
  force?: boolean;
  key: string;
  policy: QueryPolicy;
  queryFn: () => Promise<T>;
  refreshToken?: number;
}) {
  useEffect(() => {
    const snapshot = getOperatorQuerySnapshot<T>(key);
    const shouldLoad =
      force ||
      refreshToken !== undefined ||
      snapshot.data === null ||
      policy.refetchOnMount;

    if (!shouldLoad) {
      return;
    }

    void loadOperatorQuery<T>({
      force: force || refreshToken !== undefined,
      key,
      queryFn,
      retainStaleOnError: policy.retainStaleOnError,
    }).catch(() => undefined);
  }, [
    force,
    key,
    policy.refetchOnMount,
    policy.retainStaleOnError,
    queryFn,
    refreshToken,
  ]);
}

export function resetOperatorQueryCacheForTests() {
  queryCache.clear();
}
