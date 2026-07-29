from __future__ import annotations


class AuthenticationError(Exception):
    """Base authentication-domain exception."""


class EmailAlreadyRegisteredError(AuthenticationError):
    """Raised when registration attempts to use an existing normalized email."""

    def __init__(
        self,
        message: str = "An account with this email already exists.",
    ) -> None:
        super().__init__(message)


class InvalidCredentialsError(AuthenticationError):
    """Raised for all credential-authentication failures."""

    def __init__(
        self,
        message: str = "Invalid email or password.",
    ) -> None:
        super().__init__(message)


class InactiveAccountError(AuthenticationError):
    """Raised after valid credentials are confirmed but the account is inactive."""

    def __init__(
        self,
        message: str = "This account is inactive.",
    ) -> None:
        super().__init__(message)


class OAuthAccountExistsError(AuthenticationError):
    """Raised when an OAuth-only account exists and user tries password auth."""

    def __init__(
        self,
        message: str = "This account was created with Google or Apple. Please sign in with Google or Apple, or use 'Forgot Password' to set a password.",
    ) -> None:
        super().__init__(message)
