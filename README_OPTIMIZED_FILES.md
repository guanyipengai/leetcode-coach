# Optimized LeetCode Coach Files

This package is an overlay for the existing `leetcode-coach` repository.

It intentionally does **not** include your personal progress data. It also provides `study/profile.example.json` instead of overwriting `study/profile.json`.

## Install

From the parent directory of your repo:

```bash
unzip leetcode-coach-optimized-files.zip
rsync -av leetcode-coach-optimized-files/ leetcode-coach/
cd leetcode-coach
```

If you do not already have a profile:

```bash
cp study/profile.example.json study/profile.json
```

If you already have `study/profile.json`, merge the new fields manually instead of replacing your file.

## Migrate Existing Notes

Preview:

```bash
python3 .codex/skills/leetcode-coach/scripts/study.py migrate
```

Write:

```bash
python3 .codex/skills/leetcode-coach/scripts/study.py migrate --write
```

Validate:

```bash
make check
```

## What Changed

- Evidence-based metadata: attempts, hint level, solve time, first-try AC, judge failures, recall score, and teach-back status.
- `No teach-back, no solid` rule.
- Adaptive review scheduling based on quality, hints, judge failures, and repeated mistakes.
- Standardized mistake taxonomy.
- Standalone solution archiving from the VS Code LeetCode plugin workspace.
- Optional test skeleton creation.
- CI and Makefile checks.
- Better problem, pattern, and session templates.

## Important Commands

```bash
python3 .codex/skills/leetcode-coach/scripts/study.py status --brief
python3 .codex/skills/leetcode-coach/scripts/study.py plan-day
python3 .codex/skills/leetcode-coach/scripts/study.py next
python3 .codex/skills/leetcode-coach/scripts/study.py due
python3 .codex/skills/leetcode-coach/scripts/study.py mistakes
python3 .codex/skills/leetcode-coach/scripts/study.py archive-solution --slug <slug> --from-plugin --mode standalone --with-tests
python3 .codex/skills/leetcode-coach/scripts/study.py finish --slug <slug> --status AC --mastery ok --quality 4 --hint-level 1 --teach-back true
```
