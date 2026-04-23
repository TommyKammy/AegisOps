import { beforeEach, describe } from "vitest";
import { resetOperatorQueryCacheForTests } from "./operatorQueryCache";
import { registerOperatorRoutesActionReviewTests } from "./OperatorRoutes.actionReview.testSuite";
import { registerOperatorRoutesAssistantTests } from "./OperatorRoutes.assistant.testSuite";
import { registerOperatorRoutesAuthAndShellTests } from "./OperatorRoutes.authAndShell.testSuite";
import { registerOperatorRoutesCaseworkTests } from "./OperatorRoutes.casework.testSuite";
import { registerOperatorRoutesControlPlaneTests } from "./OperatorRoutes.controlPlane.testSuite";

describe("OperatorRoutes", () => {
  beforeEach(() => {
    resetOperatorQueryCacheForTests();
  });

  registerOperatorRoutesAuthAndShellTests();
  registerOperatorRoutesActionReviewTests();
  registerOperatorRoutesCaseworkTests();
  registerOperatorRoutesAssistantTests();
  registerOperatorRoutesControlPlaneTests();
});
