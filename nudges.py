"""Open enrollment nudges: find who needs help, pick the right nudge, draft it, check it.

    python nudges.py E001     # one employee, end to end
"""
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import anthropic

import rules

ROOT = Path(__file__).resolve().parent
WRITER_MODEL = "claude-sonnet-5"
CHECKER_MODEL = "claude-haiku-4-5"
PEOPLE = {p["id"]: p for p in json.load(open(ROOT / "data" / "employees.json"))}
WRITER = (ROOT / "prompts" / "writer.md").read_text()
CHECKER = (ROOT / "prompts" / "checker.md").read_text()

# Scenario: Monday morning, Nov 16, 2026. Enrollment closes Friday, Nov 20 at 5 PM.
NOW = datetime.fromisoformat(os.environ.get("NOW", "2026-11-16T08:30"))
DEADLINE = datetime(2026, 11, 20, 17, 0)
DEADLINE_TEXT = "Friday, Nov 20 at 5 PM"

_client = None


def client():
    global _client
    _client = _client or anthropic.Anthropic()
    return _client


def risk(p):
    """How likely this person is to miss the deadline, 0 to 1. In code so it's explainable."""
    if p["step"] == "done":
        return 0.0
    score = {"not_started": .5, "viewed_plans": .4, "chose_medical": .3,
             "stuck_dependents": .35, "review": .15}[p["step"]]
    score += min(p["days_since_active"], 14) / 14 * .3
    score += .15 if p["attempts_on_step"] >= 3 else 0
    return round(min(score, 1.0), 2)


def strategy(p):
    """Which nudge fits where they are. One clear idea per message."""
    increase = p["cost_per_paycheck_next_year"] - p["cost_per_paycheck_now"]
    if p["step"] == "stuck_dependents" or p["attempts_on_step"] >= 3:
        return "offer_help", "They're stuck on a step. Offer help first: benefits chat or an HR call."
    if p["step"] in ("not_started", "viewed_plans") and p["similar_plan_cost_next_year"]:
        return "real_money", f"Lead with the real cost change (+${increase} per paycheck) and the similar plan that costs less."
    if p["step"] in ("not_started", "viewed_plans"):
        return "keep_or_compare", "Make it simple: keep their current plan or compare. Mention the cost change only if it isn't zero."
    if p["step"] == "review":
        return "almost_done", "They're on the review page. One step left: review and submit."
    return "pick_up", "They chose medical. Pick up where they left off: dental, vision, dependents, review."


def send_time(p):
    """Next allowed slot: weekdays at 9 AM or 12 PM, never in quiet hours."""
    t = NOW
    while True:
        for hour in (9, 12):
            slot = t.replace(hour=hour, minute=0, second=0, microsecond=0)
            if slot > NOW and slot.weekday() < 5 and slot < DEADLINE:
                return slot
        t = (t + timedelta(days=1)).replace(hour=0)


def facts(p):
    keep = ["first_name", "language", "step", "days_since_active", "has_dependents", "current_plan",
            "cost_per_paycheck_now", "cost_per_paycheck_next_year", "similar_plan", "similar_plan_cost_next_year"]
    f = {k: p[k] for k in keep}
    f["increase_per_paycheck"] = p["cost_per_paycheck_next_year"] - p["cost_per_paycheck_now"]
    if p["similar_plan_cost_next_year"]:
        f["similar_plan_saves_per_paycheck"] = p["cost_per_paycheck_next_year"] - p["similar_plan_cost_next_year"]
    return f


WRITE_SCHEMA = {"type": "object", "additionalProperties": False,
                "required": ["subject", "body", "facts_used"],
                "properties": {"subject": {"type": "string"}, "body": {"type": "string"},
                               "facts_used": {"type": "array", "items": {"type": "string"}}}}
CHECK_SCHEMA = {"type": "object", "additionalProperties": False,
                "required": ["violations", "helpful", "helpful_reason"],
                "properties": {
                    "violations": {"type": "array", "items": {
                        "type": "object", "additionalProperties": False, "required": ["rule", "quote"],
                        "properties": {"rule": {"type": "string", "enum": [
                            "fake_urgency", "social_comparison", "guilt_or_fear",
                            "scarcity_or_competition", "misleading", "condescending"]},
                            "quote": {"type": "string"}}}},
                    "helpful": {"type": "boolean"}, "helpful_reason": {"type": "string"}}}


