"""
Business-rule utilities for the parallel agent-session example.

This module is intentionally small and deterministic. It is designed for the
"Session A" agent task: write unit tests for the public functions in this file
without modifying this file.
"""

from __future__ import annotations


VALID_CUSTOMER_TIERS = {"standard", "silver", "gold", "platinum"}


def normalize_name(name: str) -> str:
    """Return a person's name with extra whitespace removed and words title-cased."""
    if not isinstance(name, str):
        raise TypeError("name must be a string")

    cleaned = " ".join(name.strip().split())
    if not cleaned:
        raise ValueError("name cannot be empty")

    return cleaned.title()


def calculate_discount(price: float, customer_tier: str) -> float:
    """Return the discounted price for a customer tier."""
    if price < 0:
        raise ValueError("price cannot be negative")

    tier = customer_tier.strip().lower()
    if tier not in VALID_CUSTOMER_TIERS:
        raise ValueError(f"unknown customer tier: {customer_tier}")

    rates = {
        "standard": 0.00,
        "silver": 0.05,
        "gold": 0.10,
        "platinum": 0.15,
    }

    discounted = price * (1 - rates[tier])
    return round(discounted, 2)


def classify_priority(score: int) -> str:
    """Classify a numeric score as low, medium, high, or urgent priority."""
    if not isinstance(score, int):
        raise TypeError("score must be an integer")

    if score < 0 or score > 100:
        raise ValueError("score must be between 0 and 100")

    if score >= 90:
        return "urgent"
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def summarize_order(items: list[dict[str, float | int | str]]) -> dict[str, float | int]:
    """Return total item count and subtotal for an order."""
    if not items:
        return {"item_count": 0, "subtotal": 0.0}

    item_count = 0
    subtotal = 0.0

    for item in items:
        quantity = item.get("quantity", 0)
        unit_price = item.get("unit_price", 0.0)

        if not isinstance(quantity, int) or quantity < 0:
            raise ValueError("quantity must be a non-negative integer")
        if not isinstance(unit_price, (int, float)) or unit_price < 0:
            raise ValueError("unit_price must be a non-negative number")

        item_count += quantity
        subtotal += quantity * float(unit_price)

    return {"item_count": item_count, "subtotal": round(subtotal, 2)}


def is_valid_project_code(code: str) -> bool:
    """Return True when code follows the format AA-1234."""
    if not isinstance(code, str):
        return False

    parts = code.split("-")
    if len(parts) != 2:
        return False

    prefix, number = parts
    return len(prefix) == 2 and prefix.isalpha() and prefix.isupper() and len(number) == 4 and number.isdigit()
