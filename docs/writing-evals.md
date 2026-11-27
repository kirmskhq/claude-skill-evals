# Writing evals

This page covers the files in a cases folder, every check type, the rubric, defect answers, and how to keep
private rules private.

## Folder layout

```
evals/                          # --cases or $EVALS_CASES, default ./evals
  my-skill/
    skill.yaml                  # checks and rubric shared by every case; optional skill_file
    welcome-email.yaml          # one case: a saved example request
    refund-request.yaml
    answers/welcome-email.md    # recorded answer for --mode replay (optional)
    defects/welcome-email.bad.md  # a broken answer that named checks must catch (optional)
  _private/checks/              # gitignored: _all.yaml or my-skill.yaml
  results/history.jsonl         # one line per run; results/REPORT.md is built from it
```

## skill.yaml

```yaml
skill_file: ../../skills/my-skill/SKILL.md   # optional; else $SKILLS_DIR/<skill>/SKILL.md
checks:
  - {type: max_words, limit: 200}
  - id: no_filler                             # give every check a unique id
    type: forbidden
    patterns: ['I hope this helps', 'as an AI']
rubric:
  - id: answers_the_question
    text: The first sentence answers what the user asked.
```

## A case

```yaml
title: Customer asks for a refund after 40 days
input: |
  The full request, exactly as a user would send it to the skill.
checks:                         # optional, added to the shared checks
  - id: mentions_policy
    type: required
    patterns: ['30 days']
rubric:                         # optional, added to the shared rubric
  - id: polite_refusal
    text: The answer says no politely and offers an alternative.
defects:                        # optional
  - file: defects/refund.bad.md
    must_fail: [mentions_policy, no_filler]
    note: promises a refund and starts with filler
answer: answers/refund.md       # optional; default answers/<case id>.md
```

## Check types

Every check takes an optional `id` (default: its type). Ids must be unique within a case.

| Type | Parameters | Passes when |
|---|---|---|
| `max_words` | `limit` | the answer has at most `limit` words |
| `min_words` | `limit` | the answer has at least `limit` words |
| `paragraphs` | `min`, `max` | the number of paragraphs (blank-line blocks, headings excluded) is in range |
| `forbidden` | `patterns`, `ignore_case` (default true) | no regex matches; the detail lists what was found |
| `required` | `patterns`, `ignore_case` | every regex matches |
| `sections_in_order` | `sections`, `all_required` (default true) | the section names appear in this order; with `all_required: false` some may be absent |
| `first_line_not` | `patterns` | the first line after an optional greeting matches none of the patterns |
| `no_placeholders` | none | no `[Company]`, `<name>`, `{x}`, `XXX` or `TODO` is left |
| `max_sentence_words` | `limit` | no sentence is longer than `limit` words |
| `paragraph_starts_differ` | none | no two neighbouring paragraphs open with the same word |
| `language` | `lang` (`en` or `ru`), `min_share` | the share of letters in that alphabet is at least `min_share` |
| `amounts_labeled` | `labels` | every sentence with a ruble amount says gross or net (Russian answers) |

Patterns are Python regular expressions. In YAML, single quotes keep backslashes as they are: `'\bCI\b'`.

### Adding a check type

A check is a function in [`skill_evals/checks.py`](../skill_evals/checks.py) that returns `CheckResult(id, passed, detail)`:

```python
@check("ends_with_question")
def ends_with_question(text, *, id="ends_with_question"):
    last = text.strip()[-1:] if text.strip() else ""
    return CheckResult(id, last == "?", f"ends with {last!r}")
```

Add a test for it in `tests/test_checks.py`; a test fails if any registered check type has none.

## Rules that code cannot check

Put them in the rubric, one plain sentence each. The judge scores every item from 1 to 5 and quotes the words
behind a score below 4. An item the judge skips counts as 1, so a lazy judge cannot raise the average. The judge
prompt lives in [`skill_evals/prompts/judge.md`](../skill_evals/prompts/judge.md) with a `version:` that is saved
with each run, so scores from different judge prompts are never mixed up silently.

## Defects: testing the tests

A check that never fails proves nothing. For each important rule, save one answer that breaks it and list the
checks that must catch it. `skill-evals defects` and the test suite fail when a check stops catching its defect,
for example after someone loosens a regex.

## Private rules

Some rules name things you do not want to publish, such as people, employers or confidential topics. Put them in
`_private/checks/<skill>.yaml` (or `_all.yaml` for every skill) with the same `checks:` format. The folder is in
`.gitignore`, and its checks are merged into every case of that skill at run time.

For runs on private skills, set `EVALS_HISTORY` to a path outside the repository too: the history stores what each
failed check found, which can quote the answer.
