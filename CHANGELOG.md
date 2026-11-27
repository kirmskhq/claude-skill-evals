# Changelog

## 0.1.0 (2026-11-27)

First public version.

- Rule checks in YAML (12 types), an LLM judge with a rubric on a different model, defect answers that prove each check.
- Three ways to get answers: `replay` (recorded), `api` (Claude by default, or any OpenAI-compatible endpoint), `command` (any CLI).
- `run` keeps a history; `report` writes a markdown trend; `--fail-on-regression` for CI.
- `compare` runs two versions of a SKILL.md, or two sets of recorded answers, and prints BETTER, WORSE, MIXED or SAME.
- `init` scaffolds a skill; `--draft` asks a model to draft checks from SKILL.md.
- Examples: a public `release-notes` skill with an offline three-version demo, and four job-search skills.
