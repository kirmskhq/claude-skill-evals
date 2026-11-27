# Changelog

## Unreleased

Fixes found by the first live runs (NeuralDeep and Groq free tiers):

- Requests send a `skill-evals/<version>` User-Agent; Groq refused urllib's default one with HTTP 403.
- Retries wait as long as the server's `Retry-After` says (free tiers send it on 429), up to 90 seconds.
- The judge is asked once more when its reply is not valid JSON; the judge prompt is now version 2.
- A rubric item the judge scores twice counts once, with the lower score.
- The `release-notes` rubric says internal changes are meant to be left out, after the judge marked answers down for that.
- First published live run: `examples/live/groq`.

## 0.1.0 (2026-11-27)

First public version.

- Rule checks in YAML (12 types), an LLM judge with a rubric on a different model, defect answers that prove each check.
- Three ways to get answers: `replay` (recorded), `api` (Claude by default, or any OpenAI-compatible endpoint), `command` (any CLI).
- `run` keeps a history; `report` writes a markdown trend; `--fail-on-regression` for CI.
- `compare` runs two versions of a SKILL.md, or two sets of recorded answers, and prints BETTER, WORSE, MIXED or SAME.
- `init` scaffolds a skill; `--draft` asks a model to draft checks from SKILL.md.
- Examples: a public `release-notes` skill with an offline three-version demo, and four job-search skills.
