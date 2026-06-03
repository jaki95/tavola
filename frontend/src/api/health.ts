import { apiGetJson, type ApiError, type ApiResult } from "./client";
import type { HealthResponse } from "../types/health";

export async function getHealth(): Promise<ApiResult<HealthResponse>> {
  const result = await apiGetJson<unknown>("/health");

  if (!result.ok) {
    return result;
  }

  if (isHealthResponse(result.data)) {
    return {
      ok: true,
      data: result.data
    };
  }

  return {
    ok: false,
    error: invalidHealthResponseError
  };
}

function isHealthResponse(value: unknown): value is HealthResponse {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const candidate = value as Record<string, unknown>;

  return (
    typeof candidate["service"] === "string" &&
    typeof candidate["status"] === "string"
  );
}

const invalidHealthResponseError: ApiError = {
  kind: "invalid_response",
  message: "The Tavola API returned an invalid health response."
};
