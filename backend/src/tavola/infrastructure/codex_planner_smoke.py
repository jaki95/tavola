import argparse
import json
import sys
from pathlib import Path

from tavola.application.planner import PlanMenuFromRequest
from tavola.config.settings import (
    MissingPlannerCodexCredentialsError,
    Settings,
)
from tavola.domain.planner import ProposalStatus, ValidatedMenuProposal
from tavola.infrastructure.catalog_repository import StaticCatalogRepository
from tavola.infrastructure.codex_planner import (
    CodexMenuPlannerAgent,
    PythonCodexSdkClient,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run one opt-in real Codex planner smoke against seed catalog."
    )
    parser.add_argument("message", help="Customer meal request for Tavola Planner.")
    args = parser.parse_args(argv)

    settings = Settings()
    try:
        if not settings.use_real_codex_planner():
            print(
                "Real Codex planner is disabled or credentials are missing.",
                file=sys.stderr,
            )
            return 2
    except MissingPlannerCodexCredentialsError as error:
        print(str(error), file=sys.stderr)
        return 2

    planner = PlanMenuFromRequest(
        agent=CodexMenuPlannerAgent(
            client=PythonCodexSdkClient(cwd=Path.cwd()),
            model=settings.planner_codex_model,
            sandbox_mode=settings.planner_codex_sandbox_mode,
            timeout_seconds=settings.planner_codex_timeout_seconds,
        ),
        catalog_repository=StaticCatalogRepository.from_seed(),
    )
    result = planner(customer_request=args.message)
    if result.status != ProposalStatus.PROPOSAL_READY or result.menu_proposal is None:
        payload = {
            "status": result.status.value,
            "validation_errors": [
                {"code": error.code.value, "message": error.message}
                for error in result.validation_errors
            ],
            "agent_error": result.agent_error.code.value
            if result.agent_error is not None
            else None,
        }
        print(json.dumps(payload, indent=2), file=sys.stderr)
        return 1

    print(json.dumps(_proposal_payload(result.menu_proposal), indent=2))
    return 0


def _proposal_payload(proposal: ValidatedMenuProposal) -> dict[str, object]:
    return {
        "title": proposal.title,
        "explanation": proposal.explanation,
        "planner_notes": list(proposal.planner_notes),
        "party_size": proposal.party_size,
        "package_template_id": proposal.package_template_id,
        "courses": [
            {
                "course": course.course.value,
                "lines": [
                    {
                        "sku_id": line.sku.sku_id,
                        "name": line.sku.name,
                        "quantity": line.quantity,
                        "unit_label": line.sku.unit_label,
                        "unit_price_minor": line.sku.price.amount_minor,
                        "line_total_minor": line.line_total.amount_minor,
                        "rationale": line.rationale,
                    }
                    for line in course.lines
                ],
            }
            for course in proposal.courses
        ],
        "total": {
            "amount_minor": proposal.total.amount_minor,
            "currency": proposal.total.currency,
        },
        "item_count": proposal.item_count,
        "line_count": proposal.line_count,
        "warnings": list(proposal.warnings),
    }


if __name__ == "__main__":
    raise SystemExit(main())
