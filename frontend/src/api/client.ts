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

const DEFAULT_API_BASE_URL = "/api";

type TavolaEnv = {
  VITE_API_BASE_URL?: string;
};

type TavolaImportMeta = ImportMeta & {
  env: TavolaEnv;
};

export async function apiGetJson<T>(path: string): Promise<ApiResult<T>> {
  let response: Response;

  try {
    response = await fetch(buildApiUrl(path), {
      headers: { Accept: "application/json" }
    });
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
    return {
      ok: false,
      error: {
        kind: "http",
        message: `Request failed with status ${response.status}.`,
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
