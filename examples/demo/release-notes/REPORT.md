# Skill eval report

Built by `skill-evals report` from the run history. Checks are code rules; the judge score is a second model's 1-5 rating against the rubric.

## release-notes

| Date | Label | Mode | Skill version | Checks passed | Judge avg |
|---|---|---|---|---|---|
| 2026-11-27 20:31 | v1 first draft | replay | b37d2a96 | 11/15 = 73% |  |
| 2026-11-27 20:31 | v2 rules for the reader | replay | e892399c | 15/15 = 100% (+27 pts) |  |
| 2026-11-27 20:31 | v3 tidy-up | replay | ca887adf | 14/15 = 93% (-7 pts) |  |

**Latest run:**

Regressed since the previous run: v3-0-breaking/action_needed

Failed checks:

- `v3-0-breaking` / `action_needed`: missing: ### Action needed
