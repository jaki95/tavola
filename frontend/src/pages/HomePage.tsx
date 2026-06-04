import {
  BackendStatusPanel,
  type BackendStatus
} from "../components/BackendStatusPanel";
import { CatalogBrowser } from "../features/catalog/CatalogBrowser";

const workflowItems = [
  {
    label: "Catalog",
    href: "#catalog-title",
    status: "Open"
  },
  {
    label: "Basket",
    status: "Planned"
  },
  {
    label: "Checkout",
    status: "Planned"
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
          <a className="nav-link nav-link--active" href={workflowItems[0].href}>
            <span>{workflowItems[0].label}</span>
            <span>{workflowItems[0].status}</span>
          </a>
          {workflowItems.slice(1).map((item) => (
            <button className="nav-placeholder" disabled key={item.label} type="button">
              <span>{item.label}</span>
              <span>{item.status}</span>
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
              A practical deli counter for browsing real products before basket
              editing and mock pickup checkout arrive.
            </p>
          </div>
          <BackendStatusPanel status={backendStatus} />
        </section>

        <CatalogBrowser />
      </main>
    </div>
  );
}
