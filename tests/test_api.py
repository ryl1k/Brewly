import pytest
from fastapi.testclient import TestClient

from brewly import bot, store
from brewly.api import app

client = TestClient(app)
AUTH = {"Authorization": "Bearer brewly-demo-token"}


@pytest.fixture(autouse=True)
def _reset():
    store.reset()


def test_plans():
    assert {p["id"] for p in client.get("/api/plans").json()} == {"house-blend", "espresso", "decaf"}


def test_signup():
    r = client.post("/api/signup", json={"name": "Ana", "email": "ana@example.com"})
    assert r.status_code == 201 and r.json()["email"] == "ana@example.com"


def test_signup_rejects_bad_email():
    assert client.post("/api/signup", json={"name": "Ana", "email": "not-an-email"}).status_code == 422


def test_pause_four_weeks():
    r = client.post("/api/customers/c_maya/subscription/pause", json={"weeks": 4}, headers=AUTH)
    assert r.status_code == 200 and r.json()["status"] == "paused"


def test_pause_needs_token():
    assert client.post("/api/customers/c_maya/subscription/pause", json={"weeks": 2}).status_code == 401


def test_skip_next_delivery():
    before = client.get("/api/customers/c_maya/subscription").json()["next_ship_date"]
    r = client.post("/api/customers/c_maya/subscription/skip", headers=AUTH)
    assert r.json()["skipped"] == [before]


def test_bot_answers_faq_locally():
    assert "House Blend" in bot.local_answer("how much are the plans?")
    assert bot.local_answer("my signup is broken") is None
