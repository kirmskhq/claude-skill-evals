import json

import yaml

from skill_evals.__main__ import main
from skill_evals.draft import draft_checks, validate
from skill_evals.llm import LLM, Budget

from .conftest import FakePost


def test_init_creates_a_runnable_skill(tmp_path, capsys):
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text("Be brief.")
    assert main(["--cases", str(tmp_path / "evals"), "init", "brief", "--skill-file", str(skill_md)]) == 0
    assert main(["--cases", str(tmp_path / "evals"), "list"]) == 0
    assert "brief/example" in capsys.readouterr().out


def test_replay_run_writes_history_and_report(tmp_path, examples, monkeypatch, capsys):
    monkeypatch.setenv("EVALS_HISTORY", str(tmp_path / "h.jsonl"))
    assert main(["--cases", str(examples), "run", "--skill", "release-notes", "--label", "demo"]) == 0
    assert main(["--cases", str(examples), "report", "--out", str(tmp_path / "R.md")]) == 0
    assert "| demo | replay |" in (tmp_path / "R.md").read_text()


def test_draft_keeps_only_valid_checks():
    assert validate([{"type": "max_words", "limit": 5}, {"type": "nope"}, {"type": "forbidden", "patterns": ["("]},
                     {"type": "max_words"}]) == [{"type": "max_words", "limit": 5}]
    answer = "```yaml\n" + yaml.safe_dump({"checks": [{"type": "max_words", "limit": 150}, {"type": "made_up"}],
                                           "rubric": [{"id": "tone", "text": "Friendly."}]}) + "```"
    d = draft_checks("Keep it under 150 words.", llm=LLM("k", post=FakePost(answer)), model="m", budget=Budget())
    assert d["checks"] == [{"type": "max_words", "limit": 150}] and d["rubric"][0]["id"] == "tone"
    json.dumps(d)
