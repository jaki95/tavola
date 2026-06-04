import {
  getWorkflowPanelId,
  getWorkflowTabId,
  type StorefrontWorkflow
} from "./storefrontWorkflowIds";

export type { StorefrontWorkflow };

type StorefrontWorkflowTabsProps = {
  activeWorkflow: StorefrontWorkflow;
  onWorkflowChange: (workflow: StorefrontWorkflow) => void;
};

const workflows: Array<{ id: StorefrontWorkflow; label: string }> = [
  { id: "shop", label: "Shop" },
  { id: "plan", label: "Plan" }
];

export function StorefrontWorkflowTabs({
  activeWorkflow,
  onWorkflowChange
}: StorefrontWorkflowTabsProps) {
  return (
    <div
      aria-label="Storefront workflows"
      className="storefront-workflow-tabs"
      role="tablist"
    >
      {workflows.map((workflow) => (
        <button
          aria-controls={getWorkflowPanelId(workflow.id)}
          aria-selected={activeWorkflow === workflow.id}
          className="storefront-workflow-tabs__tab"
          id={getWorkflowTabId(workflow.id)}
          key={workflow.id}
          onClick={() => onWorkflowChange(workflow.id)}
          role="tab"
          type="button"
        >
          {workflow.label}
        </button>
      ))}
    </div>
  );
}
