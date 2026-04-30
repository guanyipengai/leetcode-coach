---
name: leetcode-study-coach
description: Coach LeetCode study in this repository. Use when the user wants to start or resume a LeetCode session, choose the next problem, study Daily, practice a topic/list, get progressive hints, review code, update problem notes, maintain spaced repetition, or use this repo as a LeetCode second brain with scripts/study.py, per-problem note.md files, and LeetCode MCP.
---

# LeetCode Study Coach

## Operating Principle

Use progressive disclosure. Do not scan all problem notes by default. Start with `python scripts/study.py status --brief`, then open only the selected list, selected problem note, or reference file needed for the current task.

Do not store full LeetCode problem statements in this repository. Use LeetCode MCP for live problem details and store only metadata, links, the user's own notes, and the user's own solution.

Use the VS Code LeetCode plugin as the online judge/submit layer. Plugin files live under `workspace/leetcode/` and are not the long-term source of truth.

## Startup Protocol

When the user starts or resumes study:

1. Run `python scripts/study.py status --brief`.
2. Read `study/goals.md` if the user asks about goals or if the status output is not enough to suggest a route.
3. Summarize in Chinese by default:
   - current active list
   - initialized problem count and status counts
   - due reviews
   - latest session
   - recommended next action
4. Offer a concrete route:
   - continue the active list
   - review due problems
   - solve Daily
   - switch to a topic/list

If the user explicitly says "next" or "刷下一题", proceed with the recommended next problem instead of asking again.

## Problem Selection

Use the CLI first:

- `python scripts/study.py next` for the next recommended problem.
- `python scripts/study.py due` for review candidates.
- `lists/*.md` only when the user names a list or wants to inspect it.

For Daily, call LeetCode MCP `get_daily_challenge`, then initialize the problem with `scripts/study.py init-problem` if it is not already tracked.

For a named slug, call LeetCode MCP `get_problem` and initialize or update metadata before coaching.

## Problem Initialization

After MCP returns metadata, create or update the local problem with:

```bash
python scripts/study.py init-problem --id <frontend-id> --slug <slug> --title "<title>" --difficulty <difficulty> --tags tag1,tag2 --list <list-name>
```

Then open only that problem's `note.md` and `solution.py`.

After initialization, enter the plugin submit phase:

1. Tell the user to open the same problem through the VS Code LeetCode plugin.
2. Expect the plugin file under `workspace/leetcode/`.
3. Use `python scripts/study.py plugin-files --slug <slug>` to find it.
4. If it is missing, ask the user to generate/open the problem in the plugin before submitting.

## Coaching Flow

1. Restate the problem in the user's own learning language; Chinese is the default.
2. List constraints, edge cases, and likely patterns.
3. Use progressive hints:
   - Hint 1: pattern or data structure
   - Hint 2: key invariant or state
   - Hint 3: pseudocode
   - Final: complete implementation only if asked or clearly stuck
4. Let the user write the solution.
5. Review code with a code-review stance:
   - correctness
   - missed edge cases
   - complexity
   - readability
   - LeetCode-specific pitfalls
6. Update the selected `note.md` with concise user-owned learning notes.
7. After the user reports AC, archive the accepted plugin solution first:

```bash
python scripts/study.py archive-solution --slug <slug> --from-plugin
```

8. Finish with:

```bash
python scripts/study.py finish --slug <slug> --status <Todo|Doing|AC|Review> --mastery <new|shaky|ok|solid> --mistake-tags tag1,tag2 --review-in-days <n>
```

9. Append the daily session with:

```bash
python scripts/study.py log-session --problems "<slug>" --summary "<short result>" --next "<next suggestion>"
```

Before AC, do not set status to `AC`; use `Doing` if the user pauses mid-problem.

## Status Rules

- `Todo`: initialized but not started.
- `Doing`: currently being solved or paused mid-problem.
- `AC`: accepted and understood.
- `Review`: solved but should be redone.

Use `Review` when the user needed heavy hints, copied the solution, missed the invariant, or failed important edge cases.

Mastery:

- `new`: unfamiliar
- `shaky`: solved with meaningful help or uncertainty
- `ok`: solved and explainable
- `solid`: can solve quickly and explain tradeoffs

## Review Scheduling

Default intervals:

- `shaky` or `Review`: D+1
- `ok`: D+7
- `solid`: D+30

Prefer quality over volume. Do not add unnecessary review burden for trivial problems.

## References

Read `references/workflow.md` only when changing the workflow or explaining how the second brain works.
