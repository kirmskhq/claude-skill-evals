"""Command line: skill-evals {init,list,run,compare,defects,report}. Run `skill-evals <cmd> -h` for options."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import history
from .cases import load_skill, skills
from .checks import run_check
from .compare import render
from .draft import draft_checks, init_skill
from .llm import LLM, Budget
from .runner import Generator, find_skill_file, run_skill

DEFAULT_SKILL_MODEL = "claude-sonnet-5-5"  # guess at sensible defaults; override with MODEL_SKILL / MODEL_JUDGE
DEFAULT_JUDGE_MODEL = "claude-opus-5-5"


def check_defects(cases_dir: Path, skill_names: list[str]) -> list[str]:
    """Every saved defect must fail the checks it names. Returns the problems found."""
    problems = []
    for skill in skill_names:
        for case in load_skill(skill, cases_dir):
            for d in case.defects:
                text = d.file.read_text(encoding="utf-8")
                failed = {spec.get("id", spec["type"]) for spec in case.checks if not run_check(text, spec).passed}
                missed = [m for m in d.must_fail if m not in failed]
                if missed:
                    problems.append(f"{skill}/{case.id} {d.file.name}: checks {missed} did not catch the defect")
    return problems


def _models(provider: str) -> tuple[str, str]:
    claude = provider == "anthropic"
    return (os.environ.get("MODEL_SKILL") or (DEFAULT_SKILL_MODEL if claude else ""),
            os.environ.get("MODEL_JUDGE") or (DEFAULT_JUDGE_MODEL if claude else ""))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="skill-evals", description="Regression tests for AI skills and prompts.")
    ap.add_argument("--cases", type=Path, default=Path(os.environ.get("EVALS_CASES", "evals")),
                    help="folder with one subfolder per skill (default: $EVALS_CASES or ./evals)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    i = sub.add_parser("init", help="create skill.yaml and an example case for a skill")
    i.add_argument("skill")
    i.add_argument("--skill-file", type=Path, help="path to the skill's SKILL.md (or any system prompt file)")
    i.add_argument("--draft", action="store_true", help="ask the judge model to draft checks from SKILL.md")

    sub.add_parser("list", help="list skills and cases")

    def run_opts(p):
        p.add_argument("--skill", action="append", help="skill name, repeatable; default: all")
        p.add_argument("--mode", choices=["replay", "api", "command"], default="replay")
        p.add_argument("--judge", action="store_true", help="also score answers with MODEL_JUDGE")
        p.add_argument("--max-calls", type=int, default=50, help="hard cap on model calls for the whole command")
        p.add_argument("--max-tokens", type=int, default=400_000, help="hard cap on tokens for the whole command")

    r = sub.add_parser("run", help="run cases and append the result to the history")
    run_opts(r)
    r.add_argument("--label", default="", help="short note for the report, e.g. 'shorter intro rule'")
    r.add_argument("--save-answers", type=Path, help="write each answer to this folder for review")
    r.add_argument("--fail-on-regression", action="store_true", help="exit 1 if a check that passed before fails now")
    r.add_argument("--no-history", action="store_true")

    c = sub.add_parser("compare", help="run two versions of a SKILL.md on the same cases and show what changed")
    c.add_argument("skill")
    c.add_argument("before", type=Path, help="old SKILL.md")
    c.add_argument("after", type=Path, help="new SKILL.md")
    c.add_argument("--judge", action="store_true")
    c.add_argument("--mode", choices=["api", "command"], default="api")
    c.add_argument("--max-calls", type=int, default=50)
    c.add_argument("--max-tokens", type=int, default=400_000)

    sub.add_parser("defects", help="prove every check catches its saved broken answer")
    rep = sub.add_parser("report", help="write the trend report in markdown")
    rep.add_argument("--out", type=Path, help="default: next to the history file")
    args = ap.parse_args(argv)
    cases_dir: Path = args.cases

    if args.cmd == "init":
        drafted = None
        if args.draft:
            if not args.skill_file:
                ap.error("--draft needs --skill-file")
            llm = LLM.from_env()
            drafted = draft_checks(args.skill_file.read_text(encoding="utf-8"), llm=llm,
                                   model=_models(llm.provider)[1], budget=Budget(max_calls=1))
        folder = init_skill(args.skill, cases_dir, args.skill_file, drafted)
        print(f"created {folder}: edit skill.yaml, write real inputs in example.yaml, then `skill-evals run --mode api`")
        return 0

    if args.cmd == "list":
        for s in skills(cases_dir):
            for case in load_skill(s, cases_dir):
                print(f"{s}/{case.id}: {case.title} ({len(case.checks)} checks, {len(case.rubric)} rubric items, "
                      f"{len(case.defects)} defects)")
        return 0

    if args.cmd == "defects":
        problems = check_defects(cases_dir, skills(cases_dir))
        print("\n".join(problems) or "Every saved defect is caught by the checks it names.")
        return 1 if problems else 0

    if args.cmd == "report":
        hist = history.default_path(cases_dir)
        out = args.out or hist.parent / "REPORT.md"
        out.write_text(history.report(history.load(hist)), encoding="utf-8")
        print(f"wrote {out}")
        return 0

    budget = Budget(max_calls=args.max_calls, max_tokens=args.max_tokens)
    llm = LLM.from_env() if (args.mode == "api" or args.judge) else None
    skill_model, judge_model = _models(llm.provider) if llm else ("", "")
    gen = Generator(args.mode, llm=llm, model=skill_model, command=os.environ.get("SKILL_COMMAND", ""))
    if args.mode == "command" and not gen.command:
        ap.error("set SKILL_COMMAND for --mode command")
    if (args.mode == "api" and not skill_model) or (args.judge and not judge_model):
        ap.error("set MODEL_SKILL and MODEL_JUDGE for a non-Claude provider")
    jl = llm if args.judge else None

    if args.cmd == "compare":
        before = run_skill(args.skill, gen, cases_dir=cases_dir, judge_llm=jl, judge_model=judge_model, budget=budget,
                           skill_path=args.before, label="compare: before", history_path=False)
        after = run_skill(args.skill, gen, cases_dir=cases_dir, judge_llm=jl, judge_model=judge_model, budget=budget,
                          skill_path=args.after, label="compare: after", history_path=False)
        print(render(args.skill, before, after))
        print(f"model calls {budget.calls}, tokens {budget.tokens}")
        return 0

    hist = history.default_path(cases_dir)
    runs_before = history.load(hist)
    code = 0
    for skill in args.skill or skills(cases_dir):
        if args.mode != "replay" and not find_skill_file(skill, cases_dir):
            print(f"{skill}: skipped, SKILL.md not found (set SKILLS_DIR or skill_file in skill.yaml)")
            continue
        run = run_skill(skill, gen, cases_dir=cases_dir, judge_llm=jl, judge_model=judge_model, budget=budget,
                        label=args.label, history_path=False if args.no_history else hist,
                        save_answers=args.save_answers)
        judge = f", judge {run['judge_avg']:.2f}" if run["judge_avg"] is not None else ""
        print(f"{skill}: {run['checks_passed']}/{run['checks_total']} checks{judge}")
        for case in run["cases"]:
            for k in case["checks"]:
                if not k["passed"]:
                    print(f"  FAIL {case['id']}/{k['id']}: {k['detail']}")
        reg = history.regressions(run, history.previous(runs_before + [run], run))
        if reg:
            print(f"  REGRESSED: {', '.join(reg)}")
            code = 1 if args.fail_on_regression else code
    print(f"model calls {budget.calls}, tokens {budget.tokens}")
    return code


if __name__ == "__main__":
    sys.exit(main())
