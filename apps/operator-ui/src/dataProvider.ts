import type { DataProvider } from "react-admin";

async function unsupported(method: string): Promise<never> {
  throw new Error(
    `The reviewed operator shell does not expose a data provider yet (${method} is intentionally unavailable).`,
  );
}

export const operatorDataProvider: DataProvider = {
  create: () => unsupported("create"),
  delete: () => unsupported("delete"),
  deleteMany: () => unsupported("deleteMany"),
  getList: () => unsupported("getList"),
  getMany: () => unsupported("getMany"),
  getManyReference: () => unsupported("getManyReference"),
  getOne: () => unsupported("getOne"),
  update: () => unsupported("update"),
  updateMany: () => unsupported("updateMany"),
};
