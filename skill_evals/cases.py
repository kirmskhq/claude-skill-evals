"""Loads eval cases from a cases folder (one subfolder per skill).

<cases>/<skill>/skill.yaml   checks and rubric shared by every case; optional `skill_file:` path to SKILL.md
<cases>/<skill>/<case>.yaml  one saved example input, plus case-specific checks and defects
<cases>/<skill>/answers/     recorded answers, used by --mode replay
<cases>/<skill>/defects/     broken answers that named checks must catch
<cases>/_private/checks/     gitignored: <skill>.yaml or _all.yaml with checks you do not want to publish
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class Defect:
    file: Path
    must_fail: list[str]
    note: str = ""


@dataclass
class Case:
    id: str
    skill: str
    title: str
    input: str
    checks: list[dict]
    rubric: list[dict]
    answer_file: Path | None = None
    defects: list[Defect] = field(default_factory=list)

    def recorded_answer(self) -> str:
        if not self.answer_file or not self.answer_file.exists():
            raise FileNotFoundError(f"case {self.skill}/{self.id} has no recorded answer at {self.answer_file}")
        return self.answer_file.read_text(encoding="utf-8")


def _read(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def skills(cases_dir: Path) -> list[str]:
    return sorted(p.parent.name for p in Path(cases_dir).glob("*/skill.yaml") if not p.parent.name.startswith("_"))


def skill_config(skill: str, cases_dir: Path) -> dict:
    return _read(Path(cases_dir) / skill / "skill.yaml")


def load_skill(skill: str, cases_dir: Path) -> list[Case]:
    cases_dir = Path(cases_dir)
    folder = cases_dir / skill
    if not (folder / "skill.yaml").exists():
        raise FileNotFoundError(f"no {folder / 'skill.yaml'}; run `skill-evals init {skill}` to create one")
    shared = _read(folder / "skill.yaml")
    shared_checks = list(shared.get("checks", []))
    for private in (cases_dir / "_private" / "checks" / "_all.yaml", cases_dir / "_private" / "checks" / f"{skill}.yaml"):
        if private.exists():
            shared_checks += _read(private).get("checks", [])
    out = []
    for path in sorted(folder.glob("*.yaml")):
        if path.name == "skill.yaml":
            continue
        d = _read(path)
        case_id = d.get("id") or path.stem
        checks = shared_checks + d.get("checks", [])
        ids = [c.get("id", c["type"]) for c in checks]
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        if dupes:
            raise ValueError(f"{path}: duplicate check ids {dupes}; give each check a unique id")
        out.append(Case(
            id=case_id, skill=skill, title=d.get("title", case_id), input=d["input"],
            checks=checks, rubric=shared.get("rubric", []) + d.get("rubric", []),
            answer_file=folder / d.get("answer", f"answers/{case_id}.md"),
            defects=[Defect(folder / x["file"], list(x["must_fail"]), x.get("note", "")) for x in d.get("defects", [])],
        ))
    return out
