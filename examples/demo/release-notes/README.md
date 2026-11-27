# Demo: three versions of one skill

This folder shows what skill-evals is for, without an API key. The `release-notes` skill went through three versions:

| Version | What changed in SKILL.md |
|---|---|
| [v1](v1/SKILL.md) | First draft: four short rules. |
| [v2](../../skills/release-notes/SKILL.md) | Added rules for the reader: no ticket numbers, no internal changes, a word limit. |
| [v3](v3/SKILL.md) | A "tidy-up" that dropped the rule about breaking changes. |

The answers in `v1/answers/`, `v3/answers/` and `../../cases/release-notes/answers/` (v2) are hand-written
illustrations of what each version tends to produce. They are not real model output. With an API key,
`--mode api` produces real answers instead.

Run the comparison and the trend yourself from the repo root:

```bash
skill-evals --cases examples/cases compare release-notes \
  examples/demo/release-notes/v1/SKILL.md examples/skills/release-notes/SKILL.md \
  --mode replay --answers-before examples/demo/release-notes/v1/answers \
  --answers-after examples/cases/release-notes/answers

bash examples/demo/release-notes/run_trend.sh   # writes REPORT.md next to this file
```

The [report](REPORT.md) shows v2 fixing four checks and v3 quietly breaking one: the answer to a breaking release
no longer tells users what to do.
