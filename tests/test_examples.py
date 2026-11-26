"""The example cases are a test suite of their own: recorded answers pass, saved defects get caught."""
import pytest

from skill_evals.__main__ import check_defects
from skill_evals.cases import load_skill, skills
from skill_evals.runner import Generator, run_skill


def test_examples_include_a_public_skill_and_the_job_search_skills(examples):
    assert {"release-notes", "cover-letter-ru", "vacancy-evaluation-ru", "role-profile-ru", "cv-writing-en"} <= set(
        skills(examples))


def test_every_saved_defect_is_caught(examples):
    assert check_defects(examples, skills(examples)) == []


def test_every_skill_has_at_least_one_defect(examples):
    for s in skills(examples):
        assert any(c.defects for c in load_skill(s, examples)), f"{s} has no defect case proving its checks work"


@pytest.mark.parametrize("skill", ["release-notes", "cover-letter-ru", "vacancy-evaluation-ru", "role-profile-ru",
                                   "cv-writing-en"])
def test_recorded_answers_pass_all_checks(examples, skill):
    run = run_skill(skill, Generator("replay"), cases_dir=examples, history_path=False)
    failed = [f"{c['id']}/{k['id']}: {k['detail']}" for c in run["cases"] for k in c["checks"] if not k["passed"]]
    assert failed == []


def test_private_checks_are_merged(tmp_path, examples):
    import shutil
    shutil.copytree(examples / "release-notes", tmp_path / "release-notes")
    (tmp_path / "release-notes" / "skill.yaml").write_text(
        (examples / "release-notes" / "skill.yaml").read_text().replace("../../skills", str(examples.parent / "skills")))
    (tmp_path / "_private" / "checks").mkdir(parents=True)
    (tmp_path / "_private" / "checks" / "_all.yaml").write_text(
        "checks:\n  - {id: secret_word, type: forbidden, patterns: ['dark mode']}\n")
    run = run_skill("release-notes", Generator("replay"), cases_dir=tmp_path, history_path=False)
    assert run["checks_passed"] == run["checks_total"] - 1
    assert "_private" not in skills(tmp_path)


def test_duplicate_check_ids_are_rejected(tmp_path):
    (tmp_path / "s").mkdir()
    (tmp_path / "s" / "skill.yaml").write_text("checks:\n  - {type: no_placeholders}\n")
    (tmp_path / "s" / "a.yaml").write_text("input: x\nchecks:\n  - {type: no_placeholders}\n")
    with pytest.raises(ValueError, match="duplicate"):
        load_skill("s", tmp_path)
