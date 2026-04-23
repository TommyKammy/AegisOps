import type { DataProvider } from "react-admin";
import {
  getOneForActionReview,
  getOneForAdvisoryOutput,
  getOneForStandardResource,
} from "./operatorDataProvider/detailReaders";
import {
  OperatorDataProviderAuthorizationError,
  OperatorDataProviderContractError,
  rejectUnsupported,
  UnsupportedOperatorDataProviderOperationError,
} from "./operatorDataProvider/errors";
import { getListForStandardResource } from "./operatorDataProvider/listSemantics";
import {
  isStandardResource,
  RESOURCE_BINDINGS,
} from "./operatorDataProvider/resourceBindings";
import type { OperatorDataProviderConfig } from "./operatorDataProvider/types";

export {
  OperatorDataProviderAuthorizationError,
  OperatorDataProviderContractError,
  UnsupportedOperatorDataProviderOperationError,
};

export function createOperatorDataProvider({
  fetchFn = fetch,
}: OperatorDataProviderConfig = {}): DataProvider {
  return {
    create: (_resource) => rejectUnsupported("create", _resource),
    delete: (_resource) => rejectUnsupported("delete", _resource),
    deleteMany: (_resource) => rejectUnsupported("deleteMany", _resource),
    getList(resource, params) {
      if (resource === "advisoryOutput" || resource === "actionReview") {
        return rejectUnsupported("getList", resource);
      }

      if (!isStandardResource(resource)) {
        return rejectUnsupported("getList", resource);
      }

      return getListForStandardResource({
        binding: RESOURCE_BINDINGS[resource],
        fetchFn,
        params,
        resource,
      });
    },
    getMany: (_resource) => rejectUnsupported("getMany", _resource),
    getManyReference: (_resource) =>
      rejectUnsupported("getManyReference", _resource),
    getOne(resource, params) {
      if (resource === "advisoryOutput") {
        return getOneForAdvisoryOutput(fetchFn, params);
      }

      if (resource === "actionReview") {
        return getOneForActionReview(fetchFn, params);
      }

      if (!isStandardResource(resource)) {
        return rejectUnsupported("getOne", resource);
      }

      return getOneForStandardResource(fetchFn, resource, params);
    },
    update: (_resource) => rejectUnsupported("update", _resource),
    updateMany: (_resource) => rejectUnsupported("updateMany", _resource),
  };
}

export const operatorDataProvider = createOperatorDataProvider();
