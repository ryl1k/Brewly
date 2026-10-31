"""In-memory data store with seed data (POST /api/admin/reset restores it)."""

import copy
from datetime import UTC, datetime, timedelta

PLANS = {
    "house-blend": {"id": "house-blend", "name": "House Blend", "price_cents": 1800},
    "espresso": {"id": "espresso", "name": "Espresso Roast", "price_cents": 2200},
    "decaf": {"id": "decaf", "name": "Swiss Water Decaf", "price_cents": 1700},
}

_today = datetime.now(UTC).date()

SEED = {
    "customers": {
        "c_maya": {"id": "c_maya", "name": "Maya Chen", "email": "maya@example.com"},
        "c_leo": {"id": "c_leo", "name": "Leo Park", "email": "leo@example.com"},
    },
    "subscriptions": {
        "c_maya": {
            "customer_id": "c_maya", "plan": "house-blend", "status": "active", "interval_weeks": 2,
            "next_ship_date": (_today + timedelta(days=4)).isoformat(), "paused_until": None, "skipped": [],
        },
        "c_leo": {
            "customer_id": "c_leo", "plan": "espresso", "status": "active", "interval_weeks": 2,
            "next_ship_date": (_today + timedelta(days=9)).isoformat(), "paused_until": None, "skipped": [],
        },
    },
    "charges": {
        "c_maya": [{"amount_cents": 1800, "date": (_today - timedelta(days=10)).isoformat(), "plan": "house-blend"}],
        "c_leo": [{"amount_cents": 2200, "date": (_today - timedelta(days=5)).isoformat(), "plan": "espresso"}],
    },
}  # fmt: skip

DB: dict = {}


def reset() -> None:
    DB.clear()
    DB.update(copy.deepcopy(SEED))
    DB["seq"] = 100


reset()
