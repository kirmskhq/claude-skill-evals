"""History of runs (one JSON line per run) and the markdown trend report built from it."""
from __future__ import annotations

import json
import os
from pathlib import Path


def default_path(cases_dir: Path) -> Path:
    """EVALS_HISTORY if set, else <cases>/results/history.jsonl next to the cases it measures."""
    return Path(os.environ.get("EVALS_HISTORY") or Path(cases_dir) / "results" / "history.jsonl")


def append(run: dict, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(run, ensure_ascii=False) + "\n")


def load(path: Path) -> list[dict]:
    path = Path(path)
    if not path.exists():
        return []
    return [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def previous(runs: list[dict], run: dict) -> dict | None:
    """The run before `run` (in file order) for the same skill and mode."""
    idx = next((i for i, r in enumerate(runs) if r is run), len(runs))
    same = [r for r in runs[:idx] if r["skill"] == run["skill"] and r["mode"] == run["mode"]]
    return same[-1] if same else None


def regressions(run: dict, prev: dict | None) -> list[str]:
    """Checks that passed in the previous run and fail now, as 'case/check'."""
    if not prev:
        return []
    before = {(c["id"], k["id"]) for c in prev["cases"] for k in c["checks"] if k["passed"]}
    return [f"{c['id']}/{k['id']}" for c in run["cases"] for k in c["checks"]
            if not k["passed"] and (c["id"], k["id"]) in before]


def _fmt_delta(now, before, pct=False):
    if now is None or before is None:
        return ""
    d = now - before
    if abs(d) < 1e-9:
        return " (=)"
    return f" ({d * 100:+.0f} pts)" if pct else f" ({d:+.2f})"


def report(runs: list[dict], last: int = 8) -> str:
    lines = ["# Skill eval report", "",
             "Built by `skill-evals report` from the run history. "
             "Checks are code rules; the judge score is a second model's 1-5 rating against the rubric.", ""]
    for skill in sorted({r["skill"] for r in runs}):
        sr = [r for r in runs if r["skill"] == skill][-last:]
        lines += [f"## {skill}", "", "| Date | Label | Mode | Skill version | Checks passed | Judge avg |", "|---|---|---|---|---|---|"]
        prev = None
        for r in sr:
            p = prev if prev and prev["mode"] == r["mode"] else None
            rate = f"{r['checks_passed']}/{r['checks_total']} = {r['pass_rate']:.0%}{_fmt_delta(r['pass_rate'], p and p['pass_rate'], True)}"
            judge = "" if r["judge_avg"] is None else f"{r['judge_avg']:.2f}{_fmt_delta(r['judge_avg'], p and p['judge_avg'])}"
            lines.append(f"| {r['at'][:16].replace('T', ' ')} | {r.get('label') or ''} | {r['mode']} | {r['skill_version'] or 'n/a'} | {rate} | {judge} |")
            prev = r
        latest = sr[-1]
        failed = [f"- `{c['id']}` / `{k['id']}`: {k['detail']}" for c in latest["cases"] for k in c["checks"] if not k["passed"]]
        low = [f"- `{c['id']}` / `{s['id']}` scored {s['score']}: {s['reason']}"
               for c in latest["cases"] for s in c["judge"] if s["score"] <= 3]
        reg = regressions(latest, previous(runs, latest))
        lines += ["", "**Latest run:**", ""]
        lines += [f"Regressed since the previous run: {', '.join(reg)}", ""] if reg else []
        lines += (["Failed checks:", ""] + failed + [""]) if failed else ["All checks passed.", ""]
        lines += (["Low judge scores:", ""] + low + [""]) if low else []
    return "\n".join(lines).rstrip() + "\n"
