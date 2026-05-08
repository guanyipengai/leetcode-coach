# LeetCode Coach Workflow

## Daily Start

```bash
python3 .codex/skills/leetcode-coach/scripts/study.py status --brief
python3 .codex/skills/leetcode-coach/scripts/study.py plan-day
```

Coach in this order:

1. Due reviews.
2. Existing `Doing` / `Review` problems.
3. New active-list problems.
4. Uninitialized active-list problems after MCP metadata lookup.

## New Problem

```bash
python3 .codex/skills/leetcode-coach/scripts/study.py init-problem \
  --id 49 \
  --slug group-anagrams \
  --title "Group Anagrams" \
  --difficulty Medium \
  --tags "array,hash-table,string,sorting" \
  --list hot100
```

Use `guided-solve` by default unless the user asks for interview simulation.

## Accepted Submission

```bash
python3 .codex/skills/leetcode-coach/scripts/study.py archive-solution \
  --slug group-anagrams \
  --from-plugin \
  --mode standalone \
  --with-tests
```

Then require teach-back. Only after that:

```bash
python3 .codex/skills/leetcode-coach/scripts/study.py finish \
  --slug group-anagrams \
  --status AC \
  --mastery ok \
  --mode guided-solve \
  --quality 4 \
  --hint-level 1 \
  --solve-minutes 22 \
  --first-try-ac false \
  --judge-failures "WA" \
  --mistake-tags "duplicate-handling" \
  --teach-back true
```

## Review Problem

Use `redo-from-memory`:

1. Ask for invariant.
2. Ask for approach and complexity.
3. Ask for the easiest edge case to miss.
4. Let the user code.
5. Finish with updated quality and mistakes.

## Migration

Preview first:

```bash
python3 .codex/skills/leetcode-coach/scripts/study.py migrate
```

Write changes:

```bash
python3 .codex/skills/leetcode-coach/scripts/study.py migrate --write
```

Validate:

```bash
python3 .codex/skills/leetcode-coach/scripts/study.py check
```
