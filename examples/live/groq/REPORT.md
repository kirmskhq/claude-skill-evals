# Skill eval report

Built by `skill-evals report` from the run history. Checks are code rules; the judge score is a second model's 1-5 rating against the rubric.

## release-notes

| Date | Label | Mode | Skill version | Checks passed | Judge avg |
|---|---|---|---|---|---|
| 2026-11-27 21:32 | v1 first draft | api | b37d2a96 | 14/15 = 93% | 4.00 |
| 2026-11-27 21:32 | v2 rules for the reader | api | e892399c | 15/15 = 100% (+7 pts) | 5.00 (+1.00) |
| 2026-11-27 21:32 | v3 tidy-up | api | ca887adf | 14/15 = 93% (-7 pts) | 5.00 (=) |

**Latest run:**

Regressed since the previous run: v3-0-breaking/action_needed

Failed checks:

- `v3-0-breaking` / `action_needed`: missing: ### Action needed
