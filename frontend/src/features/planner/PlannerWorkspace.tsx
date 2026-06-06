import { useEffect, useRef, useState, type FormEvent } from "react";

import { QuantityStepper } from "../../components/QuantityStepper";
import { getCatalogProduct } from "../../api/catalog";
import type { ApiResult } from "../../api/client";
import { formatBasketMoney } from "../basket/basketFormat";
import { CatalogDetail } from "../catalog/CatalogDetail";
import { getCatalogImageAsset } from "../catalog/catalogImages";
import type { CatalogDetailState } from "../catalog/useCatalogBrowser";
import type { Basket } from "../../types/basket";
import type { CatalogProductDetail } from "../../types/catalog";
import type {
  AcceptMenuProposalMode,
  MenuProposal,
  MenuProposalLine
} from "../../types/planner";
import { usePlanner, type PlannerClient } from "./usePlanner";

type PlannerCatalogClient = {
  getCatalogProduct: typeof getCatalogProduct;
};

type PlannerWorkspaceProps = {
  basket: Basket | null;
  onBasketAccepted: (basket: Basket) => void;
  onProposalReadyChange?: (isProposalReady: boolean) => void;
  client?: PlannerClient;
  catalogClient?: PlannerCatalogClient;
};

const examplePrompts = [
  "Classic Italian dinner for 2",
  "Weekend lunch for 6",
  "Antipasti spread for a party"
];

