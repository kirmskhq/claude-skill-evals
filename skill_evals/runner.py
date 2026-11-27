"""Runs a skill's cases, scores the answers and appends the run to the history file."""
from __future__ import annotations

import hashlib
import os
import shlex
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from . import history
from .cases import Case, load_skill, skill_config
from .checks import run_check
from .judge import judge, load_prompt
from .llm import LLM, Budget, LLMError


def find_skill_file(skill: str, cases_dir: Path, skills_dir: str | None = None) -> Path | None:
    """SKILL.md for a skill: `skill_file:` in skill.yaml (relative to it), else <SKILLS_DIR>/<skill>/SKILL.md."""
    configured = skill_config(skill, cases_dir).get("skill_file")
    if configured:
        p = (Path(cases_dir) / skill / configured).resolve()
        return p if p.exists() else None
    base = skills_dir or os.environ.get("SKILLS_DIR", "")
    p = Path(base).expanduser() / skill / "SKILL.md" if base else None
    return p if p and p.exists() else None


def short_hash(*texts: str) -> str:
    h = hashlib.sha256()
    for t in texts:
        h.update(t.encode())
    return h.hexdigest()[:8]


@dataclass
class Generator:
    """Gets the skill's answer for one case.

    replay   reads the recorded answer from answers/ (offline, free, for CI and for checking the checks)
    api      sends SKILL.md as the system prompt and the case input as the user message to MODEL_SKILL
    command  runs SKILL_COMMAND with the case input on stdin; {skill} and {skill_file} are filled in
    """

    mode: str
    llm: LLM | None = None
    model: str = ""
    command: str = ""
    answers_dir: Path | None = None  # replay answers from <answers_dir>/<case>.md instead of the case's answers/

    def answer(self, case: Case, skill_path: Path | None, budget: Budget) -> str:
        task = f"{self.mode}:{case.skill}/{case.id}"
        if self.mode == "replay":
            if self.answers_dir:
                path = Path(self.answers_dir) / f"{case.id}.md"
                if not path.exists():
                    raise FileNotFoundError(f"no recorded answer {path}")
                return path.read_text(encoding="utf-8")
            return case.recorded_answer()
        if self.mode == "api":
            if not skill_path:
                raise LLMError(f"SKILL.md for {case.skill} not found: set SKILLS_DIR or skill_file in skill.yaml")
            messages = [{"role": "system", "content": skill_path.read_text(encoding="utf-8")},
                        {"role": "user", "content": case.input}]
            return self.llm.chat(messages, model=self.model, budget=budget, task=task, max_tokens=4000, temperature=0.2)
        if self.mode == "command":
            budget.before(task)
            filled = self.command.replace("{skill}", case.skill).replace("{skill_file}", str(skill_path or ""))
            done = subprocess.run(shlex.split(filled), input=case.input, capture_output=True, text=True,
                                  timeout=900, check=False)
            if done.returncode != 0:
                raise LLMError(f"SKILL_COMMAND failed ({done.returncode}): {done.stderr[:300]}")
            budget.after(task, "command", 0)
            return done.stdout.strip()
        raise ValueError(f"unknown mode {self.mode!r}")


def score_case(case: Case, answer: str) -> list[dict]:
    return [vars(run_check(answer, spec)) for spec in case.checks]


def run_skill(skill: str, gen: Generator, *, cases_dir: Path, judge_llm: LLM | None = None, judge_model: str = "",
              budget: Budget | None = None, skill_path: Path | None = None, label: str = "",
              history_path: Path | None | bool = None, save_answers: Path | None = None) -> dict:
    """Runs every case of one skill. `skill_path` overrides the SKILL.md found for the skill (used by compare)."""
    if judge_llm and gen.mode == "api" and judge_model == gen.model:
        raise ValueError("MODEL_JUDGE must differ from MODEL_SKILL so a model does not grade its own answers")
    budget = budget or Budget()
    skill_path = skill_path or find_skill_file(skill, cases_dir)
    results, answers = [], []
    for case in load_skill(skill, cases_dir):
        answer = gen.answer(case, skill_path, budget)
        answers.append(answer)
        if save_answers:
            out = Path(save_answers) / skill / f"{case.id}.md"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(answer, encoding="utf-8")
        checks = score_case(case, answer)
        scores = judge(case, answer, llm=judge_llm, model=judge_model, budget=budget) if judge_llm else []
        results.append({
            "id": case.id,
            "checks": checks, "checks_passed": sum(c["passed"] for c in checks), "checks_total": len(checks),
            "judge": scores, "judge_avg": round(sum(s["score"] for s in scores) / len(scores), 2) if scores else None,
        })
    passed = sum(r["checks_passed"] for r in results)
    total = sum(r["checks_total"] for r in results)
    judged = [r["judge_avg"] for r in results if r["judge_avg"] is not None]
    run = {
        "at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "skill": skill,
        "label": label,
        "mode": gen.mode,
        "model": gen.model if gen.mode == "api" else gen.mode,
        "judge_model": judge_model if judge_llm else None,
        "judge_prompt_version": load_prompt()[1] if judge_llm else None,
        "skill_version": short_hash(skill_path.read_text(encoding="utf-8")) if skill_path else None,
        "answers_hash": short_hash(*answers),
        "checks_passed": passed,
        "checks_total": total,
        "pass_rate": round(passed / total, 3) if total else None,
        "judge_avg": round(sum(judged) / len(judged), 2) if judged else None,
        "calls": budget.calls,
        "tokens": budget.tokens,
        "cases": results,
    }
    if history_path is not False:
        history.append(run, history_path or history.default_path(cases_dir))
    return run
