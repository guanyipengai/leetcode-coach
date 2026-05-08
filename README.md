# LeetCode Coach

LeetCode Coach is a Codex-assisted practice workspace for planning sessions, solving in VS Code, reviewing mistakes, and turning accepted solutions into durable notes.

You solve with the VS Code LeetCode extension. Codex runs the bundled `leetcode-coach` skill, fetches problem metadata through LeetCode MCP when needed, gives progressive hints, archives accepted code, and schedules spaced review from evidence.

![LeetCode Coach architecture](assets/architecture.png)

## What This Repo Optimizes

- Progressive coaching instead of answer dumping.
- Daily plans that put due reviews before new problems.
- Evidence-based metadata: attempts, hint level, solve time, first-try AC, judge failures, recall score, teach-back status, and training mode.
- Adaptive review scheduling based on mastery, quality, hint usage, judge failures, and repeated mistake tags.
- `No teach-back, no solid`: a problem should not be marked `solid` until you can explain the invariant, complexity, edge cases, and pattern boundary.
- VS Code LeetCode submit flow with accepted solutions archived back into `problems/.../solution.py`.
- Standard mistake taxonomy and pattern notes for reusable learning.
- Local and CI checks through `make check`.

## Quick Start

1. Clone the repository and open it in VS Code.
2. Install and sign in to the VS Code LeetCode extension.
3. Configure LeetCode MCP in Codex if it is not already available.
4. Check the workspace:

```bash
make check
```

5. Start a Codex session in this repository:

```text
用 leetcode-coach，今天开始 LeetCode 训练。
```

The coach should recover status, build a plan, initialize the selected problem when needed, guide the solve, review code or judge failures, archive accepted code, require teach-back, and schedule the next review.

## Daily Workflow

1. Recover state:

```bash
python3 .codex/skills/leetcode-coach/scripts/study.py status --brief
python3 .codex/skills/leetcode-coach/scripts/study.py plan-day
```

2. Practice in this order: due reviews, existing `Doing` or `Review` problems, then active-list new problems.
3. Solve and submit through the VS Code LeetCode extension under `workspace/leetcode/`.
4. Ask Codex for progressive hints, edge-case checks, complexity review, or code review.
5. After AC, archive the accepted plugin file:

```bash
python3 .codex/skills/leetcode-coach/scripts/study.py archive-solution --slug <slug> --from-plugin --mode standalone --with-tests
```

6. Finish with evidence and schedule review:

```bash
python3 .codex/skills/leetcode-coach/scripts/study.py finish \
  --slug <slug> \
  --status AC \
  --mastery ok \
  --mode guided-solve \
  --quality 4 \
  --hint-level 1 \
  --solve-minutes 18 \
  --first-try-ac true \
  --teach-back true
```

## Training Modes

- `blind-solve`: no hints unless requested, close to interview conditions.
- `guided-solve`: progressive hints for new topics.
- `redo-from-memory`: explain invariant, approach, complexity, and edge cases before coding.
- `debug-drill`: start from failing code and isolate the smallest counterexample or fix direction.
- `pattern-contrast`: compare nearby patterns and force a decision boundary.

## Repository Structure

```text
.codex/skills/leetcode-coach/  # Project skill, references, and helper script
.github/workflows/             # CI validation
.vscode/settings.json          # VS Code LeetCode project settings
docs/                          # Demo and troubleshooting notes
knowledge/mistake-taxonomy.md  # Standard mistake tags
knowledge/patterns/            # Reusable pattern notes
lists/                         # Study lists by LeetCode slug
problems/                      # One directory per initialized problem
study/goals.md                 # Learning goals and current focus
study/profile.json             # Personal preferences and active list
study/profile.example.json     # Reference profile for migration
study/sessions/                # Daily session logs
templates/                     # Note/session/pattern/code templates
workspace/leetcode/            # Ignored VS Code LeetCode submit workspace
```

Problem folders are grouped by frontend ID:

```text
problems/
  0000-0999/
    0001-two-sum/
      note.md
      solution.py
      test_solution.py
```

## Data Model

Each `note.md` starts with a JSON metadata block. That block is the source of truth for progress:

```json
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
  }
}
```

Lists are views, sessions are logs, and pattern notes are reusable knowledge. The detailed asset contract lives in `.codex/skills/leetcode-coach/references/repo-contract.md`.

## Helper Commands

```bash
python3 .codex/skills/leetcode-coach/scripts/study.py next
python3 .codex/skills/leetcode-coach/scripts/study.py due
python3 .codex/skills/leetcode-coach/scripts/study.py mistakes
python3 .codex/skills/leetcode-coach/scripts/study.py plugin-files --slug <slug>
python3 .codex/skills/leetcode-coach/scripts/study.py log-session --problems "<slug>" --summary "<summary>" --next "<next>"
python3 .codex/skills/leetcode-coach/scripts/study.py finalize-session
```

Validation and migration:

```bash
make check
make strict-check
make migrate-preview
make migrate
```

## VS Code LeetCode Integration

This repo includes project-level settings for the VS Code LeetCode extension:

```json
{
  "leetcode.workspaceFolder": "${workspaceFolder}/workspace/leetcode",
  "leetcode.filePath": "${id}.${kebab-case-name}.${ext}",
  "leetcode.defaultLanguage": "python3",
  "leetcode.endpoint": "leetcode-cn"
}
```

Plugin-generated files are ignored by Git. They are for online judge interaction only. The coach archives accepted code into the matching problem directory after you report AC.

## Upgrading Older Notes

Older problem notes may not have `stats` or `Teach Back`. Preview the migration first:

```bash
make migrate-preview
```

Apply it when the preview looks correct:

```bash
make migrate
```

Then validate:

```bash
make check
```

Use `make strict-check` when you want to enforce that `solid` problems have teach-back evidence.

## Privacy And Copyright

- This is not an official LeetCode project.
- This is not a problem mirror, auto-solver, or auto-submitter.
- Do not commit LeetCode cookies, CSRF tokens, session values, or copied full problem statements.
- Store links, metadata, your own explanations, your own mistakes, and your own solutions.
- LeetCode content is governed by [LeetCode Terms](https://leetcode.com/terms).

## License

Add a license before publishing this as a public template.
