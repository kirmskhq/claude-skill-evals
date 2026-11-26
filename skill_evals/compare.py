"""Before/after comparison: did an edit to SKILL.md make the skill better or worse?

Both versions answer the same cases with the same model; the checks and the judge score both.
"""
from __future__ import annotations


def diff_runs(before: dict, after: dict) -> dict:
    """Per-check changes between two runs of the same cases."""
    def index(run):
        return {(c["id"], k["id"]): k for c in run["cases"] for k in c["checks"]}

    b, a = index(before), index(after)
    fixed = sorted(f"{c}/{k}" for (c, k), v in a.items() if v["passed"] and (c, k) in b and not b[(c, k)]["passed"])
    broken = sorted(f"{c}/{k}" for (c, k), v in a.items() if not v["passed"] and (c, k) in b and b[(c, k)]["passed"])
    jb = {(c["id"], s["id"]): s["score"] for c in before["cases"] for s in c["judge"]}
    ja = {(c["id"], s["id"]): s["score"] for c in after["cases"] for s in c["judge"]}
    judge_moves = sorted((f"{c}/{r}", jb[(c, r)], ja[(c, r)]) for (c, r) in ja if (c, r) in jb and ja[(c, r)] != jb[(c, r)])
    return {"fixed": fixed, "broken": broken, "judge_moves": judge_moves}


def verdict(before: dict, after: dict, d: dict) -> str:
    if d["broken"] and not d["fixed"]:
        return "WORSE"
    if d["fixed"] and not d["broken"]:
        return "BETTER"
    if d["fixed"] or d["broken"]:
        return "MIXED"
    jb, ja = before.get("judge_avg"), after.get("judge_avg")
    if jb is not None and ja is not None and abs(ja - jb) >= 0.25:  # guess: smaller moves are judge noise
        return "BETTER" if ja > jb else "WORSE"
    return "SAME"


def render(skill: str, before: dict, after: dict) -> str:
    d = diff_runs(before, after)
    lines = [f"{skill}: {verdict(before, after, d)}",
             f"  checks  before {before['checks_passed']}/{before['checks_total']}  after {after['checks_passed']}/{after['checks_total']}"]
    if before.get("judge_avg") is not None:
        lines.append(f"  judge   before {before['judge_avg']:.2f}  after {after['judge_avg']:.2f}")
    lines += [f"  fixed   {x}" for x in d["fixed"]]
    lines += [f"  BROKEN  {x}" for x in d["broken"]]
    lines += [f"  judge   {x}: {b} -> {a}" for x, b, a in d["judge_moves"]]
    return "\n".join(lines)
