import pytest

from skill_evals.checks import CHECKS, paragraphs, run_check


def ok(text, **spec):
    return run_check(text, spec).passed


def test_word_limits():
    assert ok("one two three", type="max_words", limit=3)
    assert not ok("one two three four", type="max_words", limit=3)
    assert not ok("one two", type="min_words", limit=3)


def test_paragraphs_ignore_headings():
    text = "# Title\n\nFirst.\n\nSecond."
    assert len(paragraphs(text)) == 2
    assert ok(text, type="paragraphs", min=2, max=2)


def test_forbidden_and_required_report_what_they_found():
    r = run_check("Мы работаем быстро, а не медленно.", {"type": "forbidden", "id": "x", "patterns": [r",\s*а не\b"]})
    assert not r.passed and "а не" in r.detail
    assert ok("Готов обсудить ваши задачи.", type="required", patterns=["Готов обсудить"])
    assert not ok("Hello", type="forbidden", patterns=["hello"])
    assert ok("Hello", type="forbidden", patterns=["hello"], ignore_case=False)


def test_sections_in_order():
    text = "Вердикт ... Что за роль ... Зарплата"
    assert ok(text, type="sections_in_order", sections=["Вердикт", "Что за роль", "Зарплата"])
    assert not ok(text, type="sections_in_order", sections=["Что за роль", "Вердикт"])
    assert not ok(text, type="sections_in_order", sections=["Вердикт", "Гэпы"])


def test_optional_sections_still_keep_order():
    spec = {"type": "sections_in_order", "sections": ["### New", "### Fixed"], "all_required": False}
    assert ok("### Fixed\n- x", **spec)
    assert not ok("### Fixed\n- x\n### New\n- y", **spec)


def test_first_line_skips_greeting():
    spec = {"type": "first_line_not", "patterns": ["откликаюсь"]}
    assert not ok("Здравствуйте!\n\nОткликаюсь на вакансию.", **spec)
    assert ok("Здравствуйте!\n\nЯ внедрил ИИ-решения.", **spec)


def test_placeholders():
    assert not ok("Dear [Company name], hi", type="no_placeholders")
    assert not ok("Привет, {имя}", type="no_placeholders")
    assert ok("Plain text, no gaps.", type="no_placeholders")


def test_sentence_length():
    assert not ok("This sentence has exactly seven words in it.", type="max_sentence_words", limit=6)
    assert ok("Short one. Another short one.", type="max_sentence_words", limit=6)


def test_paragraph_starts_differ():
    assert not ok("Я сделал.\n\nЯ внедрил.", type="paragraph_starts_differ")
    assert ok("Я сделал.\n\nВнедрил.", type="paragraph_starts_differ")


def test_language():
    assert ok("Это русский текст", type="language", lang="ru")
    assert not ok("This is English", type="language", lang="ru")
    assert not ok("Mostly English with слово", type="language", lang="en", min_share=0.98)


def test_amounts_labeled():
    assert not ok("Платят 300 000 рублей.", type="amounts_labeled")
    assert ok("Платят 300 000 рублей до вычета налогов.", type="amounts_labeled")
    assert ok("Это 250 тыс. руб. на руки.", type="amounts_labeled")


def test_unknown_check_type_is_an_error():
    with pytest.raises(ValueError, match="unknown check type"):
        run_check("x", {"type": "nope"})


def test_every_check_has_a_test_here():
    import inspect
    src = inspect.getsource(inspect.getmodule(test_language))
    assert [name for name in CHECKS if f'"{name}"' not in src and f"type=\"{name}\"" not in src] == []
