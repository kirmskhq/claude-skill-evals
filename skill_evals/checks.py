"""Deterministic checks: plain code, no model, same answer every run.

Each check takes the skill's answer as text plus its params from the case file and
returns a CheckResult. Register a new check with @check("name").
"""
from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from itertools import pairwise

WORD_RE = re.compile(r"[\w’'-]+", re.UNICODE)
CYRILLIC_RE = re.compile(r"[а-яё]", re.IGNORECASE)
LATIN_RE = re.compile(r"[a-z]", re.IGNORECASE)
PLACEHOLDER_RE = re.compile(r"\[[^\]\n]{1,40}\]|<[^>\n]{1,40}>|\bX{3,}\b|\bTODO\b|\{[^}\n]{1,40}\}")


@dataclass
class CheckResult:
    id: str
    passed: bool
    detail: str = ""


CHECKS: dict[str, Callable[..., CheckResult]] = {}


def check(name: str):
    def deco(fn):
        CHECKS[name] = fn
        return fn
    return deco


def words(text: str) -> list[str]:
    return WORD_RE.findall(text)


def paragraphs(text: str) -> list[str]:
    """Blocks of text separated by blank lines, without markdown headings."""
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text.strip()) if b.strip()]
    return [b for b in blocks if not b.startswith("#")]


def sentences(text: str) -> list[str]:
    flat = re.sub(r"\s+", " ", text)
    return [s.strip() for s in re.split(r"(?<=[.!?…])\s+", flat) if s.strip()]


@check("max_words")
def max_words(text, *, limit: int, id="max_words"):
    n = len(words(text))
    return CheckResult(id, n <= limit, f"{n} words, limit {limit}")


@check("min_words")
def min_words(text, *, limit: int, id="min_words"):
    n = len(words(text))
    return CheckResult(id, n >= limit, f"{n} words, minimum {limit}")


@check("paragraphs")
def paragraph_count(text, *, min: int = 1, max: int = 99, id="paragraphs"):
    n = len(paragraphs(text))
    return CheckResult(id, min <= n <= max, f"{n} paragraphs, allowed {min}-{max}")


@check("forbidden")
def forbidden(text, *, patterns: list[str], id="forbidden", ignore_case: bool = True):
    flags = re.IGNORECASE if ignore_case else 0
    hits = []
    for p in patterns:
        m = re.search(p, text, flags)
        if m:
            hits.append(m.group(0))
    return CheckResult(id, not hits, "found: " + "; ".join(hits) if hits else "none found")


@check("required")
def required(text, *, patterns: list[str], id="required", ignore_case: bool = True):
    flags = re.IGNORECASE if ignore_case else 0
    missing = [p for p in patterns if not re.search(p, text, flags)]
    return CheckResult(id, not missing, "missing: " + "; ".join(missing) if missing else "all present")


@check("sections_in_order")
def sections_in_order(text, *, sections: list[str], all_required: bool = True, id="sections_in_order"):
    """Section names appear in the given order (case-insensitive).

    all_required=False lets a section be left out, but those present must still be in order.
    """
    low, pos, missing = text.lower(), -1, []
    for s in sections:
        i = low.find(s.lower(), pos + 1)
        if i < 0:
            if all_required or s.lower() in low:  # absent is fine only when optional; present but earlier is not
                missing.append(s)
        else:
            pos = i
    return CheckResult(id, not missing, "missing or out of order: " + "; ".join(missing) if missing else "ok")


GREETING_RE = re.compile(r"^\s*(здравствуйте|добрый день|hello|hi|dear)\b[^.\n]{0,40}[!,.]?\s*$", re.IGNORECASE)


@check("first_line_not")
def first_line_not(text, *, patterns: list[str], id="first_line_not"):
    """The first line after an optional greeting must not match any pattern."""
    lines = [ln for ln in text.strip().splitlines() if ln.strip() and not GREETING_RE.match(ln)]
    first = lines[0] if lines else ""
    hit = next((p for p in patterns if re.search(p, first, re.IGNORECASE)), None)
    return CheckResult(id, hit is None, f"first line matches {hit!r}" if hit else "ok")


@check("no_placeholders")
def no_placeholders(text, *, id="no_placeholders"):
    m = PLACEHOLDER_RE.search(text)
    return CheckResult(id, m is None, f"placeholder: {m.group(0)}" if m else "none")


@check("max_sentence_words")
def max_sentence_words(text, *, limit: int, id="max_sentence_words"):
    longest = max((len(words(s)) for s in sentences(text)), default=0)
    return CheckResult(id, longest <= limit, f"longest sentence {longest} words, limit {limit}")


@check("paragraph_starts_differ")
def paragraph_starts_differ(text, *, id="paragraph_starts_differ"):
    """Neighbouring paragraphs must not open with the same word."""
    firsts = [(words(p) or [""])[0].lower() for p in paragraphs(text)]
    same = [f"{i + 1}-{i + 2} '{a}'" for i, (a, b) in enumerate(pairwise(firsts)) if a and a == b]
    return CheckResult(id, not same, "same opening word in paragraphs " + ", ".join(same) if same else "ok")


@check("language")
def language(text, *, lang: str, min_share: float = 0.9, id="language"):
    """Share of letters in the expected alphabet ("ru" = Cyrillic, "en" = Latin)."""
    cyr, lat = len(CYRILLIC_RE.findall(text)), len(LATIN_RE.findall(text))
    total = cyr + lat or 1
    share = (cyr if lang == "ru" else lat) / total
    return CheckResult(id, share >= min_share, f"{share:.0%} {lang} letters, minimum {min_share:.0%}")


AMOUNT_RE = re.compile(r"\d[\d\s]*(?:[.,]\d+)?\s*(?:тыс\.?\s*|млн\s*)?(?:руб\.?|рублей|рубля)", re.IGNORECASE)


@check("amounts_labeled")
def amounts_labeled(text, *, labels: list[str] = ("гросс", "до вычета", "на руки"), id="amounts_labeled"):
    """Every sentence with a ruble amount must say whether it is gross or net."""
    bad = [s[:80] for s in sentences(text) if AMOUNT_RE.search(s) and not any(lb in s.lower() for lb in labels)]
    return CheckResult(id, not bad, "unlabeled amount: " + " | ".join(bad) if bad else "ok")


def run_check(text: str, spec: dict) -> CheckResult:
    spec = dict(spec)
    kind = spec.pop("type")
    if kind not in CHECKS:
        raise ValueError(f"unknown check type {kind!r}; known: {', '.join(sorted(CHECKS))}")
    spec.setdefault("id", kind)
    return CHECKS[kind](text, **spec)
