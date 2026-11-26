import json

import pytest

from skill_evals import history
from skill_evals.cases import load_skill
from skill_evals.judge import judge
from skill_evals.llm import LLM, Budget
from skill_evals.runner import Generator, run_skill

from .conftest import FakePost


def test_judge_clamps_scores_and_fails_skipped_items(examples):
    case = load_skill("release-notes", examples)[0]
    answer = json.dumps({"scores": [{"id": "user_effect", "score": 9, "reason": "ok"}, {"id": "invented", "score": 5}]})
    scores = judge(case, "notes", llm=LLM("k", post=FakePost(answer)), model="judge", budget=Budget())
    assert {s["id"]: s["score"] for s in scores} == {"user_effect": 5, "complete": 1}


def test_api_mode_sends_skill_as_system_prompt_and_judge_is_another_model(examples, tmp_path):
    good = (examples / "release-notes" / "answers" / "v2-4.md").read_text()
    verdict = json.dumps({"scores": [{"id": "user_effect", "score": 4}, {"id": "complete", "score": 5}]})
    post = FakePost(good, verdict, good, verdict)
    llm = LLM("k", post=post)
    run = run_skill("release-notes", Generator("api", llm=llm, model="skill-model"), cases_dir=examples,
                    judge_llm=llm, judge_model="judge-model", history_path=tmp_path / "h.jsonl")
    first = post.requests[0]["payload"]
    assert "Release notes for end users" in first["system"] and first["model"] == "skill-model"
    assert post.requests[1]["payload"]["model"] == "judge-model"
    assert run["skill_version"] and run["judge_avg"] == 4.5 and run["calls"] == 4
    assert len(history.load(tmp_path / "h.jsonl")) == 1


def test_same_model_cannot_judge_itself(examples):
    llm = LLM("k", post=FakePost())
    with pytest.raises(ValueError, match="differ"):
        run_skill("release-notes", Generator("api", llm=llm, model="m"), cases_dir=examples, judge_llm=llm,
                  judge_model="m", history_path=False)


def test_command_mode_runs_any_cli(examples):
    gen = Generator("command", command="python3 -c \"import sys; print(open('{skill_file}').read()[:3])\"")
    run = run_skill("release-notes", gen, cases_dir=examples, history_path=False)
    assert run["mode"] == "command" and run["checks_passed"] < run["checks_total"]


def test_save_answers(examples, tmp_path):
    run_skill("release-notes", Generator("replay"), cases_dir=examples, history_path=False, save_answers=tmp_path)
    assert (tmp_path / "release-notes" / "v2-4.md").exists()
