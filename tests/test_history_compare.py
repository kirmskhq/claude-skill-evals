from skill_evals import history
from skill_evals.compare import diff_runs, render, verdict


def run(at, passed: dict, judge=None, mode="api", skill="s"):
    cases = [{"id": "c", "checks": [{"id": k, "passed": v, "detail": "d"} for k, v in passed.items()],
              "judge": [{"id": "r", "score": judge, "reason": "why"}] if judge else []}]
    n = sum(passed.values())
    return {"at": at, "skill": skill, "mode": mode, "label": "", "skill_version": "abc", "checks_passed": n,
            "checks_total": len(passed), "pass_rate": n / len(passed), "judge_avg": judge, "cases": cases}


def test_regressions_only_count_checks_that_passed_before():
    a = run("1", {"x": True, "y": False})
    b = run("2", {"x": False, "y": False})
    assert history.regressions(b, a) == ["c/x"]
    assert history.previous([a, b], b) is a
    assert history.previous([a, b, run("3", {"x": True}, mode="replay")], b) is a


def test_report_shows_trend_and_latest_failures():
    text = history.report([run("2026-01-01T00:00:00Z", {"x": True}, 4.0), run("2026-01-02T00:00:00Z", {"x": False}, 3.0)])
    assert "## s" in text and "(-100 pts)" in text and "(-1.00)" in text
    assert "Regressed since the previous run: c/x" in text and "scored 3" in text


def test_compare_verdicts():
    before, after = run("1", {"x": False, "y": True}), run("2", {"x": True, "y": True})
    d = diff_runs(before, after)
    assert d["fixed"] == ["c/x"] and verdict(before, after, d) == "BETTER"
    assert verdict(after, before, diff_runs(after, before)) == "WORSE"
    assert verdict(run("1", {"x": True}, 3.0), run("2", {"x": True}, 3.1), {"fixed": [], "broken": [], "judge_moves": []}) == "SAME"
    assert "BETTER" in render("s", before, after)
