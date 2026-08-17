from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.errors import (
    MetaApiError,
    MetaApiUnavailableError,
    MetaAuthenticationError,
    MetaBadRequestError,
    MetaPermissionError,
    MetaRateLimitError,
    MetaTimeoutError,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

_STATUS_BY_ERROR = {
    MetaAuthenticationError: 401,
    MetaPermissionError: 403,
    MetaRateLimitError: 429,
    MetaTimeoutError: 504,
    MetaApiUnavailableError: 503,
    MetaBadRequestError: 400,
}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(MetaApiError)
    async def handle_meta_api_error(request: Request, exc: MetaApiError) -> JSONResponse:
        status_code = _STATUS_BY_ERROR.get(type(exc), 502)
        logger.error("MetaApiError on %s: %s", request.url.path, exc.message)
        return JSONResponse(status_code=status_code, content={"error": exc.message})
