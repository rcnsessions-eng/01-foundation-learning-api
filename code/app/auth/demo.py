from typing import Annotated

from fastapi import Header, Request

from app.config import Settings
from app.domain import Principal
from app.errors import ServiceError


def require_principal(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> Principal:
    settings: Settings = request.app.state.settings
    principals: dict[str, Principal] = request.app.state.principals
    scheme, separator, credential = (authorization or "").partition(" ")
    subject = (
        settings.demo_credentials.get(credential)
        if separator and scheme.lower() == "bearer"
        else None
    )
    if subject is None:
        raise ServiceError(
            401, "unauthenticated", "Valid local demo authentication is required"
        )
    return principals[subject]
