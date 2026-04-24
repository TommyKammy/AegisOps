import { useMemo } from "react";
import { useDataProvider } from "react-admin";
import {
  buildOperatorQueryKey,
  useOperatorQueryLoader,
  useOperatorQueryState,
} from "../operatorQueryCache";
import type { UnknownRecord } from "./recordUtils";

interface QueryState<T> {
  data: T | null;
  error: Error | null;
  loading: boolean;
  refreshing: boolean;
}

export function useOperatorList(
  resource: string,
  filter: Record<string, unknown>,
  sort: { field: string; order: "ASC" | "DESC" },
  perPage = 25,
): QueryState<UnknownRecord[]> {
  const dataProvider = useDataProvider();
  const key = useMemo(
    () => buildOperatorQueryKey(["list", resource, filter, perPage, sort]),
    [filter, perPage, resource, sort],
  );
  const queryFn = useMemo(
    () => async () => {
      const result = await dataProvider.getList(resource, {
        filter,
        pagination: {
          page: 1,
          perPage,
        },
        sort,
      });

      return result.data.map((record) => record as UnknownRecord);
    },
    [dataProvider, filter, perPage, resource, sort],
  );
  const state = useOperatorQueryState<UnknownRecord[]>(key);

  useOperatorQueryLoader({
    key,
    policy: {
      refetchOnMount: true,
      retainStaleOnError: true,
    },
    queryFn,
  });

  return state;
}

export function useOperatorRecord(
  resource: string,
  id: string,
  meta?: Record<string, unknown>,
): QueryState<UnknownRecord> {
  const dataProvider = useDataProvider();
  const metaRecord = meta && typeof meta === "object" ? meta : {};
  const { reloadToken, ...cacheableMeta } = metaRecord;
  const refreshToken =
    typeof reloadToken === "number" && reloadToken > 0 ? reloadToken : undefined;
  const requestMetaKey = useMemo(
    () => buildOperatorQueryKey(["request-meta", metaRecord]),
    [metaRecord],
  );
  const requestMeta = useMemo(
    () => (Object.keys(metaRecord).length > 0 ? metaRecord : undefined),
    [requestMetaKey],
  );
  const key = useMemo(
    () => buildOperatorQueryKey(["record", resource, id, cacheableMeta]),
    [cacheableMeta, id, resource],
  );
  const queryFn = useMemo(
    () => async () => {
      const result = await dataProvider.getOne(resource, {
        id,
        meta: requestMeta,
      });

      return result.data as UnknownRecord;
    },
    [dataProvider, id, requestMeta, requestMetaKey, resource],
  );
  const state = useOperatorQueryState<UnknownRecord>(key);

  useOperatorQueryLoader({
    force: refreshToken !== undefined,
    key,
    policy: {
      refetchOnMount: true,
      retainStaleOnError: true,
    },
    queryFn,
    refreshToken,
  });

  return state;
}
