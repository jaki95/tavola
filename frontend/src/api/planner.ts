import {
  apiGetJson,
  apiSendJson,
  type ApiError,
  type ApiResult
} from "./client";
import {
  catalogCategoryIds,
  type CatalogCategoryId
} from "../types/catalog";
import type { Basket, BasketLine } from "../types/basket";
import type {
  AcceptMenuProposalRequest,
  AcceptMenuProposalResponse,
  AcceptedMealPlan,
  AcceptedMealPlanCourse,
  CreatePlannerSessionRequest,
  MenuProposal,
  MenuProposalCourse,
  MenuProposalLine,
  PlannerNote,
  PlannerCourseId,
  PlannerMode,
  PlannerFollowUpRequest,
  PlannerPackageTemplateId,
  PlannerSessionResponse,
  PlannerStatus,
  PlannerStatusResponse,
  PlanningUpdate,
  PlanningUpdateStage,
  PlannerValidationError,
  PlannerValidationErrorCode,
  ValidateMenuProposalRequest
} from "../types/planner";

const catalogCategoryIdSet = new Set<string>(catalogCategoryIds);
const plannerStatusSet = new Set<string>([
  "planning",
  "needs_input",
  "proposal_ready",
  "accepted",
  "failed"
]);
const planningUpdateStageSet = new Set<string>([
  "queued",
  "started",
  "connecting",
  "planning",
  "validating",
  "ready",
  "needs_input",
  "failed"
]);
const plannerModeSet = new Set<string>(["real_codex", "disabled"]);
const plannerCourseIdSet = new Set<string>([
  "antipasto",
  "primo",
  "dessert",
  "aperitivo",
  "drinks"
]);
const plannerPackageTemplateIdSet = new Set<string>([
  "antipasto-primo-dessert",
  "antipasto-primo",
  "primo-dessert",
  "primo-only",
  "aperitivo"
]);
const plannerValidationErrorCodeSet = new Set<string>([
  "unknown_sku",
  "unavailable_sku",
  "invalid_quantity",
  "quantity_exceeds_max",
  "duplicate_sku",
  "unsupported_course",
  "invalid_proposal"
]);

export async function getPlannerStatus(): Promise<ApiResult<PlannerStatusResponse>> {
  const result = await apiGetJson<unknown>("/planner/status");

  if (!result.ok) {
    return result;
  }

  if (isPlannerStatusResponse(result.data)) {
    return {
      ok: true,
      data: result.data
    };
  }

  return {
    ok: false,
    error: invalidPlannerStatusResponseError
  };
}

export async function createPlannerSession(
  request: CreatePlannerSessionRequest
): Promise<ApiResult<PlannerSessionResponse>> {
  return await sendPlannerSessionRequest("/planner/sessions", {
    method: "POST",
    body: request
  });
}

export async function answerFollowUp(
  plannerSessionId: string,
  request: PlannerFollowUpRequest
): Promise<ApiResult<PlannerSessionResponse>> {
  return await sendPlannerSessionRequest(
    `${plannerSessionPath(plannerSessionId)}/follow-up-answer`,
    {
      method: "POST",
      body: request
    }
  );
}

export async function fetchPlannerSession(
  plannerSessionId: string
): Promise<ApiResult<PlannerSessionResponse>> {
  const result = await apiGetJson<unknown>(plannerSessionPath(plannerSessionId));

  return mapPlannerSessionResult(result);
}

export async function validateProposal(
  plannerSessionId: string,
  request: ValidateMenuProposalRequest
): Promise<ApiResult<PlannerSessionResponse>> {
  return await sendPlannerSessionRequest(
    `${plannerSessionPath(plannerSessionId)}/proposal/validate`,
    {
      method: "POST",
      body: request
    }
  );
}

export async function acceptProposal(
  plannerSessionId: string,
  request: AcceptMenuProposalRequest
): Promise<ApiResult<AcceptMenuProposalResponse>> {
  const result = await apiSendJson<unknown>(
    `${plannerSessionPath(plannerSessionId)}/accept`,
    {
      method: "POST",
      body: request
    }
  );

  return mapAcceptProposalResult(result);
}

export const answerPlannerFollowUp = answerFollowUp;
export const getPlannerSession = fetchPlannerSession;
export const validatePlannerProposal = validateProposal;
export const acceptPlannerProposal = acceptProposal;

