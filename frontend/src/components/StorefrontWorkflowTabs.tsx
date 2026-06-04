import {
  getWorkflowPanelId,
  getWorkflowTabId,
  type StorefrontWorkflow
} from "./storefrontWorkflowIds";

export type { StorefrontWorkflow };

type StorefrontWorkflowTabsProps = {
  activeWorkflow: StorefrontWorkflow;
  onWorkflowChange: (workflow: StorefrontWorkflow) => void;
  planBadgeLabel?: string;
};

const workflows: Array<{ id: StorefrontWorkflow; label: string }> = [
  { id: "shop", label: "Shop" },
  { id: "plan", label: "Plan" }
];

export function StorefrontWorkflowTabs({
  activeWorkflow,
  onWorkflowChange,
  planBadgeLabel
}: StorefrontWorkflowTabsProps) {
  return (
    <div
      aria-label="Storefront workflows"
      className="storefront-workflow-tabs"
      role="tablist"
    >
      {workflows.map((workflow) => {
        const badgeLabel = workflow.id === "plan" ? planBadgeLabel : undefined;

        return (
          <button
            aria-controls={getWorkflowPanelId(workflow.id)}
            aria-describedby={
              badgeLabel ? `${getWorkflowTabId(workflow.id)}-badge` : undefined
            }
            aria-label={workflow.label}
            aria-selected={activeWorkflow === workflow.id}
            className="storefront-workflow-tabs__tab"
            id={getWorkflowTabId(workflow.id)}
            key={workflow.id}
            onClick={() => onWorkflowChange(workflow.id)}
            role="tab"
            type="button"
          >
            <span>{workflow.label}</span>
            {badgeLabel ? (
              <span
                className="storefront-workflow-tabs__badge"
                id={`${getWorkflowTabId(workflow.id)}-badge`}
              >
                {badgeLabel}
              </span>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
