# LeetCode Coach

[![Checks](https://github.com/guanyipengai/leetcode-coach/actions/workflows/leetcode-coach-check.yml/badge.svg)](https://github.com/guanyipengai/leetcode-coach/actions/workflows/leetcode-coach-check.yml)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB)
![Codex Skill](https://img.shields.io/badge/Codex-Skill-111827)
![VS Code](https://img.shields.io/badge/VS%20Code-LeetCode%20extension-007ACC)
![Status](https://img.shields.io/badge/status-alpha-yellow)

> A Codex skill and local study workspace that turns LeetCode practice into a review-driven coaching loop: solve in VS Code, get progressive hints, archive accepted solutions, and schedule evidence-based review.

<p align="center">
  <img src="assets/architecture.png" alt="LeetCode Coach architecture and learning loop" width="920">
</p>


## Why this exists

AI can make LeetCode practice faster, but it can also make it easier to skip the hard part. This project is designed around a stricter loop:

1. Review due problems before starting new ones.
2. Ask for progressive hints instead of full solutions.
3. Submit through the normal LeetCode workflow.
4. Archive only your accepted code and your own explanations.
5. Finish with teach-back before marking a problem as mastered.
6. Schedule the next review from evidence: time, hints, judge failures, recall quality, and mistake tags.

The goal is not to solve more problems with AI. The goal is to remember more of the problems you solve.

## What it does

- **Daily planning**: picks due reviews, active problems, and new problems from your active list.
- **Progressive coaching**: gives hints, counterexamples, edge-case checks, and complexity review without defaulting to answer dumps.
- **VS Code judge flow**: you solve and submit through the VS Code LeetCode extension under `workspace/leetcode/`.
- **Accepted-code archive**: after AC, accepted code is copied into `problems/.../solution.py`.
- **Evidence-based metadata**: tracks attempts, hint level, solve time, first-try AC, judge failures, recall score, teach-back status, and training mode.
- **Adaptive spaced review**: schedules review based on mastery, quality, hints, failures, and repeated mistake patterns.
- **Mistake taxonomy**: turns wrong answers into reusable weakness signals.
- **Pattern notes**: turns repeated ideas into durable templates and decision boundaries.
- **Local validation**: checks metadata and repository contracts with `make check`.

## What it is not

- It is not an official LeetCode project.
- It is not a LeetCode problem mirror.
- It is not an auto-submitter.
- It is not a tool for copying full problem statements or private LeetCode content into Git.
- It is not designed to replace your own reasoning during practice.

## Quick start

### 1. Clone and prepare the workspace

```bash
git clone https://github.com/guanyipengai/leetcode-coach.git
cd leetcode-coach
cp -n study/profile.example.json study/profile.json 2>/dev/null || true
make check
```

### 2. Install the judge workflow

Install the VS Code LeetCode extension, sign in, and open this repository in VS Code. The repository-level settings keep plugin-generated files under `workspace/leetcode/`, which is ignored by Git.

Optional: configure LeetCode MCP for Codex if you want the coach to fetch problem metadata automatically.

### 3. Start a coaching session

In Codex, start with:

```text
用 leetcode-coach，今天开始 LeetCode 训练。
```

or:

```text
Use leetcode-coach. Start today's LeetCode practice.
```

The coach should recover your current state, plan due reviews before new work, initialize the selected problem when needed, guide the solve, review code or judge failures, archive accepted code, require teach-back, and schedule the next review.


## Repository layout

```text
.codex/skills/leetcode-coach/      # Codex skill, references, and helper script
.github/workflows/                 # CI validation
.vscode/settings.json              # VS Code LeetCode workspace settings
docs/                              # Demo and troubleshooting notes
knowledge/mistake-taxonomy.md      # Standard mistake tags
knowledge/patterns/                # Reusable pattern notes
lists/                             # Study lists by LeetCode slug
problems/                          # One directory per initialized problem
study/goals.md                     # Learning goals and current focus
study/profile.json                 # Personal preferences and active list
study/sessions/                    # Daily session logs
templates/                         # Note, session, pattern, and code templates
workspace/leetcode/                # Ignored VS Code LeetCode submit workspace
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

## Data model

Each `note.md` starts with a JSON metadata block. That block is the source of truth for progress; lists and sessions are derived views or logs.

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

A problem should not be marked `solid` until teach-back is complete. In practice, that means you can explain:

- the invariant or state definition;
- why the chosen pattern works;
- time and space complexity;
- the easiest edge case to miss;
- when this pattern does not apply.

## Helper commands

Make targets:

```bash
make check
make strict-check
make migrate-preview
make migrate
```

## VS Code LeetCode integration

This repo expects project-level settings similar to:

```json
{
  "leetcode.workspaceFolder": "${workspaceFolder}/workspace/leetcode",
  "leetcode.filePath": "${id}.${kebab-case-name}.${ext}",
  "leetcode.defaultLanguage": "python3",
  "leetcode.endpoint": "leetcode-cn"
}
```

Plugin-generated files are temporary judge files. They should stay ignored by Git. The durable archive lives under `problems/.../` after AC.

## Upgrading older notes

Older problem notes may not include `stats` or `Teach Back`. Preview migration before writing changes:

```bash
make migrate-preview
```

Apply migration:

```bash
make migrate
make check
```

Use strict validation when you want to enforce teach-back evidence for `solid` problems:

```bash
make strict-check
```

## Project status

This project is usable as a personal LeetCode training workspace, but it is still early. The most stable parts are the repository contract, problem note format, and deterministic helper commands. Before using it as a public template, consider adding `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, and `SECURITY.md`.

## Roadmap

- richer mistake and review dashboards;
- more pattern-note templates and examples;
- coaching behavior evals, especially for answer-dumping prevention;
- problem-list import and export helpers;
- optional LangGraph runtime for resumable multi-step coaching sessions;
- installable Codex plugin packaging.

## Privacy and copyright

- Do not commit LeetCode cookies, CSRF tokens, session values, or other secrets.
- Do not commit copied full problem statements.
- Store links, metadata, your own explanations, your own mistakes, and your own accepted solutions.
- LeetCode content is governed by the LeetCode Terms of Service.

## Contributing

Issues and pull requests are welcome, especially for:

- clearer workflows and documentation;
- additional validation checks;
- mistake taxonomy improvements;
- pattern-note examples;
- tests for `study.py`.

Please keep the core principle intact: the coach should improve learning, not bypass it.

## License

MIT License. See [LICENSE](LICENSE).
