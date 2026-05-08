# Demo Conversation

用户：用 leetcode-coach，今天开始训练。

Coach：先恢复状态。

```bash
python3 .codex/skills/leetcode-coach/scripts/study.py status --brief
python3 .codex/skills/leetcode-coach/scripts/study.py plan-day
```

Coach：今天先做 2 道 due review，再做 active list 的下一道新题。第一题用 `redo-from-memory`：先说 invariant，再写代码。

用户：Two Sum 的 invariant 是什么？

Coach：先不要看代码。你需要维护一个映射：已经见过的数 -> 下标。遍历到 `x` 时，只要 `target - x` 已经出现，就找到了答案。你来说明为什么不会错过答案。

用户：AC 了。

Coach：先归档，再做 teach-back。

```bash
python3 .codex/skills/leetcode-coach/scripts/study.py archive-solution --slug two-sum --from-plugin --mode standalone --with-tests
```

Coach：请用 30 秒回答：核心 invariant 是什么？复杂度为什么是 O(n)？最容易漏掉的边界是什么？

用户：讲完了。

Coach：记录证据并安排复习。

```bash
python3 .codex/skills/leetcode-coach/scripts/study.py finish \
  --slug two-sum \
  --status AC \
  --mastery solid \
  --mode redo-from-memory \
  --quality 5 \
  --hint-level 0 \
  --solve-minutes 8 \
  --first-try-ac true \
  --teach-back true
```
