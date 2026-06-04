import { afterEach, describe, expect, test, vi } from "vitest";

import { resolveApiBaseUrl } from "./client";

describe("getHealth", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.resetModules();
    vi.unstubAllEnvs();
  });

  test("requests backend health from the default API base URL", async () => {
    const getHealth = await loadGetHealth();
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ service: "Tavola API", status: "ok" }), {
        status: 200
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    const result = await getHealth();

    expect(result).toEqual({
      ok: true,
      data: { service: "Tavola API", status: "ok" }
    });
    expect(fetchMock).toHaveBeenCalledWith("/api/health", {
      headers: { Accept: "application/json" }
    });
  });

  test("returns a predictable error for non-OK HTTP responses", async () => {
    const getHealth = await loadGetHealth();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("Unavailable", { status: 503 }))
    );

    const result = await getHealth();

    expect(result).toEqual({
      ok: false,
      error: {
        kind: "http",
        message: "Tavola could not complete the request. Please try again.",
        status: 503
      }
    });
  });

  test("returns a predictable error for transport failures", async () => {
    const getHealth = await loadGetHealth();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new TypeError("Failed to fetch"))
    );

    const result = await getHealth();

    expect(result).toEqual({
      ok: false,
      error: {
        kind: "network",
        message: "Could not reach the Tavola API."
      }
    });
  });

  test("returns a predictable error for invalid health responses", async () => {
    const getHealth = await loadGetHealth();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ status: "ok" }), { status: 200 })
      )
    );

    const result = await getHealth();

    expect(result).toEqual({
      ok: false,
      error: {
        kind: "invalid_response",
        message: "The Tavola API returned an invalid health response."
      }
    });
  });
});

describe("resolveApiBaseUrl", () => {
  test("defaults to /api when VITE_API_BASE_URL is not configured", () => {
    expect(resolveApiBaseUrl({})).toBe("/api");
  });

  test("uses configured VITE_API_BASE_URL without trailing slashes", () => {
    expect(
      resolveApiBaseUrl({ VITE_API_BASE_URL: "https://example.test/api/" })
    ).toBe("https://example.test/api");
  });
});

async function loadGetHealth() {
  const { getHealth } = await import("./health");

  return getHealth;
}
