# Contributing

Thanks for helping. Issues and pull requests are welcome.

## Set up

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]" ruff
pytest -q && ruff check .
skill-evals --cases examples/cases defects
```

All tests run offline. No API key is needed, and tests must never call a real model: pass a fake `post`
function to `LLM`, as `tests/conftest.py` does.

## Rules of the house

- **Test first.** New behaviour starts as a test.
- **A new check type comes with a test** in `tests/test_checks.py` and a row in [docs/writing-evals.md](docs/writing-evals.md).
- **A new example rule comes with a defect**: a broken answer in `defects/` that the rule must catch.
- **Prompts are versioned.** If you change the meaning of `skill_evals/prompts/*.md`, raise its `version:`.
- **No new runtime dependency without a short ADR** in `docs/adr/` (why, alternatives, risk).
- **No secrets and no personal data** in cases, answers or history. Use `_private/` for rules you cannot publish.
- **Every model call goes through `skill_evals/llm.py`** and its `Budget`. There are no unbounded loops.
