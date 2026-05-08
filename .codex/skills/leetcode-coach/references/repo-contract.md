# LeetCode Coach Repo Contract

This contract keeps the repo safe for long-term study. The machine-readable metadata in each problem note is the source of truth; list files and summaries are views.

## Required Layout

```text
.codex/skills/leetcode-coach/SKILL.md
.codex/skills/leetcode-coach/scripts/study.py
.codex/skills/leetcode-coach/references/repo-contract.md
lists/<list-name>.md
problems/<range>/<id>-<slug>/note.md
problems/<range>/<id>-<slug>/solution.py
study/profile.json
templates/problem-note.md
templates/pattern-note.md
knowledge/mistake-taxonomy.md
```

`workspace/leetcode/` is a transient VS Code LeetCode plugin workspace and should stay ignored.

## Problem Metadata

Every `note.md` must start with a JSON block:

```md
<!-- leetcode-meta
{
  "id": 1,
  "slug": "two-sum",
  "title": "Two Sum",
  "difficulty": "Easy",
  "tags": ["array", "hash-table"],
  "lists": ["hot100"],
  "status": "Todo",
  "mastery": "new",
  "last_practiced": null,
  "next_review": null,
  "mistake_tags": [],
  "stats": {
    "attempts": 0,
    "hint_level_reached": 0,
    "solve_minutes": null,
    "first_try_ac": null,
    "judge_failures": [],
    "recall_score": null,
    "teach_back_done": false,
    "last_mode": null
  },
  "links": {
    "leetcode": "https://leetcode.com/problems/two-sum/",
    "leetcode_cn": "https://leetcode.cn/problems/two-sum/"
  }
}
-->
```

Required keys:

```text
id, slug, title, difficulty, tags, lists, status, mastery,
last_practiced, next_review, mistake_tags
```

Recommended keys:

```text
stats, links
```

Allowed `status` values:

```text
Todo, Doing, AC, Review
```

Allowed `mastery` values:

```text
new, shaky, ok, solid
```

`mastery=solid` requires `stats.teach_back_done=true`, unless the user explicitly overrides this for a special reason.

## Problem Note Sections

Each problem note should include:

```md
## Restatement
## Key Observations
## Approach
## Complexity
## Teach Back
## Mistakes
## Pattern
## Review Log
```

`Teach Back` is the interview-readiness check. It should cover invariant, state/data-structure choice, complexity, edge cases, and when the pattern does not apply.

## List Files

List files such as `lists/hot100.md` are views. Slugs are parsed from backticks:

```md
- `two-sum` — Two Sum
```

Do not store progress in list files. Store progress only in problem metadata.

## Profile

`study/profile.json` may contain:

```json
{
  "language": "python3",
  "communication_language": "zh-CN",
  "active_list": "hot100",
  "daily_target": {"review": 2, "new": 2},
  "hint_policy": "progressive",
  "review_intervals_days": [1, 7, 30],
  "leetcode_endpoint": "leetcode-cn",
  "problem_url_template": "https://leetcode.cn/problems/{slug}/",
  "training_modes": ["blind-solve", "guided-solve", "redo-from-memory", "debug-drill", "pattern-contrast"],
  "solid_requires_teach_back": true
}
```

Keep personal settings in `study/profile.json`. A public template should provide `study/profile.example.json` instead of overwriting a user's existing profile.

## Solution Archiving

Archived solution modes:

- `leetcode`: keep the plugin-style code snippet as-is.
- `standalone`: extract code between `@lc code=start/end` and add obvious missing imports such as `typing.List`.

Prefer standalone mode for review and local tests.

## Mistake Tags

Use standardized mistake tags from `knowledge/mistake-taxonomy.md`. The helper can summarize recent mistakes and use repeated mistakes to shorten review intervals.

## Validation

Run:

```bash
python3 .codex/skills/leetcode-coach/scripts/study.py check
python3 .codex/skills/leetcode-coach/scripts/study.py check --strict
```

Strict mode enforces the new evidence-based schema more aggressively.
