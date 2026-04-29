import { registerOperatorRoutesCaseworkDetailTests } from "./OperatorRoutes.casework.detail.testSuite";
import { registerOperatorRoutesCaseworkIndexTests } from "./OperatorRoutes.casework.index.testSuite";
import { registerOperatorRoutesCaseworkQueueTests } from "./OperatorRoutes.casework.queue.testSuite";

export function registerOperatorRoutesCaseworkTests() {
  registerOperatorRoutesCaseworkQueueTests();
  registerOperatorRoutesCaseworkIndexTests();
  registerOperatorRoutesCaseworkDetailTests();
}
