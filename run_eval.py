"""Test the nudges and the checker.

    python run_eval.py            # 25 employees + 14 red-team messages, about 50 cents

Part 1: draft nudges for 25 at-risk employees (5 per stalled step, including Spanish speakers).
        How many pass my rules on the first draft? After one rewrite? Are they helpful?
Part 2: red team. 10 known-bad and 4 known-good messages. Does the checker catch the bad
        ones without flagging the good ones? Which layer catches what: code rules or the model?
"""
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

import nudges

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results"
OUT.mkdir(exist_ok=True)


def sample():
    picked = []
    for step in ["not_started", "viewed_plans", "chose_medical", "stuck_dependents", "review"]:
        group = sorted((p for p in nudges.PEOPLE.values() if p["step"] == step),
                       key=lambda p: (-nudges.risk(p), p["id"]))
        es = [p for p in group if p["language"] == "es"][:1]
        en = [p for p in group if p["language"] == "en"][:5 - len(es)]
        picked += en + es
    return picked


def part1():
    print("Part 1: drafting nudges for 25 at-risk employees\n")
    rows, cost = [], 0.0
    for p in sample():
        r = nudges.build(p)
        nudges.show(r)
        rows.append(r)
        cost += r["cost"]
    first = sum(r["first"]["check"]["passed"] for r in rows)
    final = sum(r["final"]["check"]["passed"] for r in rows)
    helpful = sum(r["final"]["check"]["helpful"] for r in rows)
    broke = Counter(v.split(":")[0] for r in rows for v in r["first"]["check"]["hard"] + r["first"]["check"]["soft"])
    print(f"\n   passed my rules on the first draft:  {first}/{len(rows)}")
    print(f"   passed after one rewrite:            {final}/{len(rows)}")
    print(f"   judged helpful:                      {helpful}/{len(rows)}")
    if broke:
        print("   rules broken on first drafts:       " + ", ".join(f"{k} ({n})" for k, n in broke.most_common()))
    print(f"   est. cost: ${cost:.3f}")
    return rows, cost


def part2():
    print("\nPart 2: red team, can the checker catch bad nudges?\n")
    test_person = {"id": "TEST", "first_name": "Ana", "language": "en", "step": "chose_medical",
                   "days_since_active": 3, "attempts_on_step": 0, "has_dependents": True,
                   "current_plan": "PPO 500", "cost_per_paycheck_now": 120, "cost_per_paycheck_next_year": 158,
                   "similar_plan": "PPO 1000", "similar_plan_cost_next_year": 144,
                   "preferred_channel": "text", "reminders_sent": 1}
    monday_9am = datetime(2026, 11, 16, 9, 0)
    cases = json.load(open(ROOT / "data" / "bad_nudges.json"))
    rows, cost = [], 0.0
    for c in cases:
        result, cst = nudges.check(test_person, c, send_at=monday_9am)
        cost += cst
        flagged = not result["passed"]
        ok = flagged == c["bad"]
        by = ("code" if result["hard"] else "") + ("+model" if result["soft"] else "")
        print(f"   {'ok ' if ok else 'X  '} {c['id']} {c['why']:<38} "
              f"{'flagged' if flagged else 'passed '}  {by.strip('+') or '-'}")
        rows.append({**c, "flagged": flagged, "correct": ok, "hard": result["hard"], "soft": result["soft"]})
    bad = [r for r in rows if r["bad"]]
    good = [r for r in rows if not r["bad"]]
    caught = sum(r["flagged"] for r in bad)
    false_alarms = sum(r["flagged"] for r in good)
    by_code = sum(bool(r["hard"]) for r in bad)
    by_model_only = sum(bool(r["soft"]) and not r["hard"] for r in bad)
    print(f"\n   bad messages caught:        {caught}/{len(bad)}")
    print(f"      caught by code rules:    {by_code}")
    print(f"      caught only by the model: {by_model_only}")
    print(f"   good messages wrongly flagged: {false_alarms}/{len(good)}")
    print(f"   est. cost: ${cost:.3f}")
    return rows, cost


if __name__ == "__main__":
    r1, c1 = part1()
    r2, c2 = part2()
    (OUT / "nudges.json").write_text(json.dumps(r1, indent=1, ensure_ascii=False))
    (OUT / "red_team.json").write_text(json.dumps(r2, indent=1, ensure_ascii=False))
    print(f"\nTotal est. cost: ${c1 + c2:.3f}. Details saved in results/")
