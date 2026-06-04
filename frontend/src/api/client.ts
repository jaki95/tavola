export type ApiError =
  | {
      kind: "http";
      message: string;
      status: number;
    }
  | {
      kind: "network";
      message: string;
    }
  | {
      kind: "invalid_response";
      message: string;
    };

export type ApiResult<T> =
  | {
      ok: true;
      data: T;
    }
  | {
      ok: false;
      error: ApiError;
    };

type ApiSendJsonOptions = {
  method: "POST" | "PATCH" | "DELETE";
  body?: unknown;
};

const DEFAULT_API_BASE_URL = "/api";

type TavolaEnv = {
  VITE_API_BASE_URL?: string;
};

type TavolaImportMeta = ImportMeta & {
  env: TavolaEnv;
};

export async function apiGetJson<T>(path: string): Promise<ApiResult<T>> {
  return await requestJson(path, {
    headers: { Accept: "application/json" }
  });
}

export async function apiSendJson<T>(
  path: string,
  options: ApiSendJsonOptions
): Promise<ApiResult<T>> {
  const requestOptions: RequestInit = {
    method: options.method,
    headers: { Accept: "application/json" }
  };

  if (options.body !== undefined) {
    requestOptions.headers = {
      ...requestOptions.headers,
      "Content-Type": "application/json"
    };
    requestOptions.body = JSON.stringify(options.body);
  }

  return await requestJson(path, requestOptions);
}

async function requestJson<T>(
  path: string,
  options: RequestInit
): Promise<ApiResult<T>> {
  let response: Response;

  try {
    response = await fetch(buildApiUrl(path), options);
  } catch {
    return {
      ok: false,
      error: {
        kind: "network",
        message: "Could not reach the Tavola API."
      }
    };
  }

  if (!response.ok) {
    const message = await readHttpErrorMessage(response);
    return {
      ok: false,
      error: {
        kind: "http",
        message,
        status: response.status
      }
    };
  }

  try {
    return {
      ok: true,
      data: (await response.json()) as T
    };
  } catch {
    return {
      ok: false,
      error: {
        kind: "invalid_response",
        message: "The Tavola API returned an invalid response."
      }
    };
  }
}

async function readHttpErrorMessage(response: Response): Promise<string> {
  const fallbackMessage =
    response.status >= 500
      ? "Tavola could not complete the request. Please try again."
      : `Request failed with status ${response.status}.`;

  try {
    return extractFastApiErrorMessage(await response.json()) ?? fallbackMessage;
  } catch {
    return fallbackMessage;
  }
}

function extractFastApiErrorMessage(value: unknown): string | null {
  if (!isRecord(value) || !("detail" in value)) {
    return null;
  }

  const detail = value["detail"];
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (!isRecord(item)) {
          return null;
        }
        const message = item["msg"];
        return typeof message === "string" && message.trim() ? message : null;
      })
      .filter((message): message is string => message !== null);

    if (messages.length > 0) {
      return messages.join(" ");
    }
  }

  return null;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function buildApiUrl(path: string): string {
  const baseUrl = resolveApiBaseUrl();
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;

  return `${baseUrl}${normalizedPath}`;
}

export function resolveApiBaseUrl(
  env: TavolaEnv = (import.meta as TavolaImportMeta).env
): string {
  const configuredBaseUrl = env["VITE_API_BASE_URL"]?.trim();
  const baseUrl = configuredBaseUrl || DEFAULT_API_BASE_URL;

  return baseUrl.replace(/\/+$/, "");
}
