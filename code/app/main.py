import json
import logging
import re
import time
from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse, Response

from app.api.routes import router
from app.config import Settings
from app.errors import ServiceError
from app.repositories.memory import (
    InMemoryLearningRepository,
    LearningRepository,
    demo_principals,
)
from app.services.learning import LearningService

LOGGER = logging.getLogger("learning.requests")
REQUEST_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}$")


def error_response(request: Request, status_code: int, code: str, message: str) -> JSONResponse:
    headers = {"WWW-Authenticate": "Bearer"} if status_code == 401 else None
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {"code": code, "message": message, "request_id": request.state.request_id}
        },
        headers=headers,
    )


def create_app(
    repository: LearningRepository | None = None,
    settings: Settings | None = None,
) -> FastAPI:
    configuration = settings if settings is not None else Settings.from_environment()
    LOGGER.setLevel(logging.INFO)
    if not LOGGER.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        LOGGER.addHandler(handler)
    application = FastAPI(title="PRD 01 Synthetic Learning API", version=configuration.version)
    application.state.settings = configuration
    application.state.principals = demo_principals()
    application.state.service = LearningService(
        repository if repository is not None else InMemoryLearningRepository()
    )

    @application.middleware("http")
    async def correlate(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        candidate = request.headers.get("X-Request-ID", "")
        request.state.request_id = (
            candidate
            if REQUEST_ID.fullmatch(candidate)
            and candidate not in configuration.demo_credentials
            else str(uuid4())
        )
        started = time.monotonic()
        try:
            response = await call_next(request)
        except Exception:
            response = error_response(request, 500, "internal_error", "Internal service error")
        response.headers["X-Request-ID"] = request.state.request_id
        route = request.scope.get("route")
        LOGGER.info(
            json.dumps(
                {
                    "event": "http_request",
                    "request_id": request.state.request_id,
                    "method": request.method,
                    "route": getattr(route, "path", "unmatched"),
                    "status": response.status_code,
                    "duration_ms": round((time.monotonic() - started) * 1000, 3),
                }
            )
        )
        return response

    @application.exception_handler(ServiceError)
    async def service_error(request: Request, exception: ServiceError) -> JSONResponse:
        return error_response(request, exception.status_code, exception.code, exception.message)

    @application.exception_handler(RequestValidationError)
    async def validation_error(
        request: Request, exception: RequestValidationError
    ) -> JSONResponse:
        return error_response(request, 422, "invalid_request", "Request validation failed")

    @application.exception_handler(HTTPException)
    async def http_error(request: Request, exception: HTTPException) -> JSONResponse:
        return error_response(
            request, exception.status_code, "http_error", "Request cannot be served"
        )

    application.include_router(router)
    return application
