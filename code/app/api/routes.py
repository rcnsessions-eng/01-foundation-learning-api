from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.auth.demo import require_principal
from app.config import Settings
from app.domain import ContentCollection, Health, Identifier, Principal, PublicProgress
from app.services.learning import LearningService

router = APIRouter()
AuthenticatedPrincipal = Annotated[Principal, Depends(require_principal)]


def learning_service(request: Request) -> LearningService:
    service: LearningService = request.app.state.service
    return service


@router.get("/health", response_model=Health)
def health(request: Request) -> Health:
    settings: Settings = request.app.state.settings
    return Health(version=settings.version)


@router.get("/v1/content", response_model=ContentCollection)
def list_content(
    principal: AuthenticatedPrincipal,
    service: Annotated[LearningService, Depends(learning_service)],
    limit: Annotated[int, Query(ge=1, le=20)] = 10,
) -> ContentCollection:
    return service.list_content(principal, limit)


@router.get("/v1/learners/{learner_id}/progress", response_model=PublicProgress)
def read_progress(
    learner_id: Identifier,
    principal: AuthenticatedPrincipal,
    service: Annotated[LearningService, Depends(learning_service)],
) -> PublicProgress:
    return service.read_progress(principal, learner_id)
