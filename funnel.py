"""Where employees are in the enrollment flow, and where they stall. Free, no AI.

    python funnel.py
"""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
people = json.load(open(ROOT / "data" / "employees.json"))
FLOW = ["not_started", "viewed_plans", "chose_medical", "stuck_dependents", "review", "done"]
LABEL = {"not_started": "Haven't logged in", "viewed_plans": "Looked at plans, chose nothing",
         "chose_medical": "Chose medical, stopped", "stuck_dependents": "Stuck adding dependents",
         "review": "On the review page, didn't submit", "done": "Submitted"}
count = Counter(p["step"] for p in people)
total = len(people)
print(f"{total} employees, 4 days before the deadline\n")
for step in FLOW:
    n = count[step]
    print(f"  {LABEL[step]:<36} {n:>4}  {n / total:5.1%}  {'#' * round(n / total * 60)}")
not_done = total - count["done"]
print(f"\n  Not submitted: {not_done} ({not_done / total:.0%})")
idle = sum(1 for p in people if p["step"] != "done" and p["days_since_active"] >= 5)
print(f"  Not submitted and idle 5+ days: {idle}")
hike = sum(1 for p in people if p["step"] != "done" and p["cost_per_paycheck_next_year"] - p["cost_per_paycheck_now"] >= 18)
print(f"  Not submitted and facing an increase of $18+ per paycheck: {hike}")
cheaper = sum(1 for p in people if p["step"] != "done" and p["similar_plan_cost_next_year"])
print(f"  Not submitted, and a similar plan would cost them less: {cheaper}")
