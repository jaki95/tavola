import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, test, vi } from "vitest";

import { StorefrontWorkflowTabs } from "./StorefrontWorkflowTabs";
import { getWorkflowPanelId } from "./storefrontWorkflowIds";

describe("StorefrontWorkflowTabs", () => {
  test("renders controlled Shop and Plan workflow tabs with accessible state", () => {
    render(
      <StorefrontWorkflowTabs activeWorkflow="shop" onWorkflowChange={vi.fn()} />
    );

    const tabList = screen.getByRole("tablist", {
      name: "Storefront workflows"
    });
    const shopTab = within(tabList).getByRole("tab", { name: "Shop" });
    const planTab = within(tabList).getByRole("tab", { name: "Plan" });

    expect(shopTab).toHaveAttribute("aria-selected", "true");
    expect(shopTab).toHaveAttribute("aria-controls", getWorkflowPanelId("shop"));
    expect(planTab).toHaveAttribute("aria-selected", "false");
    expect(planTab).toHaveAttribute("aria-controls", getWorkflowPanelId("plan"));
    expect(shopTab).toHaveAttribute("type", "button");
    expect(planTab).toHaveAttribute("type", "button");
  });

  test("delegates workflow selection without owning active state", () => {
    const onWorkflowChange = vi.fn();
    const { rerender } = render(
      <StorefrontWorkflowTabs
        activeWorkflow="shop"
        onWorkflowChange={onWorkflowChange}
      />
    );

    fireEvent.click(screen.getByRole("tab", { name: "Plan" }));

    expect(onWorkflowChange).toHaveBeenCalledWith("plan");
    expect(screen.getByRole("tab", { name: "Shop" })).toHaveAttribute(
      "aria-selected",
      "true"
    );

    rerender(
      <StorefrontWorkflowTabs
        activeWorkflow="plan"
        onWorkflowChange={onWorkflowChange}
      />
    );

    expect(screen.getByRole("tab", { name: "Plan" })).toHaveAttribute(
      "aria-selected",
      "true"
    );
  });
});
