"""Brewly HTTP API + the site with its support chat widget."""

import os
from datetime import UTC, datetime
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from brewly import bot, rules, store

app = FastAPI(title="Brewly API", version="1.0.0", description="Coffee subscriptions: customers, plans and subscriptions.")
STATIC = Path(__file__).parent / "static"


def require_service_token(authorization: str = Header(default="")) -> None:
    if authorization != f"Bearer {os.environ.get('BREWLY_SERVICE_TOKEN', 'brewly-demo-token')}":
        raise HTTPException(status_code=401, detail="missing or invalid service token")


def _today():
    return datetime.now(UTC).date()


def _sub(customer_id: str) -> dict:
    sub = store.DB["subscriptions"].get(customer_id)
    if sub is None:
        raise HTTPException(status_code=404, detail="no subscription for this customer")
    return sub


def _save(customer_id: str, fn, *args) -> dict:
    try:
        store.DB["subscriptions"][customer_id] = fn(_sub(customer_id), *args)
    except rules.RuleError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return store.DB["subscriptions"][customer_id]


class Signup(BaseModel):
    name: str
    email: str
    plan: str = "house-blend"


class Pause(BaseModel):
    weeks: int = Field(description="1 to 8 weeks")


@app.get("/api/plans", operation_id="list_plans", summary="List coffee plans and prices")
def list_plans() -> list[dict]:
    return list(store.PLANS.values())


@app.post("/api/signup", operation_id="signup", summary="Create a customer account and subscription", status_code=201)
def signup(body: Signup) -> dict:
    try:
        clean = rules.validate_signup(body.name, body.email)
    except rules.RuleError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    if body.plan not in store.PLANS:
        raise HTTPException(status_code=422, detail="Unknown plan")
    if any(c["email"] == clean["email"] for c in store.DB["customers"].values()):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    cid = f"c_{store.DB['seq']}"
    store.DB["seq"] += 1
    store.DB["customers"][cid] = {"id": cid, **clean}
    store.DB["subscriptions"][cid] = {
        "customer_id": cid, "plan": body.plan, "status": "active", "interval_weeks": 2,
        "next_ship_date": _today().isoformat(), "paused_until": None, "skipped": [],
    }  # fmt: skip
    return store.DB["customers"][cid]


@app.get("/api/customers/{customer_id}", operation_id="get_customer", summary="Get a customer")
def get_customer(customer_id: str) -> dict:
    c = store.DB["customers"].get(customer_id)
    if c is None:
        raise HTTPException(status_code=404, detail="customer not found")
    return c


@app.get("/api/customers/{customer_id}/subscription", operation_id="get_subscription", summary="Get a customer's subscription")
def get_subscription(customer_id: str) -> dict:
    return _sub(customer_id)


@app.get("/api/customers/{customer_id}/charges", operation_id="list_charges", summary="List a customer's charges")
def list_charges(customer_id: str) -> list[dict]:
    return store.DB["charges"].get(customer_id, [])


@app.post(
    "/api/customers/{customer_id}/subscription/pause", operation_id="pause_subscription",
    summary="Pause a subscription for 1 to 8 weeks", dependencies=[Depends(require_service_token)],
)  # fmt: skip
def pause_subscription(customer_id: str, body: Pause) -> dict:
    return _save(customer_id, rules.pause, body.weeks, _today())


@app.post(
    "/api/customers/{customer_id}/subscription/resume", operation_id="resume_subscription",
    summary="Resume a paused subscription", dependencies=[Depends(require_service_token)],
)  # fmt: skip
def resume_subscription(customer_id: str) -> dict:
    return _save(customer_id, rules.resume, _today())


@app.post(
    "/api/customers/{customer_id}/subscription/skip", operation_id="skip_next_delivery",
    summary="Skip the next delivery (up to 24h before it ships)", dependencies=[Depends(require_service_token)],
)  # fmt: skip
def skip_next_delivery(customer_id: str) -> dict:
    return _save(customer_id, rules.skip_next, _today())


@app.post("/api/admin/reset", include_in_schema=False)
def reset() -> dict:
    store.reset()
    bot.SESSIONS.clear()
    return {"status": "reset"}


# ---------------------------------------------------------------------------- site + support bot


class ChatIn(BaseModel):
    session_id: str = Field(min_length=4, max_length=64)
    customer_id: str
    message: str = Field(min_length=1, max_length=2000)


@app.post("/bot/chat", include_in_schema=False)
async def chat(body: ChatIn) -> dict:
    customer = store.DB["customers"].get(body.customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="unknown customer")
    return await bot.handle(body.session_id, customer, body.message)


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/demo/customers", include_in_schema=False)
def demo_customers() -> list[dict]:
    return [{**c, "subscription": store.DB["subscriptions"].get(c["id"])} for c in store.DB["customers"].values()]
