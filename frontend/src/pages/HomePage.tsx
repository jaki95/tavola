import {
  BackendStatusPanel,
  type BackendStatus
} from "../components/BackendStatusPanel";

const workflowItems = [
  {
    label: "Catalog",
    detail: "Browse antipasti, primi, desserts, drinks, and pantry staples."
  },
  {
    label: "Basket",
    detail: "Review server-priced deli selections before checkout."
  },
  {
    label: "Checkout",
    detail: "Confirm a mock pickup order when the flow is ready."
  }
] as const;

const workspaceCards = [
  {
    title: "Today's storefront",
    body: "A focused workspace for turning real deli products into a validated basket."
  },
  {
    title: "Pickup flow",
    body: "Checkout will stay lightweight: customer details, pickup window, and no payment processing."
  },
  {
    title: "Planner-ready",
    body: "Future menu proposals will map ideas back to real SKUs before anything reaches the basket."
  }
] as const;

type HomePageProps = {
  backendStatus: BackendStatus;
};

export function HomePage({ backendStatus }: HomePageProps) {
  return (
    <div className="site-shell">
      <header className="top-bar">
        <a className="brand-mark" href="#workspace">
          <span className="brand-mark__eyebrow">Independent Italian deli</span>
          <span className="brand-mark__name">Tavola</span>
        </a>
        <nav aria-label="Primary" className="primary-nav">
          {workflowItems.map((item) => (
            <button className="nav-placeholder" disabled key={item.label} type="button">
              <span>{item.label}</span>
              <span>Planned</span>
            </button>
          ))}
        </nav>
      </header>

      <main className="storefront-workspace" id="workspace">
        <section className="workspace-intro" aria-labelledby="app-title">
          <div className="workspace-intro__copy">
            <p className="eyebrow">Storefront workspace</p>
            <h1 id="app-title">Tavola</h1>
            <p className="intro">
              A practical home base for browsing deli products, shaping a basket,
              and preparing a mock pickup checkout.
            </p>
          </div>
          <BackendStatusPanel status={backendStatus} />
        </section>

        <section className="workflow-strip" aria-label="Commerce workflow">
          {workflowItems.map((item) => (
            <article className="workflow-card" key={item.label}>
              <p className="workflow-card__label">{item.label}</p>
              <p>{item.detail}</p>
              <span>Not wired yet</span>
            </article>
          ))}
        </section>

        <section className="workspace-grid" aria-label="Storefront notes">
          {workspaceCards.map((card) => (
            <article className="workspace-card" key={card.title}>
              <h2>{card.title}</h2>
              <p>{card.body}</p>
            </article>
          ))}
        </section>
      </main>
    </div>
  );
}
