# Brewly: coffee subscriptions

Brewly delivers freshly roasted coffee on a schedule. Customers sign up, pick a blend, and manage their
subscription (pause, skip a delivery, change plan). A small support bot on the site answers the basics and
escalates everything else to **Supfeel** over MCP.

This repo is a demo target for Supfeel: it has real bugs that Supfeel finds and fixes from customer tickets.

## Business rules

- **Plans**: House Blend $18, Espresso Roast $22, Swiss Water Decaf $17, per delivery. Shipping is always free.
- **Schedule**: every 2 weeks. You are charged on the shipping day, and the coffee arrives 1–3 days later.
- **Pause**: 1 to 8 weeks (inclusive). Charges stop while paused; the schedule resumes automatically.
- **Skip**: skip the next delivery any time up to 24 hours before its shipping day. Skipped deliveries aren't charged.
- **Cancel**: any time, no fee.
- **Sign-up**: name and a valid email address (any standard address, including `+` tags like `maya+coffee@gmail.com`).

## API

OpenAPI: [`openapi.json`](openapi.json). Write operations need `Authorization: Bearer $BREWLY_SERVICE_TOKEN`
(default `brewly-demo-token`).

## Run

```bash
pip install -r requirements.txt
cp .env.example .env           # SUPFEEL_MCP_URL + SUPFEEL_API_KEY for the support bot
uvicorn brewly.api:app --port 8100     # site + chat widget: http://localhost:8100
pytest
```
