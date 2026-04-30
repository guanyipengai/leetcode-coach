# LeetCode Study Brain

A Codex + MCP + Skill powered template for building a personal LeetCode second brain.

The repository starts as a clean learning scaffold. It does not include full LeetCode problem statements or a bundled Hot 100 list. After cloning, use Codex and the LeetCode MCP to initialize only the problems or lists you want to study.

## Core Ideas

- One problem, one `note.md`.
- Each `note.md` owns its progress metadata.
- Python scripts query and update notes so agents do not need to load every file.
- Codex Skills provide the coaching workflow.
- Problem statements are fetched on demand through MCP, not stored in the public template.

LeetCode content is copyrighted by LeetCode. Keep this template focused on links, metadata, your own notes, and your own solutions. See [LeetCode Terms](https://leetcode.com/terms).

## Daily Use

Start a new Codex session in this repository and say:

```text
用 leetcode-study-coach，今天开始学习。
```

The coach should:

1. Run `python scripts/study.py status --brief`.
2. Summarize goals, progress, due reviews, and the latest session.
3. Suggest whether to continue the active list, review due problems, solve Daily, or switch topic.
4. Fetch the chosen problem through LeetCode MCP.
5. Coach with progressive hints.
6. Review your solution.
7. Update the problem note, session log, and next review date.

## Repository Layout

```text
.codex/skills/leetcode-study-coach/  # Project skill
knowledge/patterns/                  # Reusable problem patterns
lists/                               # Study lists by slug
problems/                            # One folder per problem
scripts/study.py                     # Zero-dependency CLI for agents
study/goals.md                       # Learning goals
study/profile.json                   # Preferences and active list
study/sessions/                      # Daily logs
templates/                           # Note/session/pattern/code templates
workspace/leetcode/                  # Ignored VS Code LeetCode plugin workspace
```

Problem folders are grouped by frontend ID:

```text
problems/
  0000-0999/
    0001-two-sum/
      note.md
      solution.py
```

## CLI

Use the CLI directly or let the Skill call it:

```bash
python scripts/study.py status --brief
python scripts/study.py next
python scripts/study.py due
python scripts/study.py init-problem --id 1 --slug two-sum --title "Two Sum" --difficulty Easy --tags array,hash-table --list my-list
python scripts/study.py plugin-files --slug two-sum
python scripts/study.py archive-solution --slug two-sum --from-plugin
python scripts/study.py finish --slug two-sum --status AC --mastery ok --review-in-days 7
python scripts/study.py check
```

## VS Code LeetCode Plugin

This template includes project-level VS Code settings for the LeetCode plugin:

- Plugin files are generated under `workspace/leetcode/`.
- `workspace/leetcode/` is ignored by Git.
- Use plugin files for `Test` and `Submit`.
- After AC, ask Codex to archive the accepted code into the matching `problems/.../solution.py`.

The long-term source of truth remains each problem's `note.md` and archived `solution.py`.

## Adding A Study List

Create a Markdown file under `lists/` with slugs:

```md
# My Topic

- `two-sum`
- `group-anagrams`
```

The script treats lists as views. Progress still lives in the problem's own `note.md`.

## Publishing This Template

For a clean public template:

- Keep the scaffold, scripts, templates, and Skill.
- Do not commit LeetCode cookies or session values.
- Do not commit full problem statements copied from LeetCode.
- Keep personal progress only if this is your private learning repo.
