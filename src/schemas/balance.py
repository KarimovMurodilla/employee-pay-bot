from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass
class PaymentRequest:
    """Data class for payment requests."""

    user_id: int
    establishment_id: int
    amount: Decimal
    description: str | None = None
    receipt_data: dict[str, Any] | None = None


@dataclass
class PaymentResult:
    """Data class for payment results."""

    success: bool
    transaction_id: int | None = None
    error_message: str | None = None
    balance_after: Decimal | None = None


@dataclass
class BalanceTopUpRequest:
    """Data class for balance top-up requests."""

    user_id: int
    amount: Decimal
    admin_id: int
    description: str | None = None
