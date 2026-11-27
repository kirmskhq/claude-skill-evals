"""The offline demo in examples/demo must keep telling the truth: v1 -> v2 is better, v2 -> v3 is worse."""
from skill_evals import history
from skill_evals.__main__ import main
from skill_evals.compare import diff_runs, verdict
from skill_evals.runner import Generator, run_skill

DEMO = "examples/demo/release-notes"


def replay(examples, answers):
    return run_skill("release-notes", Generator("replay", answers_dir=examples.parent.parent / answers),
                     cases_dir=examples, history_path=False)


def test_v2_fixes_v1_and_v3_breaks_v2(examples):
    v1, v2, v3 = replay(examples, f"{DEMO}/v1/answers"), replay(examples, "examples/cases/release-notes/answers"), \
        replay(examples, f"{DEMO}/v3/answers")
    assert verdict(v1, v2, diff_runs(v1, v2)) == "BETTER"
    d = diff_runs(v2, v3)
    assert verdict(v2, v3, d) == "WORSE" and d["broken"] == ["v3-0-breaking/action_needed"]


def test_trend_flags_the_regression(examples, tmp_path, monkeypatch):
    root = examples.parent.parent
    monkeypatch.setenv("EVALS_HISTORY", str(tmp_path / "h.jsonl"))
    for label, skill_file, answers in [("v1", f"{DEMO}/v1/SKILL.md", f"{DEMO}/v1/answers"),
                                       ("v2", "examples/skills/release-notes/SKILL.md", "examples/cases/release-notes/answers"),
                                       ("v3", f"{DEMO}/v3/SKILL.md", f"{DEMO}/v3/answers")]:
        code = main(["--cases", str(examples), "run", "--skill", "release-notes", "--label", label,
                     "--skill-file", str(root / skill_file), "--answers", str(root / answers), "--fail-on-regression"])
        assert code == (1 if label == "v3" else 0)
    runs = history.load(tmp_path / "h.jsonl")
    assert len({r["skill_version"] for r in runs}) == 3
    assert "Regressed since the previous run: v3-0-breaking/action_needed" in history.report(runs)


def test_compare_cli_in_replay_mode(examples, capsys):
    root = examples.parent.parent
    main(["--cases", str(examples), "compare", "release-notes", str(root / f"{DEMO}/v1/SKILL.md"),
          str(root / "examples/skills/release-notes/SKILL.md"), "--mode", "replay",
          "--answers-before", str(root / f"{DEMO}/v1/answers"),
          "--answers-after", str(root / "examples/cases/release-notes/answers")])
    assert "release-notes: BETTER" in capsys.readouterr().out
