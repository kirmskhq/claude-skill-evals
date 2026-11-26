---
name: release-notes
description: Turn a list of merged changes into short release notes for end users. Use when someone pastes commit messages or PR titles and asks for release notes or a changelog entry.
---

# Release notes for end users

The reader is a user of the product, not a developer. They want to know what changed for them.

1. Start with a heading `## What's new` and nothing before it.
2. Group items under `### New`, `### Improved` and `### Fixed`, in that order. Leave out an empty group.
3. One bullet per change, one sentence each, starting with a verb in the past tense ("Added", "Fixed").
4. Describe the effect for the user. Never mention ticket numbers, commit hashes, branch names or file paths.
5. Leave out internal changes (refactoring, CI, dependency bumps, tests) entirely.
6. Keep the whole text under 150 words.
7. If a change is a breaking change, end with a `### Action needed` group that says what the user must do.
