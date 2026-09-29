"""Input validation helpers."""

import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")

ALLOWED_CURRENCIES = {"USD", "EUR", "GBP", "INR", "NGN"}


def valid_email(value: str) -> bool:
    return bool(value) and len(value) <= 254 and EMAIL_RE.match(value) is not None


def valid_slug(value: str) -> bool:
    return bool(value) and SLUG_RE.match(value) is not None


def valid_currency(value: str) -> bool:
    return value in ALLOWED_CURRENCIES


def valid_amount(amount_cents: int) -> bool:
    return isinstance(amount_cents, int) and 0 < amount_cents <= 100_000_000


def clean_description(value: str, limit: int = 140) -> str:
    text = re.sub(r"\s+", " ", value or "").strip()
    return text[:limit]


def validate_expense(payload: dict) -> list[str]:
    errors: list[str] = []
    if not valid_amount(payload.get("amount_cents", 0)):
        errors.append("amount_cents must be a positive integer")
    if not payload.get("group_id"):
        errors.append("group_id is required")
    if clean_description(payload.get("description", "")) == "":
        errors.append("description is required")
    if payload.get("currency") and not valid_currency(payload["currency"]):
        errors.append("unsupported currency")
    return errors