def _call(model, system, content, schema, max_tokens):
    r = client().messages.create(model=model, max_tokens=max_tokens, system=system,
                                 messages=[{"role": "user", "content": content}],
                                 output_config={"format": {"type": "json_schema", "schema": schema}})
    rates = {WRITER_MODEL: (3, 15), CHECKER_MODEL: (1, 5)}[model]
    cost = (r.usage.input_tokens * rates[0] + r.usage.output_tokens * rates[1]) / 1e6
    return json.loads(next(b.text for b in r.content if b.type == "text")), cost


def draft(p, feedback=None):
    name, how = strategy(p)
    content = (f"Employee facts:\n{json.dumps(facts(p), indent=1)}\n\nStrategy: {name}. {how}\n"
               f"Channel: {p['preferred_channel']}\nReal deadline: {DEADLINE_TEXT}\n"
               f"Days until the deadline when this is sent: {(DEADLINE.date() - send_time(p).date()).days}")
    if feedback:
        content += "\n\nYour last draft broke these rules. Rewrite it without them:\n- " + "\n- ".join(feedback)
    out, cost = _call(WRITER_MODEL, WRITER, content, WRITE_SCHEMA, 1000)
    out["channel"] = p["preferred_channel"]
    return out, cost


def check(p, nudge, send_at=None):
    """Two layers: hard rules in code, then a cheaper model for judgment calls (tone, guilt, pressure)."""
    send_at = send_at or send_time(p)
    hard = rules.check(p, nudge, send_at, DEADLINE)
    content = (f"Employee facts:\n{json.dumps(facts(p), indent=1)}\nReal deadline: {DEADLINE_TEXT}\n\n"
               f"Message ({nudge['channel']}):\nSubject: {nudge.get('subject', '')}\n{nudge['body']}")
    soft, cost = _call(CHECKER_MODEL, CHECKER, content, CHECK_SCHEMA, 800)
    soft_found = [f"{v['rule']}: \"{v['quote']}\"" for v in soft["violations"]]
    return {"hard": hard, "soft": soft_found, "helpful": soft["helpful"],
            "helpful_reason": soft["helpful_reason"], "passed": not hard and not soft_found}, cost


def build(p):
    """Draft, check, and if it fails, rewrite once with the reasons. Returns everything for the report."""
    nudge, c1 = draft(p)
    result, c2 = check(p, nudge)
    first = {"nudge": nudge, "check": result}
    final, cost = first, c1 + c2
    if not result["passed"]:
        nudge2, c3 = draft(p, feedback=result["hard"] + result["soft"])
        result2, c4 = check(p, nudge2)
        final, cost = {"nudge": nudge2, "check": result2}, cost + c3 + c4
    return {"id": p["id"], "step": p["step"], "language": p["language"], "risk": risk(p),
            "strategy": strategy(p)[0], "send_at": send_time(p).strftime("%a %b %d, %I:%M %p"),
            "first": first, "final": final, "revised": final is not first, "cost": round(cost, 4)}


def show(r):
    n, c = r["final"]["nudge"], r["final"]["check"]
    print(f"\n{r['id']}  step: {r['step']}  risk: {r['risk']}  strategy: {r['strategy']}  "
          f"{n['channel']}, {r['send_at']}")
    if n.get("subject"):
        print(f"   Subject: {n['subject']}")
    print(f"   {n['body']}")
    print(f"   {'PASS' if c['passed'] else 'FAIL'}"
          f"{'  (after one rewrite)' if r['revised'] else ''}  helpful: {c['helpful']}")
    for v in c["hard"] + c["soft"]:
        print(f"   - {v}")


if __name__ == "__main__":
    pid = sys.argv[1] if len(sys.argv) > 1 else next(i for i, x in PEOPLE.items() if x["step"] != "done")
    p = PEOPLE[pid]
    if p["step"] == "done":
        print(f"{pid} already submitted. No nudge.")
    else:
        r = build(p)
        show(r)
        print(f"\n   est. cost: ${r['cost']}")
