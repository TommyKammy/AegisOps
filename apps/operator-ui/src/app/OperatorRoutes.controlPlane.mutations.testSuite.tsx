import { registerOperatorRoutesControlPlaneActionRequestTests } from "./OperatorRoutes.controlPlane.actionRequests.testSuite";
import { registerOperatorRoutesControlPlaneCaseRecordTests } from "./OperatorRoutes.controlPlane.caseRecords.testSuite";
import { registerOperatorRoutesControlPlanePromotionTests } from "./OperatorRoutes.controlPlane.promotion.testSuite";
import { registerOperatorRoutesControlPlaneTicketRequestTests } from "./OperatorRoutes.controlPlane.ticketRequests.testSuite";

export function registerOperatorRoutesControlPlaneMutationTests() {
  registerOperatorRoutesControlPlanePromotionTests();
  registerOperatorRoutesControlPlaneCaseRecordTests();
  registerOperatorRoutesControlPlaneActionRequestTests();
  registerOperatorRoutesControlPlaneTicketRequestTests();
}
