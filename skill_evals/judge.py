"""LLM judge: a second model scores each answer against the skill's rubric (1-5 per item).

The judge must be a different model from the one that ran the skill, so a model does not grade itself.
"""
from __future__ import annotations

from pathlib import Path

from .cases import Case
from .llm import LLM, Budget, LLMError, extract_json, wrap_untrusted

PROMPT_PATH = Path(__file__).parent / "prompts" / "judge.md"


def load_prompt() -> tuple[str, str]:
    text = PROMPT_PATH.read_text(encoding="utf-8")
    _, front, body = text.split("---", 2)
    version = next(ln.split(":", 1)[1].strip() for ln in front.splitlines() if ln.startswith("version:"))
    return body.strip(), version


def judge(case: Case, answer: str, *, llm: LLM, model: str, budget: Budget) -> list[dict]:
    if not case.rubric:
        return []
    system, _ = load_prompt()
    rubric = "\n".join(f"- {r['id']}: {r['text']}" for r in case.rubric)
    user = (
        f"Rubric:\n{rubric}\n\n"
        f"Task the assistant received:\n{wrap_untrusted(case.input, 'case-input')}\n\n"
        f"Answer to grade:\n{wrap_untrusted(answer, 'skill-answer')}"
    )
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    task = f"judge:{case.skill}/{case.id}"
    raw = llm.chat(messages, model=model, budget=budget, task=task, max_tokens=1500)
    try:
        data = extract_json(raw)
    except ValueError as e:
        # open models often break JSON with an unescaped quote; ask once more, then give up loudly
        messages += [{"role": "assistant", "content": raw},
                     {"role": "user", "content": f"Your reply was not valid JSON ({e}). Send the same scores as "
                                                 "valid JSON only, with single quotes inside the reasons."}]
        raw = llm.chat(messages, model=model, budget=budget, task=task + ":retry", max_tokens=1500)
        try:
            data = extract_json(raw)
        except ValueError as e2:
            raise LLMError(f"judge reply for {case.skill}/{case.id} is not valid JSON twice: {e2}") from e2
    known = {r["id"] for r in case.rubric}
    best: dict[str, dict] = {}
    for s in data.get("scores", []):
        if s.get("id") in known:
            score = max(1, min(5, int(s.get("score", 1))))
            # a judge that scores one item twice must not count it twice; the lower score stands
            if s["id"] not in best or score < best[s["id"]]["score"]:
                best[s["id"]] = {"id": s["id"], "score": score, "reason": str(s.get("reason", ""))[:400]}
    scores = list(best.values())
    missing = known - set(best)
    # an item the judge skipped counts as a fail, so a lazy judge cannot raise the average
    scores += [{"id": m, "score": 1, "reason": "judge did not score this item"} for m in sorted(missing)]
    return scores
