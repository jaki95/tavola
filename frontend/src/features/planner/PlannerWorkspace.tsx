import { useEffect, useState, type FormEvent } from "react";

import { formatBasketMoney } from "../basket/basketFormat";
import { getCatalogImageAsset } from "../catalog/catalogImages";
import type { Basket } from "../../types/basket";
import type {
  AcceptMenuProposalMode,
  MenuProposal,
  MenuProposalLine
} from "../../types/planner";
import { usePlanner, type PlannerClient } from "./usePlanner";

type PlannerWorkspaceProps = {
  basket: Basket | null;
  onBasketAccepted: (basket: Basket) => void;
  onProposalReadyChange?: (isProposalReady: boolean) => void;
  client?: PlannerClient;
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
  client
}: PlannerWorkspaceProps) {
  const planner = usePlanner({ client });
  const [prompt, setPrompt] = useState("");
  const [followUpAnswer, setFollowUpAnswer] = useState("");
  const [isComposerOpen, setIsComposerOpen] = useState(true);
  const [isConfirmingReplace, setIsConfirmingReplace] = useState(false);
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
          onRemoveLine={planner.removeLine}
          onSetLineQuantity={planner.setLineQuantity}
        />
      ) : null}
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
        overlapNote={overlapNote}
        proposal={proposal}
        total={total}
      />

      {proposalDetails}

      {isConfirmingReplace ? (
        <div className="planner-replace-confirmation" role="alert">
          <p>This will replace the current basket.</p>
          <div>
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
      ) : null}

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
  onRemoveLine,
  onSetLineQuantity
}: {
  actionsDisabled: boolean;
  proposal: MenuProposal;
  isReadOnly: boolean;
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
  overlapNote,
  proposal,
  total
}: {
  actionsDisabled: boolean;
  basket: Basket | null;
  isAcceptPending: boolean;
  isConfirmingReplace: boolean;
  onAccept: (mode: AcceptMenuProposalMode) => void;
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
          disabled={!canAccept || isConfirmingReplace}
          onClick={() => onAccept("replace")}
          type="button"
        >
          Replace basket
        </button>
      </div>
    </div>
  );
}

function ProposalLineItem({
  line,
  isDisabled,
  isReadOnly = false,
  onRemoveLine,
  onSetLineQuantity
}: {
  line: MenuProposalLine;
  isDisabled: boolean;
  isReadOnly?: boolean;
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

  function updateQuantity(value: string) {
    const quantity = Number.parseInt(value, 10);
    if (Number.isInteger(quantity) && quantity > 0) {
      onSetLineQuantity(line.sku_id, quantity);
    }
  }

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
        <div className="planner-line__summary">
          <div>
            <h5>{lineName}</h5>
            <p>
              {line.unit_label} · {unitPrice} each
            </p>
          </div>
          <strong>{lineTotal}</strong>
        </div>
        <p className="planner-line__rationale">
          {customerPlannerText(line.rationale)}
        </p>
        {isReadOnly ? null : (
          <div className="planner-line__controls">
            <label>
              <span>Quantity for {lineName}</span>
              <input
                disabled={isDisabled}
                inputMode="numeric"
                min={1}
                onBlur={(event) => updateQuantity(event.currentTarget.value)}
                onChange={(event) => updateQuantity(event.currentTarget.value)}
                type="number"
                value={line.quantity}
              />
            </label>
            <button
              aria-label={`Remove ${lineName} from proposal`}
              className="planner-action--secondary"
              disabled={isDisabled}
              onClick={() => onRemoveLine(line.sku_id)}
              type="button"
            >
              Remove
            </button>
          </div>
        )}
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
