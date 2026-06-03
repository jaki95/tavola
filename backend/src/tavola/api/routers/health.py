from typing import TypedDict

from fastapi import APIRouter, Request


class HealthResponse(TypedDict):
    service: str
    status: str


router = APIRouter(tags=["health"])


@router.get("/health")
def read_health(request: Request) -> HealthResponse:
    return {"service": request.app.title, "status": "ok"}
