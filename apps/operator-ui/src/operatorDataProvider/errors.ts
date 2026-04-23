export class UnsupportedOperatorDataProviderOperationError extends Error {}

export class OperatorDataProviderAuthorizationError extends Error {
  status: number;

  constructor(status: number) {
    super("Backend operator boundary rejected the request.");
    this.name = "OperatorDataProviderAuthorizationError";
    this.status = status;
  }
}

export class OperatorDataProviderContractError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "OperatorDataProviderContractError";
  }
}

export function rejectUnsupported(
  method: string,
  resource: string,
): Promise<never> {
  return Promise.reject(
    new UnsupportedOperatorDataProviderOperationError(
      `The reviewed operator shell does not support ${method} for resource ${resource}.`,
    ),
  );
}