async function sendPlannerSessionRequest(
  path: string,
  options: { method: "POST"; body: unknown }
): Promise<ApiResult<PlannerSessionResponse>> {
  const result = await apiSendJson<unknown>(path, options);

  return mapPlannerSessionResult(result);
}

function mapPlannerSessionResult(
  result: ApiResult<unknown>
): ApiResult<PlannerSessionResponse> {
  if (!result.ok) {
    return result;
  }

  if (isPlannerSessionResponse(result.data)) {
    return {
      ok: true,
      data: sanitizePlannerSessionResponse(result.data)
    };
  }

  return {
    ok: false,
    error: invalidPlannerSessionResponseError
  };
}

function mapAcceptProposalResult(
  result: ApiResult<unknown>
): ApiResult<AcceptMenuProposalResponse> {
  if (!result.ok) {
    return result;
  }

  if (isAcceptMenuProposalResponse(result.data)) {
    return {
      ok: true,
      data: result.data
    };
  }

  return {
    ok: false,
    error: invalidPlannerAcceptResponseError
  };
}

function plannerSessionPath(plannerSessionId: string): string {
  return `/planner/sessions/${encodeURIComponent(plannerSessionId)}`;
}

function sanitizePlannerSessionResponse(
  response: PlannerSessionResponse
): PlannerSessionResponse {
  return {
    ...response,
    follow_up_question:
      response.follow_up_question === null
        ? null
        : sanitizeCustomerPlannerText(response.follow_up_question),
    menu_proposal:
      response.menu_proposal === null
        ? null
        : sanitizeMenuProposal(response.menu_proposal),
    validation_errors: response.validation_errors.map((error) => ({
      ...error,
      message: sanitizeCustomerPlannerText(error.message)
    })),
    planning_updates: response.planning_updates.map((update) => ({
      ...update,
      message: sanitizeCustomerPlannerText(update.message)
    }))
  };
}

function sanitizeMenuProposal(proposal: MenuProposal): MenuProposal {
  return {
    ...proposal,
    title: sanitizeCustomerPlannerText(proposal.title),
    explanation: sanitizeCustomerPlannerText(proposal.explanation),
    planner_notes: proposal.planner_notes.map((note) => ({
      ...note,
      message: sanitizeCustomerPlannerText(note.message)
    })),
    courses: proposal.courses.map((course) => ({
      ...course,
      course_label: sanitizeCustomerPlannerText(course.course_label),
      lines: course.lines.map((line) => ({
        ...line,
        name: sanitizeCustomerPlannerText(line.name),
        category_label: sanitizeCustomerPlannerText(line.category_label),
        rationale: sanitizeCustomerPlannerText(line.rationale)
      }))
    })),
    warnings: proposal.warnings.map(sanitizeCustomerPlannerText)
  };
}

