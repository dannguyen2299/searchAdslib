class MetaApiError(Exception):
    """Base class for all errors coming from the Meta Ad Library API."""

    def __init__(self, message: str, *, status_code: int | None = None, meta_code: int | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.meta_code = meta_code


class MetaAuthenticationError(MetaApiError):
    """access_token is missing, invalid, or expired (Graph API error code 190)."""


class MetaPermissionError(MetaApiError):
    """The token is valid but lacks permission / identity confirmation for
    the Ad Library API (e.g. facebook.com/ID not completed)."""


class MetaRateLimitError(MetaApiError):
    """Graph API rate limit exceeded (error code 4, 17, 32, 613 or HTTP 429)."""


class MetaTimeoutError(MetaApiError):
    """The request to Meta timed out."""


class MetaApiUnavailableError(MetaApiError):
    """Meta returned a 5xx / network-level failure."""


class MetaBadRequestError(MetaApiError):
    """The request was rejected for a reason unrelated to auth/rate-limit,
    e.g. an unsupported ad_reached_countries value."""
