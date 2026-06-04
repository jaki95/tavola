import type { Basket } from "./basket";
import type { CatalogCategoryId } from "./catalog";

export type PlannerStatus =
  | "needs_input"
  | "proposal_ready"
  | "accepted"
  | "failed";

export type PlannerCourseId = "antipasto" | "primo" | "dessert" | "aperitivo";

export type PlannerPackageTemplateId =
  | "antipasto-primo-dessert"
  | "antipasto-primo"
  | "primo-dessert"
  | "primo-only"
  | "aperitivo";

export type PlannerValidationErrorCode =
  | "unknown_sku"
  | "unavailable_sku"
  | "invalid_quantity"
  | "quantity_exceeds_max"
  | "duplicate_sku"
  | "unsupported_course"
  | "invalid_proposal";

export type PlannerValidationError = {
  code: PlannerValidationErrorCode;
  message: string;
  sku_id?: string | null;
  course?: PlannerCourseId | null;
};

export type FollowUpQuestion = {
  message: string;
};

export type PlannerNote = {
  note_type: string;
  source: string;
  message: string;
};

export type MenuProposalLine = {
  sku_id: string;
  name: string;
  category_id: CatalogCategoryId;
  category_label: string;
  unit_label: string;
  quantity: number;
  unit_price_minor: number;
  line_total_minor: number;
  currency: string;
  image_id: string;
  rationale: string;
};

export type MenuProposalCourse = {
  course: PlannerCourseId;
  course_label: string;
  lines: MenuProposalLine[];
};

export type MenuProposal = {
  title: string;
  explanation: string;
  planner_notes: PlannerNote[];
  party_size: number | null;
  package_template_id: PlannerPackageTemplateId;
  courses: MenuProposalCourse[];
  total_minor: number;
  currency: string;
  item_count: number;
  line_count: number;
  warnings: string[];
};

export type PlannerSessionResponse = {
  planner_session_id: string;
  status: PlannerStatus;
  customer_request: string;
  follow_up_answers: string[];
  follow_up_question: string | null;
  menu_proposal: MenuProposal | null;
  validation_errors: PlannerValidationError[];
};

export type CreatePlannerSessionRequest = {
  message: string;
};

export type PlannerFollowUpRequest = {
  message: string;
};

export type ValidateMenuProposalRequest = {
  menu_proposal: MenuProposal;
};

export type AcceptMenuProposalMode = "append" | "replace";

export type AcceptMenuProposalLineRequest = {
  sku_id: string;
  quantity: number;
};

export type AcceptMenuProposalRequest = {
  basket_id: string;
  mode: AcceptMenuProposalMode;
  menu_proposal: MenuProposal;
};

export type AcceptedMealPlanCourse = {
  course: PlannerCourseId;
  course_label: string;
  line_sku_ids: string[];
};

export type AcceptedMealPlan = {
  title: string;
  party_size: number | null;
  package_template_id: PlannerPackageTemplateId;
  courses: AcceptedMealPlanCourse[];
};

export type AcceptMenuProposalResponse = {
  basket: Basket;
  meal_plan_grouping: AcceptedMealPlan;
};
