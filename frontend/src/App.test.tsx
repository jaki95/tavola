import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, test, vi } from "vitest";

import { App } from "./App";
import { getHealth } from "./api/health";

vi.mock("./api/health", () => ({
  getHealth: vi.fn()
}));

const getHealthMock = vi.mocked(getHealth);

describe("App", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  test("renders the Tavola storefront workspace shell", () => {
    getHealthMock.mockResolvedValue({
      ok: true,
      data: { service: "Tavola API", status: "ok" }
    });

    render(<App />);

    expect(
      screen.getByRole("heading", { level: 1, name: "Tavola" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("navigation", { name: "Primary" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /catalog planned/i })
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: /basket planned/i })
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: /checkout planned/i })
    ).toBeDisabled();
  });

  test("shows the backend status loading state by default", () => {
    getHealthMock.mockResolvedValue({
      ok: true,
      data: { service: "Tavola API", status: "ok" }
    });

    render(<App />);

    expect(screen.getByText("Checking backend")).toBeInTheDocument();
    expect(screen.getByText("Waiting for the health check.")).toBeInTheDocument();
  });

  test("shows the backend status success state from the health client", async () => {
    getHealthMock.mockResolvedValue({
      ok: true,
      data: { service: "Tavola API", status: "ok" }
    });

    render(<App />);

    expect(await screen.findByText("Backend connected")).toBeInTheDocument();
    expect(screen.getByText("Tavola API is ready.")).toBeInTheDocument();
  });

  test("shows the backend status error state from the health client", async () => {
    getHealthMock.mockResolvedValue({
      ok: false,
      error: {
        kind: "network",
        message: "Could not reach the Tavola API."
      }
    });

    render(<App />);

    expect(await screen.findByText("Backend unavailable")).toBeInTheDocument();
    expect(
      screen.getByText("Could not reach the Tavola API.")
    ).toBeInTheDocument();
  });
});
