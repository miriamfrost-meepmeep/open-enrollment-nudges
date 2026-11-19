"""Make 500 made-up employees mid-way through open enrollment. No real data.

    python generate_data.py      # writes data/employees.json (already included)
"""
import json
import random
from pathlib import Path

random.seed(2026)
FIRST = ["Ana", "Ben", "Carla", "Dev", "Elena", "Frank", "Grace", "Hector", "Imani", "Jamal",
         "Kim", "Luis", "Maya", "Nate", "Olivia", "Priya", "Quinn", "Rosa", "Sam", "Tasha",
         "Uri", "Vera", "Wes", "Ximena", "Yusuf", "Zoe", "Marisol", "Andre", "Lena", "Omar"]
PLANS = [("PPO 500", "PPO 1000"), ("PPO 1000", "HDHP 2500"), ("HMO Plus", "HMO Basic"),
         ("HDHP 2500", None), ("PPO 500", "HMO Plus")]
# Where each employee is today, 4 days before the deadline. Order = the enrollment flow.
STEPS = [("done", .52), ("not_started", .14), ("viewed_plans", .10), ("chose_medical", .09),
         ("stuck_dependents", .07), ("review", .08)]


def pick_step():
    r, total = random.random(), 0
    for step, p in STEPS:
        total += p
        if r <= total:
            return step
    return "done"


people = []
for n in range(1, 501):
    current, alt = random.choice(PLANS)
    cost = random.randrange(60, 221)
    increase = random.choice([0, 0, 6, 12, 18, 24, 31, 38, 44])
    step = pick_step()
    p = {
        "id": f"E{n:03d}",
        "first_name": random.choice(FIRST),
        "language": "es" if random.random() < .12 else "en",
        "step": step,
        "days_since_active": 0 if step == "done" else random.choice([0, 1, 2, 3, 5, 8, 11, 14]),
        "attempts_on_step": random.choice([3, 4, 5]) if step == "stuck_dependents" else random.choice([0, 1]),
        "has_dependents": step == "stuck_dependents" or random.random() < .45,
        "current_plan": current,
        "cost_per_paycheck_now": cost,
        "cost_per_paycheck_next_year": cost + increase,
        "similar_plan": alt,
        "similar_plan_cost_next_year": (cost + increase - random.choice([9, 14, 22, 27])) if alt and increase >= 18 else None,
        "preferred_channel": random.choice(["email", "email", "text", "app"]),
        "reminders_sent": random.choice([0, 1, 1, 2, 3]) if step != "done" else 0,
    }
    people.append(p)

Path(__file__).resolve().parent.joinpath("data", "employees.json").write_text(json.dumps(people, indent=1))
print(f"{len(people)} employees written")
