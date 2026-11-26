[![tests](https://github.com/kirmskhq/claude-skill-evals/actions/workflows/tests.yml/badge.svg)](https://github.com/kirmskhq/claude-skill-evals/actions/workflows/tests.yml) [![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

# skill-evals

**skill-evals tells you whether an edit to your AI skill made its answers better or worse.**

A skill is a written instruction for a model: a Claude `SKILL.md`, a custom GPT's instructions, a system prompt.
You keep changing it, and every change can quietly break something that used to work. skill-evals runs your skill on
a few saved example requests, checks every answer against your own rules, and keeps a history, so a regression shows
up the day you make it, not weeks later in a bad answer.

It works with Claude by default and with any other model through an OpenAI-compatible API or any command-line tool.

## What you get

- **Rule checks in plain YAML.** Word limits, banned phrases, required sections in order, a fixed closing line,
  answer language, sentence length, leftover placeholders. They run in milliseconds and cost nothing.
- **An LLM judge for the rest.** Rules that need judgement ("the opening gives a reason to invite the candidate")
  go into a rubric. A second model scores each item from 1 to 5 and quotes the words behind a low score. The judge
  must be a different model from the one that runs the skill.
- **Before and after in one command.** `skill-evals compare my-skill old/SKILL.md new/SKILL.md` runs both versions
  on the same cases and prints `BETTER`, `WORSE`, `MIXED` or `SAME`, with every check that got fixed or broken.
- **History and a trend report.** Every run is a line in `history.jsonl`; `skill-evals report` turns it into a
  markdown table per skill, with changes against the previous run and the latest failures.
- **Checks that prove themselves.** Each case can store broken answers and name the checks that must catch them.
  If a check stops catching its defect, the suite fails. A check nobody tested is a check you cannot trust.
- **A draft from your skill.** `skill-evals init my-skill --skill-file SKILL.md --draft` asks a model to turn the
  testable rules in your skill into checks and the rest into a rubric. You review it before trusting it.
- **Guard rails.** A hard cap on model calls and tokens for every command, skill answers passed to the judge as
  untrusted data, and a gitignored `_private/` folder for checks you do not want to publish.

## Quick start

```bash
pip install -e ".[dev]"
pytest -q                                              # 41 offline tests, no API key
skill-evals --cases examples/cases list                # 5 example skills, 7 cases
skill-evals --cases examples/cases defects             # every saved broken answer is caught
skill-evals --cases examples/cases run                 # replay recorded answers through the checks
skill-evals --cases examples/cases report              # writes examples/cases/results/REPORT.md
```

A live run of the bundled public skill, on Claude:

```bash
cp .env.example .env && set -a && . ./.env && set +a  # add LLM_API_KEY
skill-evals --cases examples/cases run --skill release-notes --mode api --judge --label "baseline"
```

## Your own skill in five minutes

```bash
skill-evals init my-skill --skill-file ~/.claude/skills/my-skill/SKILL.md     # add --draft for model-drafted checks
# 1. Put a real request into evals/my-skill/example.yaml (add more cases as files next to it)
# 2. Edit the checks in evals/my-skill/skill.yaml
skill-evals run --mode api --judge --label "before my edit"
# edit SKILL.md, then:
skill-evals run --mode api --judge --label "shorter intro rule" --fail-on-regression
skill-evals report
```

A case is one small YAML file:

```yaml
title: A normal release with a fix and an internal change
input: |
  Write release notes for these merged PRs:
  - feat: export reports to CSV (#412)
  - chore: bump eslint to v9 (#416)
checks:                       # added to the checks shared in skill.yaml
  - id: no_internal_changes
    type: forbidden
    patterns: ['bump', 'dependenc']
defects:                      # broken answers that these checks must catch
  - file: defects/v2-4.leaks.md
    must_fail: [no_internal_changes]
```

Check types: `max_words`, `min_words`, `paragraphs`, `forbidden`, `required`, `sections_in_order`,
`first_line_not`, `no_placeholders`, `max_sentence_words`, `paragraph_starts_differ`, `language`,
`amounts_labeled`. Adding one is a ten-line function in [`skill_evals/checks.py`](skill_evals/checks.py).

## Three ways to get an answer

| Mode | What runs | Use it for |
|---|---|---|
| `replay` | recorded answers in `answers/` | CI, checking your checks, offline demos |
| `api` | `SKILL.md` as the system prompt, the case as the user message | quick runs on Claude or any OpenAI-compatible model |
| `command` | any CLI you set in `SKILL_COMMAND`, with the case on stdin | agents with tools and reference files, other harnesses |

Models and providers are set in `.env`: `LLM_PROVIDER=anthropic` (default) or `openai` for OpenAI, OpenRouter,
LiteLLM, Ollama or vLLM via `LLM_BASE_URL`. `MODEL_SKILL` runs the skill and `MODEL_JUDGE` grades it.

`api` mode sends only `SKILL.md`. A skill that relies on its reference files or on tools gives a fuller answer in
`command` mode, for example through a headless agent CLI (guess: `SKILL_COMMAND="claude -p"` with the skill
installed; not tested in this version).

## Examples

[`examples/cases/`](examples/cases/) holds five skills:

- **release-notes**, a small public skill that ships in [`examples/skills/`](examples/skills/release-notes/SKILL.md),
  so anyone can run a live eval end to end.
- **cover-letter-ru, vacancy-evaluation-ru, role-profile-ru, cv-writing-en**, the author's own job-search skills.
  Each check quotes the rule it comes from. The skills themselves stay private; the vacancies, companies and
  answers in the cases are invented, and checks that would reveal personal data live in `_private/`.

[`examples/cases/results/REPORT.md`](examples/cases/results/REPORT.md) is the report from the first run, on the
recorded answers.

## How it is built

```
case YAML ──► get answer (replay | api | command) ──► rule checks ──► judge (optional, another model)
                                                                          │
                          history.jsonl ◄──── one line per run ◄──────────┘ ──► report.md / compare
```

Standard library plus `pyyaml`; no provider SDK. Design decisions and guesses to revisit are in
[ADR 0001](docs/adr/0001-design.md). The ideas of a judge on a different model, defect cases that prove each check
and a hard budget come from the author's earlier
[llm-evals-harness](https://github.com/kirmskhq/llm-evals-harness-wip).

## Status

First version, 26 November 2026. The checks, history, report, `compare` and `init` are covered by offline tests.
Live runs through both adapters are tested against a fake network only; the first real run is still to come.

## Next

- Run several samples per case and report the spread, since one answer per case hides flaky behaviour.
- A pairwise judge for `compare` ("which answer follows the skill better?"), which is steadier than two 1-5 scores.
- A GitHub Action that comments the `compare` result on a pull request that changes a `SKILL.md`.