export function PlannerWorkspace({
  basket,
  onBasketAccepted,
  onProposalReadyChange,
  client,
  catalogClient = { getCatalogProduct }
}: PlannerWorkspaceProps) {
  const planner = usePlanner({ client });
  const [prompt, setPrompt] = useState("");
  const [followUpAnswer, setFollowUpAnswer] = useState("");
  const [isComposerOpen, setIsComposerOpen] = useState(true);
  const [isConfirmingReplace, setIsConfirmingReplace] = useState(false);
  const [productDetail, setProductDetail] = useState<CatalogDetailState>({
    status: "closed"
  });
  const detailRequestId = useRef(0);
  const isPlanning =
    planner.state.status === "planning" ||
    planner.state.session?.status === "planning";
  const isAcceptPending = planner.state.status === "accept_pending";
  const isAccepted = planner.state.status === "accepted";
  const activeRequest =
    planner.state.session?.customer_request ??
    (!isComposerOpen ? prompt.trim() : "");
  const isPlannerUnavailable =
    planner.plannerStatus.status === "disabled" ||
    planner.plannerStatus.status === "error";
  const hasReviewableProposal =
    planner.state.status === "proposal_ready" && Boolean(planner.draftProposal);

  useEffect(() => {
    onProposalReadyChange?.(hasReviewableProposal);
  }, [hasReviewableProposal, onProposalReadyChange]);

  async function submitPrompt(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedPrompt = prompt.trim();
    if (trimmedPrompt) {
      setPrompt(trimmedPrompt);
      setIsComposerOpen(false);
    }
    setIsConfirmingReplace(false);
    await planner.submitPrompt(trimmedPrompt);
  }

  async function submitFollowUp(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await planner.submitFollowUp(followUpAnswer);
    setFollowUpAnswer("");
  }

  async function acceptProposal(mode: AcceptMenuProposalMode) {
    if (!basket || isAcceptPending || isAccepted) {
      return;
    }

    if (mode === "replace" && basket.lines.length > 0 && !isConfirmingReplace) {
      setIsConfirmingReplace(true);
      return;
    }

    const acceptedBasket = await planner.acceptProposal(basket.basket_id, mode);
    if (acceptedBasket) {
      onBasketAccepted(acceptedBasket);
      setIsConfirmingReplace(false);
    }
  }

  function startNewRequest() {
    if (!planner.reset()) {
      return;
    }

    setPrompt("");
    setFollowUpAnswer("");
    setIsConfirmingReplace(false);
    setIsComposerOpen(true);
  }

  function closeProductDetail() {
    detailRequestId.current += 1;
    setProductDetail({ status: "closed" });
  }

  function openProductDetail(skuId: string) {
    const requestId = detailRequestId.current + 1;
    detailRequestId.current = requestId;
    setProductDetail({ status: "loading", skuId });

    async function loadProductDetail() {
      const result = await catalogClient.getCatalogProduct(skuId);

      if (detailRequestId.current !== requestId) {
        return;
      }

      setProductDetail(mapPlannerProductDetailResult(skuId, result));
    }

    void loadProductDetail();
  }

  return (
    <section
      aria-labelledby="planner-workspace-title"
      className={[
        "planner-workspace",
        planner.draftProposal ? "planner-workspace--expanded" : ""
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <div className="planner-workspace__header">
        <div className="planner-workspace__title-group">
          <div className="planner-workspace__heading-line">
            <h2 id="planner-workspace-title">Plan a menu</h2>
            <span className="planner-workspace__codex">powered by Codex</span>
          </div>
          <p className="planner-workspace__lede">
            Include party size, budget, occasion, or constraints.
          </p>
        </div>
      </div>

      {isComposerOpen ? (
        <>
          <div className="planner-intake">
            <form className="planner-composer" onSubmit={submitPrompt}>
              <label className="planner-composer__field">
                <span>Meal request</span>
                <textarea
                  disabled={isPlannerUnavailable}
                  name="meal-request"
                  onChange={(event) => setPrompt(event.target.value)}
                  placeholder="Vegetarian dinner for 4 around £50"
                  rows={2}
                  value={prompt}
                />
              </label>
              <button
                disabled={isPlannerUnavailable || !prompt.trim()}
                type="submit"
              >
                Plan menu
              </button>
            </form>

            <PlannerTrust />
          </div>

          <div className="planner-examples" aria-label="Example meal requests">
            <span>Try an example</span>
            {examplePrompts.map((examplePrompt) => (
              <button
                disabled={isPlannerUnavailable}
                key={examplePrompt}
                onClick={() => setPrompt(examplePrompt)}
                type="button"
              >
                {examplePrompt}
              </button>
            ))}
          </div>
        </>
      ) : activeRequest ? (
        <div className="planner-intake planner-intake--submitted">
          <div
            className="planner-request-summary"
            aria-label="Current planner request"
          >
            <div>
              <span>Planning for</span>
              <strong>{customerPlannerText(activeRequest)}</strong>
            </div>
            <button
              className="planner-action--secondary"
              disabled={isPlanning}
              onClick={startNewRequest}
              title={
                isPlanning
                  ? "Wait for Tavola to finish planning before starting another request."
                  : undefined
              }
              type="button"
            >
              New request
            </button>
          </div>
          <PlannerTrust />
        </div>
      ) : null}

      {isPlannerUnavailable ? (
        <p className="planner-workspace__alert" role="alert">
          {planner.plannerStatus.message}
        </p>
      ) : null}

      {planner.state.status === "planning" ? (
        <PlanningStatus elapsedMs={planner.planningElapsedMs} />
      ) : null}

      {planner.state.status === "failed" ||
      planner.state.status === "validation_error" ? (
        <p className="planner-workspace__alert" role="alert">
          {customerPlannerText(planner.state.message)}
        </p>
      ) : null}

      {planner.state.status === "accepted" ? (
        <p className="planner-workspace__status" role="status">
          {customerPlannerText(planner.state.message)}
        </p>
      ) : null}

      {planner.state.status === "needs_input" && planner.state.session ? (
        <div className="planner-follow-up" aria-label="Planner follow-up">
          <div className="planner-follow-up__question">
            <p>Planner needs one choice before review.</p>
            <h3>{customerPlannerText(planner.state.session.follow_up_question ?? "")}</h3>
          </div>
          <form className="planner-follow-up__form" onSubmit={submitFollowUp}>
            <label>
              <span>Follow-up answer</span>
              <input
                disabled={isPlanning}
                onChange={(event) => setFollowUpAnswer(event.target.value)}
                placeholder="Full lunch with dessert"
                value={followUpAnswer}
              />
            </label>
            <button disabled={!followUpAnswer.trim()} type="submit">
              Continue planning
            </button>
          </form>
        </div>
      ) : null}

      {planner.draftProposal ? (
        <ProposalReview
          basket={basket}
          isAccepted={isAccepted}
          isAcceptPending={isAcceptPending}
          isConfirmingReplace={isConfirmingReplace}
          proposal={planner.draftProposal}
          onAccept={acceptProposal}
          onCancelReplace={() => setIsConfirmingReplace(false)}
          onOpenProductDetail={openProductDetail}
          onRemoveLine={planner.removeLine}
          onSetLineQuantity={planner.setLineQuantity}
        />
      ) : null}

      <CatalogDetail
        detail={productDetail}
        onClose={closeProductDetail}
        showAddAction={false}
      />
    </section>
  );
}

function PlannerTrust() {
  return (
    <aside className="planner-trust" aria-label="Planner validation promise">
      <strong>Tavola validates before Basket changes.</strong>
      <ul>
        <li>Real Products from the catalog</li>
        <li>Prices come from Tavola's catalog</li>
        <li>Dietary requests checked against product labels</li>
        <li>Menu proposal shown for review</li>
      </ul>
    </aside>
  );
}

function mapPlannerProductDetailResult(
  skuId: string,
  result: ApiResult<CatalogProductDetail>
): CatalogDetailState {
  if (!result.ok) {
    return {
      status: "error",
      skuId,
      message: result.error.message
    };
  }

  return {
    status: "success",
    skuId,
    product: result.data
  };
}

function PlanningStatus({ elapsedMs }: { elapsedMs: number | null }) {
  const progress = planningProgress(elapsedMs);

  return (
    <section
      aria-label="Planning updates"
      aria-live="polite"
      className="planner-live"
      role="status"
    >
      <div className="planner-live__summary">
        <span aria-hidden="true" className="planner-live__signal" />
        <div>
          <p>{progress.message}</p>
        </div>
      </div>
      <ol className="planner-live__steps" aria-label="Planning progress">
        {planningSteps.map((step, index) => (
          <li
            className={
              index < progress.activeIndex
                ? "planner-live__step planner-live__step--done"
                : index === progress.activeIndex
                  ? "planner-live__step planner-live__step--active"
                  : "planner-live__step"
            }
            key={step}
          >
            {step}
          </li>
        ))}
      </ol>
    </section>
  );
}

const planningSteps = ["Catalog", "Menu shape", "Prices", "Review"];

function planningProgress(elapsedMs: number | null): {
  activeIndex: number;
  message: string;
} {
  const elapsed = elapsedMs ?? 0;

  if (elapsed >= 30_000) {
    return {
      activeIndex: 3,
      message: "Tavola is checking the proposal before review."
    };
  }

  if (elapsed >= 15_000) {
    return {
      activeIndex: 2,
      message: "Validating products and prices."
    };
  }

  if (elapsed >= 5_000) {
    return {
      activeIndex: 1,
      message: "Checking the catalog and shaping a menu."
    };
  }

  return {
    activeIndex: 0,
    message: "Tavola is planning your menu."
  };
}

function ProposalReview({
  basket,
  proposal,
  isAccepted,
  isAcceptPending,
  isConfirmingReplace,
  onAccept,
  onCancelReplace,
  onOpenProductDetail,
  onRemoveLine,
  onSetLineQuantity
}: {
  basket: Basket | null;
  proposal: MenuProposal;
  isAccepted: boolean;
  isAcceptPending: boolean;
  isConfirmingReplace: boolean;
  onAccept: (mode: AcceptMenuProposalMode) => void;
  onCancelReplace: () => void;
  onOpenProductDetail: (skuId: string) => void;
  onRemoveLine: (skuId: string) => void;
  onSetLineQuantity: (skuId: string, quantity: number) => void;
}) {
  const [isReceiptExpanded, setIsReceiptExpanded] = useState(false);
  const total = formatBasketMoney({
    amount_minor: proposal.total_minor,
    currency: proposal.currency
  });
  const basketHasLines = Boolean(basket && basket.lines.length > 0);
  const actionsDisabled = isAcceptPending || isAccepted;
  const overlapNote = getBasketOverlapNote(basket, proposal);
  const proposalDetails = (
    <ProposalDetails
      actionsDisabled={actionsDisabled}
      proposal={proposal}
      isReadOnly={isAccepted}
      onOpenProductDetail={onOpenProductDetail}
      onRemoveLine={onRemoveLine}
      onSetLineQuantity={onSetLineQuantity}
    />
  );

  if (isAccepted) {
    return (
      <div
        className="planner-proposal planner-proposal--accepted"
        aria-label="Menu proposal receipt"
      >
        <div className="planner-proposal-receipt">
          <div className="planner-proposal-receipt__copy">
            <span>Basket updated</span>
            <h3>{customerPlannerText(proposal.title)}</h3>
            <p>
              {total} · {proposal.item_count}{" "}
              {proposal.item_count === 1 ? "item" : "items"} moved to Basket.
              Continue from Basket when ready.
            </p>
          </div>
          <button
            aria-expanded={isReceiptExpanded}
            className="planner-action--secondary"
            onClick={() => setIsReceiptExpanded((isExpanded) => !isExpanded)}
            type="button"
          >
            {isReceiptExpanded ? "Hide proposal" : "View proposal"}
          </button>
        </div>

        {isReceiptExpanded ? proposalDetails : null}
      </div>
    );
  }

  return (
    <div className="planner-proposal" aria-label="Menu proposal">
      <div className="planner-proposal__summary">
        <div>
          <h3>{customerPlannerText(proposal.title)}</h3>
          <p>{customerPlannerText(proposal.explanation)}</p>
        </div>
        <div className="planner-proposal__totals" aria-live="polite">
          <div>
            <span>Total</span>
            <strong>{total}</strong>
          </div>
          <div>
            <span>Products</span>
            <strong>{proposal.item_count}</strong>
          </div>
        </div>
      </div>

      <ProposalActionStrip
        actionsDisabled={actionsDisabled}
        basket={basket}
        isAcceptPending={isAcceptPending}
        isConfirmingReplace={isConfirmingReplace}
        onAccept={onAccept}
        onCancelReplace={onCancelReplace}
        overlapNote={overlapNote}
        proposal={proposal}
        total={total}
      />

      {proposalDetails}

      <div className="planner-proposal__actions" aria-label="Menu proposal actions">
        <button
          disabled={actionsDisabled || proposal.line_count === 0 || !basket}
          onClick={() => onAccept("append")}
          type="button"
        >
          {isAcceptPending ? "Adding" : "Add to basket"}
        </button>
        <button
          className="planner-action--secondary"
          disabled={
            actionsDisabled ||
            proposal.line_count === 0 ||
            !basket ||
            (basketHasLines && isConfirmingReplace)
          }
          onClick={() => onAccept("replace")}
          type="button"
        >
          Replace basket
        </button>
      </div>
    </div>
  );
}

function ProposalDetails({
  actionsDisabled,
  proposal,
  isReadOnly,
  onOpenProductDetail,
  onRemoveLine,
  onSetLineQuantity
}: {
  actionsDisabled: boolean;
  proposal: MenuProposal;
  isReadOnly: boolean;
  onOpenProductDetail: (skuId: string) => void;
  onRemoveLine: (skuId: string) => void;
  onSetLineQuantity: (skuId: string, quantity: number) => void;
}) {
  return (
    <>
      {proposal.warnings.length > 0 ? (
        <div className="planner-warnings" role="note">
          {proposal.warnings.map((warning) => (
            <p key={warning}>{customerPlannerText(warning)}</p>
          ))}
        </div>
      ) : null}

      <div className="planner-courses" aria-label="Proposal courses">
        {proposal.courses.map((course) => (
          <section
            aria-label={course.course_label}
            className="planner-course"
            key={course.course}
          >
            <h4>{customerPlannerText(course.course_label)}</h4>
            <ul className="planner-course__lines">
              {course.lines.map((line) => (
                <ProposalLineItem
                  isDisabled={actionsDisabled}
                  isReadOnly={isReadOnly}
                  key={line.sku_id}
                  line={line}
                  onOpenProductDetail={onOpenProductDetail}
                  onRemoveLine={onRemoveLine}
                  onSetLineQuantity={onSetLineQuantity}
                />
              ))}
            </ul>
          </section>
        ))}
      </div>

      <div className="planner-notes" aria-label="Planner notes">
        <div>
          <h4>Validation notes</h4>
          <p>Tavola checked catalog items, labels, and prices.</p>
        </div>
        <ul>
          {proposal.planner_notes.map((note) => (
            <li key={`${note.note_type}-${note.message}`}>
              {customerPlannerText(note.message)}
            </li>
          ))}
        </ul>
      </div>
    </>
  );
}

function ProposalActionStrip({
  actionsDisabled,
  basket,
  isAcceptPending,
  isConfirmingReplace,
  onAccept,
  onCancelReplace,
  overlapNote,
  proposal,
  total
}: {
  actionsDisabled: boolean;
  basket: Basket | null;
  isAcceptPending: boolean;
  isConfirmingReplace: boolean;
  onAccept: (mode: AcceptMenuProposalMode) => void;
  onCancelReplace: () => void;
  overlapNote: string;
  proposal: MenuProposal;
  total: string;
}) {
  const itemLabel = proposal.item_count === 1 ? "item" : "items";
  const canAccept = !actionsDisabled && proposal.line_count > 0 && Boolean(basket);

  return (
    <div
      className="planner-proposal-action-strip"
      aria-label="Proposal basket actions"
    >
      <div className="planner-proposal-action-strip__details">
        <div>
          <span>Total</span>
          <strong>{total}</strong>
        </div>
        <div>
          <span>Items</span>
          <strong>
            {proposal.item_count} {itemLabel}
          </strong>
        </div>
        <p>{overlapNote}</p>
      </div>
      {isConfirmingReplace ? (
        <div
          className="planner-proposal-action-strip__confirmation"
          role="alert"
        >
          <p>This will replace the current Basket.</p>
          <div className="planner-proposal-action-strip__actions">
            <button
              disabled={actionsDisabled}
              onClick={() => onAccept("replace")}
              type="button"
            >
              Confirm replace basket
            </button>
            <button
              className="planner-action--secondary"
              disabled={actionsDisabled}
              onClick={onCancelReplace}
              type="button"
            >
              Keep current basket
            </button>
          </div>
        </div>
      ) : (
        <div className="planner-proposal-action-strip__actions">
          <button
            aria-label="Add proposal to basket"
            disabled={!canAccept}
            onClick={() => onAccept("append")}
            type="button"
          >
            {isAcceptPending ? "Adding" : "Add to basket"}
          </button>
          <button
            aria-label="Replace basket with proposal"
            className="planner-action--secondary"
            disabled={!canAccept}
            onClick={() => onAccept("replace")}
            type="button"
          >
            Replace basket
          </button>
        </div>
      )}
    </div>
  );
}

function ProposalLineItem({
  line,
  isDisabled,
  isReadOnly = false,
  onOpenProductDetail,
  onRemoveLine,
  onSetLineQuantity
}: {
  line: MenuProposalLine;
  isDisabled: boolean;
  isReadOnly?: boolean;
  onOpenProductDetail: (skuId: string) => void;
  onRemoveLine: (skuId: string) => void;
  onSetLineQuantity: (skuId: string, quantity: number) => void;
}) {
  const lineName = customerPlannerText(line.name);
  const image = getCatalogImageAsset(line.image_id, lineName);
  const unitPrice = formatBasketMoney({
    amount_minor: line.unit_price_minor,
    currency: line.currency
  });
  const lineTotal = formatBasketMoney({
    amount_minor: line.line_total_minor,
    currency: line.currency
  });

  return (
    <li className="planner-line" aria-label={lineName}>
      <span aria-hidden="true" className="planner-line__rail" />
      <img
        alt={image.alt}
        className="planner-line__image"
        height={image.height}
        src={image.src}
        width={image.width}
      />
      <div className="planner-line__body">
        <div className="planner-line__copy">
          <div className="planner-line__title-row">
            <h5>{lineName}</h5>
            <button
              aria-label={`View details for ${lineName}`}
              className="planner-line__detail-action"
              onClick={() => onOpenProductDetail(line.sku_id)}
              title={`View details for ${lineName}`}
              type="button"
            >
              <span aria-hidden="true">i</span>
            </button>
          </div>
          <p>
            {line.unit_label} · {unitPrice} each
          </p>
          <p className="planner-line__rationale">
            {customerPlannerText(line.rationale)}
          </p>
        </div>
        <div className="planner-line__commerce">
          <strong>{lineTotal}</strong>
          {isReadOnly ? null : (
            <div className="planner-line__controls">
              <QuantityStepper
                className="planner-line__quantity"
                decreaseLabel={`Decrease ${lineName} quantity`}
                disabled={isDisabled}
                groupLabel={`${lineName} quantity`}
                increaseLabel={`Increase ${lineName} quantity`}
                inputLabel={`Quantity for ${lineName}`}
                quantity={line.quantity}
                onQuantityChange={(quantity) =>
                  onSetLineQuantity(line.sku_id, quantity)
                }
              />
              <button
                aria-label={`Remove ${lineName} from proposal`}
                className="planner-action--secondary planner-line__remove"
                disabled={isDisabled}
                onClick={() => onRemoveLine(line.sku_id)}
                type="button"
              >
                Remove
              </button>
            </div>
          )}
        </div>
      </div>
    </li>
  );
}

function customerPlannerText(value: string): string {
  return value
    .replace(/\bTavola tools\b/gi, "Tavola checks")
    .replace(/\bplanner tool execution\b/gi, "planner checks")
    .replace(/\bpackage templates\b/gi, "menu plans")
    .replace(/\bpackage template\b/gi, "menu plan")
    .replace(/\btemplates\b/gi, "menu plans")
    .replace(/\btemplate\b/gi, "menu plan")
    .replace(/\bsku_id\b/gi, "product")
    .replace(/\bsku ids\b/gi, "products")
    .replace(/\bskus\b/gi, "products")
    .replace(/\bsku\b/gi, "product");
}

function getBasketOverlapNote(
  basket: Basket | null,
  proposal: MenuProposal
): string {
  if (!basket) {
    return "Basket unavailable.";
  }

  if (basket.lines.length === 0) {
    return "Basket empty. Add or replace starts from this proposal.";
  }

  const proposalSkuIds = new Set(
    proposal.courses.flatMap((course) => course.lines.map((line) => line.sku_id))
  );
  const overlapCount = basket.lines.filter((line) =>
    proposalSkuIds.has(line.sku_id)
  ).length;

  if (overlapCount > 0) {
    const productLabel = overlapCount === 1 ? "Product" : "Products";
    return `${overlapCount} ${productLabel} already in Basket. Add increases quantities; Replace swaps Basket.`;
  }

  const itemLabel = basket.item_count === 1 ? "item" : "items";
  return `Basket has ${basket.item_count} ${itemLabel}. Add keeps them; Replace swaps Basket.`;
}
