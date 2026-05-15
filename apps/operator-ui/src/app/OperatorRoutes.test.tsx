import { beforeEach, describe } from "vitest";
import { resetOperatorQueryCacheForTests } from "./operatorQueryCache";
import { registerOperatorRoutesActionReviewTests } from "./OperatorRoutes.actionReview.testSuite";
import { registerOperatorRoutesAssistantTests } from "./OperatorRoutes.assistant.testSuite";
import { registerOperatorRoutesAuthAndShellTests } from "./OperatorRoutes.authAndShell.testSuite";
import { registerOperatorRoutesBusinessHoursHandoffTests } from "./OperatorRoutes.businessHoursHandoff.testSuite";
import { registerOperatorRoutesCaseworkTests } from "./OperatorRoutes.casework.testSuite";
import { registerOperatorRoutesControlPlaneTests } from "./OperatorRoutes.controlPlane.testSuite";
import { registerOperatorRoutesDetectorActivationReviewTests } from "./OperatorRoutes.detectorActivationReview.testSuite";
import { registerOperatorRoutesFirstLoginChecklistTests } from "./OperatorRoutes.firstLoginChecklist.testSuite";
import { registerOperatorRoutesRecordSearchTests } from "./OperatorRoutes.recordSearch.testSuite";
import { registerOperatorRoutesSourceHealthDashboardTests } from "./OperatorRoutes.sourceHealthDashboard.testSuite";
import { registerOperatorRoutesTodayTests } from "./OperatorRoutes.today.testSuite";

describe("OperatorRoutes", () => {
  beforeEach(() => {
    resetOperatorQueryCacheForTests();
  });

  registerOperatorRoutesAuthAndShellTests();
  registerOperatorRoutesActionReviewTests();
  registerOperatorRoutesCaseworkTests();
  registerOperatorRoutesAssistantTests();
  registerOperatorRoutesControlPlaneTests();
  registerOperatorRoutesDetectorActivationReviewTests();
  registerOperatorRoutesRecordSearchTests();
  registerOperatorRoutesSourceHealthDashboardTests();
  registerOperatorRoutesFirstLoginChecklistTests();
  registerOperatorRoutesTodayTests();
  registerOperatorRoutesBusinessHoursHandoffTests();
});
