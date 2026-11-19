# Open Enrollment Nudges: real urgency, never fake urgency

Miriam Frost, November 2026. My own project, designed and tested end to end. All employee data is made up.

## The problem

Shopping apps are very good at getting people to act before a deadline. Open enrollment is very bad at it. In this scenario, 4 days before the deadline, 236 of 500 employees (47%) haven't submitted.

In active enrollment, that matters. If an employee submits nothing, they have no medical, dental or vision coverage next year.

I wanted to borrow what works from consumer apps without borrowing the pressure.

## The research: one day of my own phone

I screenshotted a day of eBay and Depop notifications and sorted every tactic.

- eBay sent 7 notifications. Depop sent 8.
- eBay sent one at 1:29 AM. Depop sent two after 11 PM.
- A Depop notification said "You've got 24 hours to buy." The same offer in the app said "Expires in 13d 17hr."
- The useful ones were specific: "Price reduced by $14.20. Now $127.80." "Lowered the price of an item in your bag."

| Keep | Never |
| --- | --- |
| Real money | Urgency stronger than the real deadline |
| The real deadline, exactly | "Act fast" with no date |
| Pick up where you left off | Sends between 8 PM and 8 AM |
| Two clear choices | 7 or 8 messages a day |
| | Comparing you to coworkers |
| | Scarcity and competition |

The "Never" column became the rules.

## What I built

- **Funnel:** where 500 employees are stuck. 72 haven't logged in. 48 looked at plans and chose nothing. 43 chose medical and stopped. 31 are stuck adding dependents. 42 are on the review page.
- **Risk score in code:** how likely each person is to miss the deadline, based on their step and how long they've been idle.
- **One strategy per person:** offer help if they're stuck, lead with real money if their cost is going up, "one step left" if they're on the review page.
- **Timing:** weekdays at 9 AM or 12 PM only. A cap of 3 reminders per person for the whole window. At the cap, no more messages: they're flagged for a personal HR call.
- **Claude drafts each message** in the employee's language (English or Spanish), using only their real numbers.
- **Two-layer checker.** Code catches hard rules: banned phrases, numbers not in the facts, wrong dates, quiet hours, the cap. A cheaper model catches judgment calls: guilt, condescension, subtle pressure. A failed message gets one rewrite with the reasons.
- **Red team:** 14 deliberately bad messages and 6 good ones, to test the checker itself.

## What the first version got wrong, and how I knew

The first version passed its own tests and was still wrong. Twice.

**1. It assumed passive enrollment.** Messages said "Keep my plan" and "your plan stays the same." In active enrollment, an employee who believes that does nothing and loses coverage. My "no fear" rule would also have blocked the one warning they most needed.

Fix: every message must state, once and calmly, that no selection means no coverage next year. Saying the plan carries over is now blocked in code, in English and Spanish.

**2. It assumed every plan would be offered again.** "Re-select my current plan" only works if the plan still exists. Plan lineups change every year.

Fix: a next-year plan lineup. In this scenario HMO Plus is discontinued, affecting 59 of the 236 employees who haven't submitted. Those employees are told first that their plan is ending and they need to choose a new one. The writer never sees a next-year price for a discontinued plan, and "re-select" is blocked for them.

Neither is something a generic AI builder would know. Both came from working in HR and payroll.

## Results

| | Run 2 | Run 3 (final) |
| --- | --- | --- |
| Messages drafted | 19 | 21 |
| Passed on the first draft | 3 | **11** |
| Passed after one rewrite | 4 | **16** |
| Judged helpful | 19 | **21** |
| Bad messages caught (red team) | 14 of 14 | **14 of 14** |
| Good messages wrongly flagged | 3 of 6 | **0 of 6** |
| Sent to HR instead (reminder cap) | 4 | 4 |
| Cost of the full test | $0.66 | $0.50 |

**Run 2 failed mostly because of my own checks.** Messages said "no medical, dental or vision coverage." My check only knew "no coverage." I fixed three of these bugs.

**The checker also caught mistakes in my own answer key.** It flagged 3 of my "good" examples, and it was right. I had written "about 4 minutes," which isn't a fact the system has. My Spanish example said the employee was on the review page when they weren't.

**What still fails in Run 3:**
- The writer wrote "choose your 2025 plan" in 5 first drafts. It was never told the plan year. A new code check caught every one.
- The model checker twice flagged the required no-coverage sentence as fear, even though the instructions say it's required. Judgment calls by a smaller model aren't fully consistent.

## Where I drew the line

**Social proof** ("80% of your coworkers have enrolled") is off in notifications. It may get people to finish, but it doesn't help them choose a better plan. In HR, people can't mute the app.

**Tracking.** A separate teardown of Duolingo showed apps fingerprinting your network to tell home from work. An employer should never do that. This system uses only enrollment activity: what step you're on and how long you've been idle.

## Limits

- Made-up employees and plans. One scenario, one deadline.
- One run per version. Results vary between runs.
- Costs are estimates from token counts, not billing.
- Messages are drafted and checked, not sent.

## What I'd do next

- Give the writer the plan year. That alone fixes 5 of the remaining failures.
- Use the stronger model for judgment checks on the required notice, or check that sentence in code only.
- Test the passive-enrollment version side by side.
- Measure the real outcome: did people submit, and did they pick a better plan, not just any plan.
