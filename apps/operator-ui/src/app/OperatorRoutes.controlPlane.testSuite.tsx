import { registerOperatorRoutesControlPlaneMutationTests } from "./OperatorRoutes.controlPlane.mutations.testSuite";
import { registerOperatorRoutesControlPlaneReadOnlyTests } from "./OperatorRoutes.controlPlane.readOnly.testSuite";

export function registerOperatorRoutesControlPlaneTests() {
  registerOperatorRoutesControlPlaneReadOnlyTests();
  registerOperatorRoutesControlPlaneMutationTests();
}
