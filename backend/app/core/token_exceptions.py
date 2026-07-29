from __future__ import annotations


class TokenError(Exception):
    """Base token-domain exception."""


class TokenConfigurationError(TokenError):
    """Raised when JWT configuration is missing or invalid."""

    def __init__(
        self,
        message: str = "Token security is not configured.",
    ) -> None:
        super().__init__(message)


class InvalidTokenError(TokenError):
    """Raised when a token is invalid for any reason other than expiration."""

    def __init__(
        self,
        message: str = "Invalid authentication token.",
    ) -> None:
        super().__init__(message)


class ExpiredTokenError(InvalidTokenError):
    """Raised when the token has expired."""

    def __init__(
        self,
        message: str = "Authentication token has expired.",
    ) -> None:
        super().__init__(message)
