# Open Enrollment Nudges

Reminders that help employees finish open enrollment, built on what shopping and learning apps know about getting people to act, without the pressure tactics.

Built by Miriam Frost, product manager. My own project. All employee data is made up.

## The idea

eBay and Depop are very good at getting people to act before a deadline. Open enrollment is very bad at it. I screenshotted a day of eBay and Depop notifications on my own phone and sorted every tactic into two piles:

- **Keep:** real money, a real deadline, picking up where you left off, two clear choices.
- **Never:** urgency stronger than the real deadline, "act fast" with no date, late-night sends, high volume, comparing you to others, scarcity.

Example from my phone: a Depop notification said "You've got 24 hours to buy." The same offer in the app said "Expires in 13d 17hr."

The "Never" pile became the rules this project checks every message against.

**Read the case study: [CASE_STUDY.md](CASE_STUDY.md)**

## What it does

1. **Funnel:** 500 made-up employees, 4 days before the deadline. Where are they stuck? (`funnel.py`, free)
2. **Risk:** who is most likely to miss the deadline. Scored in code, so it's explainable.
3. **Strategy:** one idea per message, picked by where the person is: offer help if they're stuck, lead with real money if their cost is going up, "one step left" if they're on the review page.
4. **Timing:** weekdays at 9 AM or 12 PM only. Never 8 PM to 8 AM. No more than 3 reminders per person in total.
5. **Draft:** Claude writes the message in the employee's language, using only their real numbers.
6. **Check, two layers:** hard rules in code (banned phrases, invented numbers, wrong dates, quiet hours, the cap), then a cheaper model for judgment calls (guilt, condescension, subtle pressure). A message that fails gets one rewrite with the reasons.
7. **Red team:** 14 known-bad and 6 known-good messages test whether the checker itself works.

## Run it

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...
python funnel.py          # where people stall (free)
python nudges.py E001     # one employee, end to end
python run_eval.py        # 25 employees + red team, about 50 cents
```

## Results

Final run: 21 messages drafted. 16 passed every rule after one rewrite, and all 21 were judged helpful. The red team caught 14 of 14 bad messages and wrongly flagged 0 of 6 good ones. About 50 cents.

The first version assumed passive enrollment and that every plan would be offered again. Both would have cost employees their coverage. Read what changed in the case study: [CASE_STUDY.md](CASE_STUDY.md)
