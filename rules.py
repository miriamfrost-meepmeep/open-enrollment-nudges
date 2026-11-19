"""Hard rules checked in code. No AI. Every one of these comes from my teardown of eBay and Depop."""
import re

BANNED = ["act fast", "act now", "hurry", "don't miss out", "dont miss out", "last chance",
          "before it's too late", "time is running out", "running out", "only a few",
          "limited", "everyone", "your coworkers", "your co-workers", "most people",
          "other employees", "your team has", "be the first",
          "date limite se acerca rápido", "no te quedes atrás", "todos tus compañeros", "date prisa", "última oportunidad"]
QUIET_START, QUIET_END = 20, 8      # no sends from 8 PM to 8 AM
MAX_REMINDERS = 3                   # total for the whole enrollment window
MONTHS = r"(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?|enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)"


def allowed_money(f):
    """Only dollar amounts that appear in the facts the writer was given."""
    keys = ["cost_per_paycheck_now", "cost_per_paycheck_next_year", "increase_per_paycheck",
            "similar_plan_cost_next_year", "similar_plan_saves_per_paycheck"]
    return {f[k] for k in keys if f.get(k) is not None}


PASSIVE_PHRASES = ["stays the same", "stay the same", "stays in place", "carries over", "carry over",
                   "renews automatically", "automatically renew", "keep my plan", "keep your plan",
                   "do nothing", "no action needed", "no need to do anything",
                   "se mantiene", "mantener mi plan", "mantener tu plan", "sigue igual", "se renueva"]
CONSEQUENCE = r"(no (medical |health )?(coverage|benefits)|won't have (medical |health )?(coverage|benefits)|will not have|without (coverage|benefits)|lose (your )?(coverage|benefits)|coverage (will )?end|sin (cobertura|beneficios)|no tendr[aá]s)"


REUSE = ["re-select", "reselect", "re-enroll in your", "same plan", "keep your", "keep my",
         "volver a elegir", "mismo plan", "mantener"]


def check(p, nudge, send_at, deadline, enrollment="active", offered=True, facts=None):
    facts = facts or p
    """Returns a list of rule violations. Empty list = passes."""
    text = (nudge.get("subject") or "") + " " + nudge["body"]
    low = text.lower()
    found = []
    for phrase in BANNED:
        if phrase in low:
            found.append(f"banned phrase: '{phrase}'")
    for m in re.finditer(r"\$\s?(\d[\d,]*(?:\.\d+)?)", text):
        if round(float(m.group(1).replace(",", ""))) not in allowed_money(facts):
            found.append(f"number not in the facts: ${m.group(1)}")
    for m in re.finditer(r"%", text):
        found.append("percentage used (no facts include percentages)")
        break
    for m in re.finditer(rf"\b{MONTHS}\s+(?P<a>\d{{1,2}})\b|\b(?P<b>\d{{1,2}})\s+de\s+{MONTHS}", low):
        day = int(m.group("a") or m.group("b"))
        if day != deadline.day:
            found.append(f"date that isn't the deadline: '{m.group(0)}'")
    if enrollment == "active":
        for phrase in PASSIVE_PHRASES:
            if phrase in low:
                found.append(f"says the plan carries over, but enrollment is active: '{phrase}'")
        if not re.search(CONSEQUENCE, low):
            found.append("missing the required notice: no selection means no benefits next year")
    if not offered:
        for phrase in REUSE:
            if phrase in low:
                found.append(f"suggests reusing a plan that isn't offered next year: '{phrase}'")
        plan = p["current_plan"].lower()
        if plan in low and not re.search(r"(no longer|not (be )?offered|discontinued|ending|won't be available|ya no (se )?ofrece|no estar[aá] disponible)", low):
            found.append(f"mentions {p['current_plan']} without saying it's no longer offered")
    days_left = (deadline.date() - send_at.date()).days
    if days_left > 1 and re.search(r"\b(today|tonight|24 hours|hours left|hoy|esta noche)\b", low):
        found.append(f"urgency stronger than the real deadline ({days_left} days left)")
    if not (QUIET_END <= send_at.hour < QUIET_START):
        found.append(f"send time in quiet hours: {send_at:%I:%M %p}")
    if p["reminders_sent"] + 1 > MAX_REMINDERS:
        found.append(f"over the {MAX_REMINDERS}-reminder cap")
    limit = 300 if nudge["channel"] in ("text", "app") else 900
    if len(nudge["body"]) > limit:
        found.append(f"too long for {nudge['channel']}: {len(nudge['body'])} characters")
    return found
