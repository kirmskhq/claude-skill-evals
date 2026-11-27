#!/usr/bin/env bash
# Replays the three versions of the release-notes skill and writes the trend report. No API key needed.
set -euo pipefail
cd "$(dirname "$0")/../../.."
D=examples/demo/release-notes
export EVALS_HISTORY=$D/history.jsonl
rm -f "$EVALS_HISTORY"
skill-evals --cases examples/cases run --skill release-notes --label "v1 first draft" \
  --skill-file $D/v1/SKILL.md --answers $D/v1/answers
skill-evals --cases examples/cases run --skill release-notes --label "v2 rules for the reader" \
  --skill-file examples/skills/release-notes/SKILL.md --answers examples/cases/release-notes/answers
skill-evals --cases examples/cases run --skill release-notes --label "v3 tidy-up" \
  --skill-file $D/v3/SKILL.md --answers $D/v3/answers || true
skill-evals --cases examples/cases report --out $D/REPORT.md
