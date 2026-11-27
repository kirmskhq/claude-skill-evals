"""Scaffolding for a new skill: `init` writes templates, `--draft` asks a model to propose checks from SKILL.md."""
from __future__ import annotations

import re
from pathlib import Path

import yaml

from .checks import run_check
from .llm import LLM, Budget, wrap_untrusted

TEMPLATE_SKILL = """\
# Checks and rubric shared by every case of this skill. Edit freely; see README for all check types.
{skill_file}checks:
  - {{type: no_placeholders}}
  # - {{type: max_words, limit: 300}}
  # - {{id: banned_phrases, type: forbidden, patterns: ['as an AI', 'I hope this helps']}}

rubric:
  - id: follows_skill
    text: The answer follows the instructions of the skill for this kind of request.
"""

TEMPLATE_CASE = """\
title: First example
# A real request someone would send to this skill. Avoid personal data if you publish the cases.
input: |
  Replace this with an example input.
# defects:                  # optional: broken answers that named checks must catch
#   - file: defects/example.bad.md
#     must_fail: [no_placeholders]
"""


def validate(checks: list[dict]) -> list[dict]:
    """Keeps only checks that are known types with valid parameters and regexes."""
    good = []
    for spec in checks or []:
        try:
            for p in spec.get("patterns", []):
                re.compile(p)
            run_check("probe text.", spec)
            good.append(spec)
        except Exception:  # noqa: BLE001 (a bad draft check is dropped, not fatal)
            continue
    return good


def draft_checks(skill_md: str, *, llm: LLM, model: str, budget: Budget) -> dict:
    system = (Path(__file__).parent / "prompts" / "draft_checks.md").read_text(encoding="utf-8").split("---", 2)[2].strip()
    raw = llm.chat([{"role": "system", "content": system},
                    {"role": "user", "content": wrap_untrusted(skill_md, "SKILL.md")}],
                   model=model, budget=budget, task="draft-checks", max_tokens=3000)
    m = re.search(r"```(?:ya?ml)?\s*(.*?)```", raw, re.DOTALL)
    data = yaml.safe_load(m.group(1) if m else raw) or {}
    return {"checks": validate(data.get("checks")), "rubric": [r for r in data.get("rubric") or [] if r.get("id") and r.get("text")],
            "raw": raw}


def init_skill(skill: str, cases_dir: Path, skill_file: Path | None = None, drafted: dict | None = None) -> Path:
    folder = Path(cases_dir) / skill
    if (folder / "skill.yaml").exists():
        raise FileExistsError(f"{folder / 'skill.yaml'} already exists")
    (folder / "answers").mkdir(parents=True, exist_ok=True)
    (folder / "defects").mkdir(exist_ok=True)
    rel = f"skill_file: {Path(skill_file).resolve()}\n" if skill_file else ""
    if drafted:
        text = ("# DRAFT written by a model from SKILL.md. Review every check before trusting it.\n" + rel +
                yaml.safe_dump({"checks": drafted["checks"], "rubric": drafted["rubric"]}, allow_unicode=True, sort_keys=False))
        (folder / "draft_raw.yaml.txt").write_text(drafted["raw"], encoding="utf-8")
    else:
        text = TEMPLATE_SKILL.format(skill_file=rel)
    (folder / "skill.yaml").write_text(text, encoding="utf-8")
    (folder / "example.yaml").write_text(TEMPLATE_CASE, encoding="utf-8")
    return folder
