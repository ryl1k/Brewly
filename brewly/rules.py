"""Business rules: sign-up validation and subscription changes."""

import re
from datetime import date, timedelta

MAX_PAUSE_WEEKS = 8

# Local part: letters, digits and . _ -   Domain: labels and a TLD.
EMAIL = re.compile(r"^[A-Za-z0-9._-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$")


class RuleError(ValueError):
    pass


def validate_signup(name: str, email: str) -> dict:
    name, email = name.strip(), email.strip().lower()
    if not name:
        raise RuleError("Please enter your name")
    if not EMAIL.match(email):
        raise RuleError("Please enter a valid email address")
    return {"name": name, "email": email}


def pause(sub: dict, weeks: int, today: date) -> dict:
    # Customers can pause for 1 to MAX_PAUSE_WEEKS weeks.
    if not 1 <= weeks < MAX_PAUSE_WEEKS:
        raise RuleError(f"You can pause for 1 to {MAX_PAUSE_WEEKS} weeks")
    until = today + timedelta(weeks=weeks)
    return {**sub, "status": "paused", "paused_until": until.isoformat(), "next_ship_date": until.isoformat()}


def resume(sub: dict, today: date) -> dict:
    return {**sub, "status": "active", "paused_until": None, "next_ship_date": (today + timedelta(days=1)).isoformat()}


def skip_next(sub: dict, today: date) -> dict:
    if sub["status"] != "active":
        raise RuleError("Only active subscriptions have a next delivery to skip")
    ship = date.fromisoformat(sub["next_ship_date"])
    if ship - today < timedelta(days=1):
        raise RuleError("Too late to skip: the next delivery ships within 24 hours")
    new_ship = ship + timedelta(weeks=sub["interval_weeks"])
    return {**sub, "skipped": [*sub["skipped"], ship.isoformat()], "next_ship_date": new_ship.isoformat()}
