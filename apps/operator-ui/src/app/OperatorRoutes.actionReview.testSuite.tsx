import { registerOperatorRoutesActionReviewAccessTests } from "./OperatorRoutes.actionReview.access.testSuite";
import { registerOperatorRoutesActionReviewDetailTests } from "./OperatorRoutes.actionReview.detail.testSuite";
import { registerOperatorRoutesActionReviewLinkSafetyTests } from "./OperatorRoutes.actionReview.linkSafety.testSuite";
import { registerOperatorRoutesActionReviewSubmissionTests } from "./OperatorRoutes.actionReview.submission.testSuite";

export function registerOperatorRoutesActionReviewTests() {
  registerOperatorRoutesActionReviewAccessTests();
  registerOperatorRoutesActionReviewDetailTests();
  registerOperatorRoutesActionReviewSubmissionTests();
  registerOperatorRoutesActionReviewLinkSafetyTests();
}
