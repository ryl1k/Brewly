# Demo: Brewly Bot escalates to Supfeel

Brewly's own support bot only knows plans, prices and shipping. Everything else goes to **Supfeel** over MCP
(`brewly/bot.py`), which has read this repository.

## Run

```bash
# Supfeel API on :8000 and dashboard on :3000 must be running
cd brewly && .venv/bin/uvicorn brewly.api:app --port 8100     # http://localhost:8100
curl -X POST localhost:8100/api/admin/reset                    # fresh data before each run
```

Supfeel dashboard login for this demo workspace: `demo@brewly.dev` / `brewly-demo-2026`.

## Script (≈ 4 min)

1. **Show the product and its bugs** (no chat yet):
   - "Gift a friend" → Create account with `maya+coffee@gmail.com` → *Please enter a valid email address*.
   - Your subscription → Pause for **8 weeks** → *You can pause for 1 to 8 weeks* (it says 8, but refuses 8).
2. Open **💬 Help** (signed in as Maya).
   - `How much are the plans?` → answered by Brewly Bot itself. "The first-line bot handles the easy stuff."
3. `I can't sign up my friend, it says the email maya+coffee@gmail.com is invalid`
   - Badge **⚡ Supfeel T-…**: apology + workaround; "Engineering: the EMAIL regex omits '+'".
   - Supfeel dashboard → ticket: root cause, **diff + regression test** (PR + CI when the repo is on GitHub), trace graph.
4. `Please skip my next delivery, I'm travelling` → Supfeel proposes it → **Yes, go ahead** → done and **verified by
   reading the subscription back**; the "Next shipment" date on the page moves two weeks.
5. Switch to **Leo** → `Why was I charged before my coffee arrived?` → explained from Brewly's docs (charged on
   the shipping day, arrives 1–3 days later): no human, no ticket churn.
6. Optional: `I want to pause for 8 weeks but it says I can't` → the second bug (off-by-one `< 8`).
7. Close on the Supfeel **Board**, **Tickets** board and **Inbox** (Telegram buzzes for each bug/action).

Cost: ≈ $0.15 of Claude for the whole run.

## Pull requests instead of patches

Imported from a local folder, fixes are attached to the ticket as a patch. For real PRs + CI: push this repo to a
public GitHub repo, install the Supfeel GitHub App on it, and import it by URL in the workspace.