function sanitizeCustomerPlannerText(value: string): string {
  return value
    .replace(/\bTavola tools\b/gi, "Tavola checks")
    .replace(/\bplanner tool execution\b/gi, "planner checks")
    .replace(/\bTavola is getting your menu request ready\./gi, "Sending request")
    .replace(/\bPlanning has started\./gi, "Sending request")
    .replace(/\bConnecting to Tavola's planner\./gi, "Preparing Tavola's menu checks.")
    .replace(/\bPreparing Tavola's menu checks\./gi, "Sending request")
    .replace(/\bPreparing your menu plan\./gi, "Sending request")
    .replace(/\bRequest received\./gi, "Sending request")
    .replace(/\bStarting request\./gi, "Sending request")
    .replace(/\bRequest queued\./gi, "Sending request")
    .replace(/\bChecking the menu against Tavola's catalog\./gi, "Reviewing products and prices")
    .replace(/\bChecking Tavola's catalog\./gi, "Checking Tavola's catalog")
    .replace(/\bReviewing products and prices\./gi, "Reviewing products and prices")
    .replace(/\bpackage templates\b/gi, "menu plans")
    .replace(/\bpackage template\b/gi, "menu plan")
    .replace(/\btemplates\b/gi, "menu plans")
    .replace(/\btemplate\b/gi, "menu plan")
    .replace(/\bsku_id\b/gi, "product")
    .replace(/\bsku ids\b/gi, "products")
    .replace(/\bskus\b/gi, "products")
    .replace(/\bsku\b/gi, "product");
}

function isPlannerStatusResponse(
  value: unknown
): value is PlannerStatusResponse {
  return (
    isRecord(value) &&
    typeof value["enabled"] === "boolean" &&
    isPlannerMode(value["mode"]) &&
    typeof value["message"] === "string"
  );
}

function isPlannerSessionResponse(
  value: unknown
): value is PlannerSessionResponse {
  if (!isRecord(value)) {
    return false;
  }

  const status = value["status"];
  const menuProposal = value["menu_proposal"];

  return (
    typeof value["planner_session_id"] === "string" &&
    isPlannerStatus(status) &&
    typeof value["customer_request"] === "string" &&
    Array.isArray(value["follow_up_answers"]) &&
    value["follow_up_answers"].every(isString) &&
    (value["follow_up_question"] === null ||
      typeof value["follow_up_question"] === "string") &&
    (menuProposal === null || isMenuProposal(menuProposal)) &&
    Array.isArray(value["validation_errors"]) &&
    value["validation_errors"].every(isPlannerValidationError) &&
    Array.isArray(value["planning_updates"]) &&
    value["planning_updates"].every(isPlanningUpdate)
  );
}

function isPlanningUpdate(value: unknown): value is PlanningUpdate {
  return (
    isRecord(value) &&
    isPlanningUpdateStage(value["stage"]) &&
    typeof value["message"] === "string"
  );
}

function isMenuProposal(value: unknown): value is MenuProposal {
  if (!isRecord(value)) {
    return false;
  }

  return (
    typeof value["title"] === "string" &&
    typeof value["explanation"] === "string" &&
    Array.isArray(value["planner_notes"]) &&
    value["planner_notes"].every(isPlannerNote) &&
    (value["party_size"] === null || isPositiveInteger(value["party_size"])) &&
    isPlannerPackageTemplateId(value["package_template_id"]) &&
    Array.isArray(value["courses"]) &&
    value["courses"].every(isMenuProposalCourse) &&
    isMinorUnitAmount(value["total_minor"]) &&
    typeof value["currency"] === "string" &&
    isNonNegativeInteger(value["item_count"]) &&
    isNonNegativeInteger(value["line_count"]) &&
    Array.isArray(value["warnings"]) &&
    value["warnings"].every(isString)
  );
}

function isPlannerNote(value: unknown): value is PlannerNote {
  return (
    isRecord(value) &&
    typeof value["note_type"] === "string" &&
    typeof value["source"] === "string" &&
    typeof value["message"] === "string"
  );
}

function isMenuProposalCourse(value: unknown): value is MenuProposalCourse {
  if (!isRecord(value)) {
    return false;
  }

  return (
    isPlannerCourseId(value["course"]) &&
    typeof value["course_label"] === "string" &&
    Array.isArray(value["lines"]) &&
    value["lines"].every(isMenuProposalLine)
  );
}

function isMenuProposalLine(value: unknown): value is MenuProposalLine {
  if (!isRecord(value)) {
    return false;
  }

  return (
    typeof value["sku_id"] === "string" &&
    typeof value["name"] === "string" &&
    isCatalogCategoryId(value["category_id"]) &&
    typeof value["category_label"] === "string" &&
    typeof value["unit_label"] === "string" &&
    isPositiveInteger(value["quantity"]) &&
    isMinorUnitAmount(value["unit_price_minor"]) &&
    isMinorUnitAmount(value["line_total_minor"]) &&
    typeof value["currency"] === "string" &&
    typeof value["image_id"] === "string" &&
    typeof value["rationale"] === "string"
  );
}

function isPlannerValidationError(
  value: unknown
): value is PlannerValidationError {
  if (!isRecord(value)) {
    return false;
  }

  return (
    isPlannerValidationErrorCode(value["code"]) &&
    typeof value["message"] === "string" &&
    optionalString(value["sku_id"]) &&
    (value["course"] === undefined ||
      value["course"] === null ||
      isPlannerCourseId(value["course"]))
  );
}

function isAcceptMenuProposalResponse(
  value: unknown
): value is AcceptMenuProposalResponse {
  return (
    isRecord(value) &&
    isBasket(value["basket"]) &&
    isAcceptedMealPlan(value["meal_plan_grouping"])
  );
}

function isAcceptedMealPlan(value: unknown): value is AcceptedMealPlan {
  if (!isRecord(value)) {
    return false;
  }

  return (
    typeof value["title"] === "string" &&
    value["title"].trim().length > 0 &&
    (value["party_size"] === null || isPositiveInteger(value["party_size"])) &&
    isPlannerPackageTemplateId(value["package_template_id"]) &&
    Array.isArray(value["courses"]) &&
    value["courses"].every(isAcceptedMealPlanCourse)
  );
}

function isAcceptedMealPlanCourse(
  value: unknown
): value is AcceptedMealPlanCourse {
  if (!isRecord(value)) {
    return false;
  }

  return (
    isPlannerCourseId(value["course"]) &&
    typeof value["course_label"] === "string" &&
    Array.isArray(value["line_sku_ids"]) &&
    value["line_sku_ids"].every(isString)
  );
}

function isBasket(value: unknown): value is Basket {
  if (!isRecord(value)) {
    return false;
  }

  return (
    typeof value["basket_id"] === "string" &&
    Array.isArray(value["lines"]) &&
    value["lines"].every(isBasketLine) &&
    isMinorUnitAmount(value["total_minor"]) &&
    typeof value["currency"] === "string" &&
    isNonNegativeInteger(value["item_count"]) &&
    isNonNegativeInteger(value["line_count"])
  );
}

function isBasketLine(value: unknown): value is BasketLine {
  if (!isRecord(value)) {
    return false;
  }

  return (
    typeof value["sku_id"] === "string" &&
    typeof value["name"] === "string" &&
    isCatalogCategoryId(value["category_id"]) &&
    typeof value["category_label"] === "string" &&
    typeof value["unit_label"] === "string" &&
    isPositiveInteger(value["quantity"]) &&
    isMinorUnitAmount(value["unit_price_minor"]) &&
    isMinorUnitAmount(value["line_total_minor"]) &&
    typeof value["currency"] === "string" &&
    typeof value["image_id"] === "string"
  );
}

function isPlannerStatus(value: unknown): value is PlannerStatus {
  return typeof value === "string" && plannerStatusSet.has(value);
}

function isPlanningUpdateStage(value: unknown): value is PlanningUpdateStage {
  return typeof value === "string" && planningUpdateStageSet.has(value);
}

function isPlannerMode(value: unknown): value is PlannerMode {
  return typeof value === "string" && plannerModeSet.has(value);
}

function isPlannerCourseId(value: unknown): value is PlannerCourseId {
  return typeof value === "string" && plannerCourseIdSet.has(value);
}

function isPlannerPackageTemplateId(
  value: unknown
): value is PlannerPackageTemplateId {
  return typeof value === "string" && plannerPackageTemplateIdSet.has(value);
}

function isPlannerValidationErrorCode(
  value: unknown
): value is PlannerValidationErrorCode {
  return typeof value === "string" && plannerValidationErrorCodeSet.has(value);
}

function isCatalogCategoryId(value: unknown): value is CatalogCategoryId {
  return typeof value === "string" && catalogCategoryIdSet.has(value);
}

function isMinorUnitAmount(value: unknown): value is number {
  return isNonNegativeInteger(value);
}

function isNonNegativeInteger(value: unknown): value is number {
  return typeof value === "number" && Number.isInteger(value) && value >= 0;
}

function isPositiveInteger(value: unknown): value is number {
  return typeof value === "number" && Number.isInteger(value) && value > 0;
}

function optionalString(value: unknown): boolean {
  return value === undefined || value === null || typeof value === "string";
}

function isString(value: unknown): value is string {
  return typeof value === "string";
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

const invalidPlannerSessionResponseError: ApiError = {
  kind: "invalid_response",
  message: "The Tavola API returned an invalid planner response."
};

const invalidPlannerStatusResponseError: ApiError = {
  kind: "invalid_response",
  message: "The Tavola API returned an invalid planner status response."
};

const invalidPlannerAcceptResponseError: ApiError = {
  kind: "invalid_response",
  message: "The Tavola API returned an invalid planner acceptance response."
};
