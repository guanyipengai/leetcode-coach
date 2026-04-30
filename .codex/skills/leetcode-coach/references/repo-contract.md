# Repository Asset Contract

This contract is for the LeetCode Coach agent. Keep strict rules small and stable. Human-owned learning notes should stay flexible unless the helper script depends on a field or format.

## Strict Contracts

### Problem Notes

Each tracked problem lives at:

```text
problems/<bucket>/<frontend-id>-<slug>/note.md
```

Example:

```text
problems/0000-0999/0001-two-sum/note.md
```

Each `note.md` must start with one JSON metadata comment:

```md
<!-- leetcode-meta
{
  "id": 1,
  "slug": "two-sum",
  "title": "Two Sum",
  "difficulty": "Easy",
  "tags": ["array", "hash-table"],
  "lists": ["example"],
  "status": "Todo",
  "mastery": "new",
  "last_practiced": null,
  "next_review": null,
  "mistake_tags": []
}
-->
```

Required fields:

- `id`: LeetCode frontend ID as an integer.
- `slug`: LeetCode URL slug.
- `title`: display title from MCP metadata.
- `difficulty`: LeetCode difficulty string.
- `tags`: array of tag slugs or readable tag names.
- `lists`: array of study list names without `.md`.
- `status`: one of `Todo`, `Doing`, `AC`, `Review`.
- `mastery`: one of `new`, `shaky`, `ok`, `solid`.
- `last_practiced`: `YYYY-MM-DD` or `null`.
- `next_review`: `YYYY-MM-DD` or `null`.
- `mistake_tags`: array of short mistake labels.

Do not store full LeetCode problem statements in `note.md`. Store the learner's own restatement, observations, mistakes, and review notes.

### Archived Solutions

Each initialized problem may have:

```text
problems/<bucket>/<frontend-id>-<slug>/solution.py
```

The coach archives accepted code from the VS Code LeetCode plugin workspace after the learner reports AC. The plugin source file must contain `@lc code=start` and `@lc code=end` markers for automatic extraction.

### Study Lists

Study lists live in:

```text
lists/<list-name>.md
```

The helper parses LeetCode slugs from backticks. Use one backticked slug per bullet:

```md
# Hash Table Practice

- `two-sum`
- `group-anagrams`
```

List files are views. They do not store progress. Progress remains in each problem's `note.md` metadata.

### Profile

`study/profile.json` is the coach's compact preference and routing config.

Expected keys:

- `language`: default solution language, usually `python3`.
- `communication_language`: default coaching language, usually `zh-CN`.
- `active_list`: list name under `lists/` without `.md`.
- `daily_target.new_problems`: target number of new problems per session.
- `daily_target.review_problems`: target number of review problems per session.
- `hint_policy`: expected coach hint style, usually `progressive`.
- `review_intervals_days`: default spaced repetition intervals.

Keep this JSON small. Do not store per-problem progress here.

### Templates

Templates live under `templates/` and are used by the bundled helper.

- `problem-note.md` must keep a valid `leetcode-meta` JSON comment; the helper replaces it when initializing a problem.
- `problem-note.md` should keep a `# Problem Title` heading and `https://leetcode.com/problems/` placeholder so the helper can render title and link.
- `session.md` must keep the literal `YYYY-MM-DD` placeholder so the helper can render a dated session file.
- `solution.py` is only the initial archived-solution placeholder. VS Code LeetCode plugin files are the submit workspace.

## Flexible Conventions

### Goals

`study/goals.md` is user-owned planning text. The coach may read it to understand long-term goals, current focus, constraints, or preferences. Do not require a strict schema.

### Sessions

Daily logs live in:

```text
study/sessions/YYYY-MM-DD.md
```

The coach may append concise entries after a study session. Keep entries useful for future review: problems touched, result, key takeaway, and suggested next step.

### Pattern Notes

Reusable pattern notes live in:

```text
knowledge/patterns/<pattern-name>.md
```

Recommended sections:

- `When To Use`
- `Core Idea`
- `Template`
- `Common Mistakes`
- `Problems`

Pattern notes are human learning assets. They should be clear and reusable, but they are not strict machine state.

## Agent Rules

- Prefer the bundled helper for state queries and updates.
- Read this contract before creating or modifying repository assets, fixing validation errors, changing templates, or explaining asset formats.
- Keep strict machine-readable data small and predictable.
- Keep human-owned notes concise, personal, and useful.
- Never commit cookies, session tokens, CSRF tokens, or copied full LeetCode statements.
