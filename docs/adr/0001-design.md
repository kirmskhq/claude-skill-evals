# ADR 0001: Design of the first version

Date: 2026-11-26. Status: accepted.

## Decisions

1. **Cases are files, not a database.** One YAML file per example input, one markdown file per recorded answer.
   Skill authors review evals in the same pull request as the skill change.
2. **Code checks first, model judge second.** Rules that code can test (limits, banned phrases, section order)
   are deterministic checks that give the same answer every run and cost nothing. Rules that need judgement go
   to a rubric scored 1-5 by a judge model, which must differ from the model that runs the skill.
3. **Every check proves itself.** A case can list broken answers (`defects:`) with the checks that must catch
   them; `skill-evals defects` and the test suite fail if a check stops catching its defect.
4. **Any model, Claude by default.** Two small adapters: the Anthropic Messages API (default) and any
   OpenAI-compatible endpoint. `--mode command` runs any CLI, so agents with tools (for example a headless
   Claude Code run that loads the skill with its reference files) can be evaluated too.
5. **Hard budget.** Every command has caps on model calls and tokens; there are no unbounded loops.
6. **Private by default for real skills.** Skills are read from the author's machine and never copied into the
   cases folder. Private checks live in a gitignored `_private/` folder.

## Dependencies

Only `pyyaml` (case files) at runtime and `pytest` for development. HTTP uses the standard library, so there
is no provider SDK to pin. Alternative considered: `httpx` with async calls, as in `llm-evals-harness-wip`;
not needed at this scale. Risk: low; `pyyaml` is stable and widely used.

## Guesses to revisit

- Default models (`claude-sonnet-5-5` runs the skill, `claude-opus-5-5` judges).
- A judge average must move by 0.25 or more before `compare` calls it better or worse.
- Several word and sentence limits in the example cases are marked `# guess` where the skill gives no number.
