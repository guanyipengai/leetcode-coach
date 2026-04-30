# Workflow Reference

## Repository Model

- `note.md` metadata is the source of truth for progress.
- The skill's bundled helper script is the agent-only query/update interface.
- `lists/*.md` are study views, not progress stores.
- `study/sessions/*.md` are daily logs.
- `knowledge/patterns/*.md` are reusable pattern notes.
- `workspace/leetcode/` is the ignored VS Code LeetCode plugin submit workspace.

## Session Loop

1. Recover state with the skill's bundled helper.
2. Pick a route: continue, review, Daily, or topic.
3. Fetch problem details through MCP.
4. Initialize or update the local problem note.
5. Ask the user to use the VS Code LeetCode plugin file for Test/Submit.
6. Teach before implementation: restate the problem, clarify constraints, discuss examples, identify patterns, and stop before full code.
7. Coach with progressive hints while the learner writes and submits through the plugin.
8. Review plugin code or judge failures until AC.
9. After AC, archive plugin code into `problems/.../solution.py`.
10. Update metadata, notes, session log, and review date.

## Public Template Boundary

Do not commit LeetCode cookies, session tokens, or full problem statements.

Problem content should be fetched from MCP during study. Notes should contain the user's own restatement and reasoning.

Plugin-generated files are temporary submit files and should not be committed.
