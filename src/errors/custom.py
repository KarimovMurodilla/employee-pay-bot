"""Custom exceptions."""


class ValidationError(Exception):
    """Custom exception for validation errors."""

    pass


class InsufficientFundsError(Exception):
    """Custom exception for insufficient funds."""

    pass


class LimitExceedError(Exception):
    """Custom exception for limit violations."""

    pass
