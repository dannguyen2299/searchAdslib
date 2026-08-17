import logging

from app.config import get_settings

_REDACTED = "***REDACTED***"
_SENSITIVE_KEYS = {"access_token", "meta_access_token", "app_secret", "meta_app_secret"}


def redact_params(params: dict) -> dict:
    """Returns a copy of params safe to log — never print access tokens or secrets."""
    return {k: (_REDACTED if k.lower() in _SENSITIVE_KEYS else v) for k, v in params.items()}


def configure_logging() -> None:
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    # httpx/httpcore log the full request URL (including our access_token
    # query param) at INFO level by default — silence that so the token
    # never ends up in logs regardless of the configured app log level.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
