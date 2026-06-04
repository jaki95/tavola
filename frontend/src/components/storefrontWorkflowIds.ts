export type StorefrontWorkflow = "shop" | "plan";

export function getWorkflowPanelId(workflow: StorefrontWorkflow): string {
  return `storefront-workflow-panel-${workflow}`;
}

export function getWorkflowTabId(workflow: StorefrontWorkflow): string {
  return `storefront-workflow-tab-${workflow}`;
}
