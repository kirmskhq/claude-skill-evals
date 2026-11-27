# Live run: release-notes on Groq

A real run of the three `release-notes` versions from the [demo](../../demo/release-notes/), on 2026-11-27.

| | |
|---|---|
| Endpoint | Groq free tier, OpenAI-compatible (`LLM_PROVIDER=openai`) |
| Skill model | `qwen/qwen3.8-27b` |
| Judge model | `openai/gpt-oss-120b` |
| Calls | 12 for the three runs, 8 for the compare, about 13,000 tokens |

- [run.log](run.log): the console output of every command.
- [REPORT.md](REPORT.md): the trend report built from [history.jsonl](history.jsonl).
- `v1/`, `v2/`, `v3/`: the answers each version produced.

What it shows: the rule checks found the v3 regression (no "Action needed" section after a breaking change), while
the judge scored v2 and v3 the same, 5.00. One sample per case, so a re-run can differ.

To reproduce, from the repo root:

```bash
export LLM_PROVIDER=openai LLM_BASE_URL=https://api.groq.com/openai/v1 LLM_API_KEY=...   # your own key
export MODEL_SKILL=qwen/qwen3.8-27b MODEL_JUDGE=openai/gpt-oss-120b EVALS_HISTORY=/tmp/history.jsonl
skill-evals --cases examples/cases compare release-notes \
  examples/skills/release-notes/SKILL.md examples/demo/release-notes/v3/SKILL.md --mode api --judge
```
