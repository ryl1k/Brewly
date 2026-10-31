"""Brewly's first-line support bot: deliberately simple.

It answers a few FAQ questions itself. Everything else is escalated to Supfeel over MCP (the `escalate`, `reply`
and `confirm` tools), and Supfeel's `customer_reply` is relayed to the customer. When Supfeel needs the customer's
OK for an action, the bot asks the question and passes the answer to `confirm`.
"""

import os
import re
from dataclasses import dataclass, field
from typing import Any

from dotenv import load_dotenv

load_dotenv()

AGENT_NAME = "Brewly Bot"

FAQ: list[tuple[re.Pattern, str]] = [
    (re.compile(r"^\s*(hi|hello|hey|good (morning|afternoon|evening))\b[\s!.?]*$", re.I),
     "Hi! I'm Brewly Bot. Ask me about plans, shipping or pausing, or tell me what's going on."),
    (re.compile(r"\b(plans?|prices?|how much|cost)\b", re.I),
     "We have House Blend ($18), Espresso Roast ($22) and Swiss Water Decaf ($17), per delivery, every 2 weeks."),
    (re.compile(r"\b(shipping|delivery) (cost|fee|free)\b|\bfree shipping\b", re.I),
     "Shipping is always free."),
]  # fmt: skip
YES = re.compile(r"^\s*(yes|yep|yeah|sure|ok|okay|go ahead|please do|do it|confirm)\b", re.I)
NO = re.compile(r"^\s*(no|nope|don'?t|cancel|not now|stop)\b", re.I)


@dataclass
class Session:
    transcript: list[dict[str, str]] = field(default_factory=list)
    ticket_id: str | None = None
    status: str | None = None
    pending_question: str | None = None


SESSIONS: dict[str, Session] = {}


class SupfeelUnavailable(RuntimeError):
    pass


async def call_supfeel(tool: str, args: dict[str, Any]) -> dict[str, Any]:
    """One MCP tool call to Supfeel (streamable HTTP, bearer key)."""
    url, key = os.environ.get("SUPFEEL_MCP_URL", ""), os.environ.get("SUPFEEL_API_KEY", "")
    if not url or not key or key.endswith("..."):
        raise SupfeelUnavailable("Supfeel isn't connected (set SUPFEEL_MCP_URL and SUPFEEL_API_KEY)")
    import httpx2
    from mcp import Client
    from mcp.client.streamable_http import streamable_http_client

    http = httpx2.AsyncClient(headers={"Authorization": f"Bearer {key}"}, timeout=300)
    async with Client(streamable_http_client(url, http_client=http)) as client:
        result = await client.call_tool(tool, args)
    if result.is_error:
        raise SupfeelUnavailable(result.content[0].text if result.content else "Supfeel error")
    return result.structured_content or {}


def local_answer(message: str) -> str | None:
    for pattern, answer in FAQ:
        if pattern.search(message):
            return answer
    return None


def _out(text: str, source: str, s: Session, result: dict | None = None) -> dict[str, Any]:
    s.transcript.append({"role": "assistant", "content": text})
    out: dict[str, Any] = {"text": text, "from": source, "ticket_id": s.ticket_id, "status": s.status}
    if result:
        out["question"] = (result.get("needs_confirmation") or {}).get("question")
        out["action"] = (result.get("needs_confirmation") or {}).get("action")
        out["engineering"] = result.get("engineering")
        out["trace_url"] = result.get("trace_url")
        out["category"] = result.get("category")
    return out


async def handle(session_id: str, customer: dict, message: str) -> dict[str, Any]:
    s = SESSIONS.setdefault(session_id, Session())
    history = list(s.transcript)
    s.transcript.append({"role": "customer", "content": message})
    try:
        # 1. A pending action: the customer's yes/no goes straight to Supfeel's confirm tool.
        if s.pending_question and s.ticket_id and (YES.match(message) or NO.match(message)):
            result = await call_supfeel("confirm", {"ticket_id": s.ticket_id, "approved": bool(YES.match(message))})
            return _relay(s, result)
        # 2. An open escalation continues with Supfeel.
        if s.ticket_id and s.status not in (None, "resolved"):
            return _relay(s, await call_supfeel("reply", {"ticket_id": s.ticket_id, "message": message}))
        # 3. The bot's own (small) knowledge.
        answer = local_answer(message)
        if answer:
            return _out(answer, "bot", s)
        # 4. Out of its depth: escalate with the full handoff.
        result = await call_supfeel(
            "escalate",
            {
                "message": message,
                "conversation": history[-10:],
                "attempted": "Checked the FAQ (plans, prices, shipping); no answer there.",
                "agent": AGENT_NAME,
                "customer": {"name": customer["name"], "email": customer["email"], "ref": customer["id"]},
            },
        )
        return _relay(s, result)
    except SupfeelUnavailable as e:
        return _out(f"Sorry, I can't help with that right now. A teammate will get back to you. ({e})", "bot", s)


def _relay(s: Session, result: dict) -> dict[str, Any]:
    s.ticket_id = result.get("ticket_id", s.ticket_id)
    s.status = result.get("status")
    s.pending_question = (result.get("needs_confirmation") or {}).get("question")
    text = result.get("customer_reply") or "We're on it."
    if s.pending_question:
        text = f"{text}\n\n{s.pending_question}"
    return _out(text, "supfeel", s, result)
