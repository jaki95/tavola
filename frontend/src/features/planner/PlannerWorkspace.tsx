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
  const [isConfirmingReplace, setIsConfirmingReplace] = useState(false);
  const isPlanning = planner.state.status === "planning";
  const isAcceptPending = planner.state.status === "accept_pending";
  const isAccepted = planner.state.status === "accepted";
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
    setIsConfirmingReplace(false);
    await planner.submitPrompt(prompt);
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
        </div>
      </div>

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

      {isPlannerUnavailable ? (
        <p className="planner-workspace__alert" role="alert">
          {planner.plannerStatus.message}
        </p>
      ) : null}

      {planner.state.status === "planning" ? (
        <p className="planner-workspace__status" role="status">
          {planningProgressMessage(planner.planningElapsedMs)}
        </p>
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
        <div className="planner-follow-up">
          <p className="planner-follow-up__request">
            {customerPlannerText(planner.state.session.customer_request)}
          </p>
          <h3>{customerPlannerText(planner.state.session.follow_up_question ?? "")}</h3>
          <form className="planner-follow-up__form" onSubmit={submitFollowUp}>
            <label>
              <span>Follow-up answer</span>
              <input
                disabled={isPlanning}
                onChange={(event) => setFollowUpAnswer(event.target.value)}
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

function planningProgressMessage(elapsedMs: number | null): string {
  const elapsed = elapsedMs ?? 0;

  if (elapsed >= 30_000) {
    return "Still planning.";
  }

  if (elapsed >= 15_000) {
    return "Validating products and prices.";
  }

  if (elapsed >= 5_000) {
    return "Checking the catalog and shaping a menu.";
  }

  return "Tavola is planning your menu.";
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
  const total = formatBasketMoney({
    amount_minor: proposal.total_minor,
    currency: proposal.currency
  });
  const basketHasLines = Boolean(basket && basket.lines.length > 0);
  const actionsDisabled = isAcceptPending || isAccepted;

  return (
    <div className="planner-proposal" aria-label="Menu proposal">
      <div className="planner-proposal__summary">
        <div>
          <p className="eyebrow">Menu proposal</p>
          <h3>{customerPlannerText(proposal.title)}</h3>
          <p>{customerPlannerText(proposal.explanation)}</p>
        </div>
        <div className="planner-proposal__total" aria-live="polite">
          <span>{total}</span>
          <span>{proposal.item_count} items</span>
        </div>
      </div>

      <div className="planner-notes" aria-label="Planner notes">
        <h4>Planner notes</h4>
        <ul>
          {proposal.planner_notes.map((note) => (
            <li key={`${note.note_type}-${note.message}`}>
              {customerPlannerText(note.message)}
            </li>
          ))}
        </ul>
      </div>

      {proposal.warnings.length > 0 ? (
        <div className="planner-warnings" role="note">
          {proposal.warnings.map((warning) => (
            <p key={warning}>{customerPlannerText(warning)}</p>
          ))}
        </div>
      ) : null}

      <div className="planner-courses">
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
                  canRemove={course.lines.length > 1}
                  isDisabled={actionsDisabled}
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

      <div className="planner-proposal__actions">
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

function ProposalLineItem({
  line,
  canRemove,
  isDisabled,
  onRemoveLine,
  onSetLineQuantity
}: {
  line: MenuProposalLine;
  canRemove: boolean;
  isDisabled: boolean;
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
            className="planner-action--secondary"
            disabled={isDisabled || !canRemove}
            onClick={() => onRemoveLine(line.sku_id)}
            type="button"
          >
            Remove {lineName} from proposal
          </button>
        </div>
      </div>
    </li>
  );
}

function customerPlannerText(value: string): string {
  return value
    .replace(/\bTavola tools\b/gi, "Tavola checks")
    .replace(/\bplanner tool execution\b/gi, "planner checks")
    .replace(/\bpackage templates\b/gi, "menu structures")
    .replace(/\bpackage template\b/gi, "menu structure")
    .replace(/\btemplates\b/gi, "menu structures")
    .replace(/\btemplate\b/gi, "menu structure")
    .replace(/\bsku_id\b/gi, "product")
    .replace(/\bsku ids\b/gi, "products")
    .replace(/\bskus\b/gi, "products")
    .replace(/\bsku\b/gi, "product");
}
