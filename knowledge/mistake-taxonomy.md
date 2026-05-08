# Mistake Taxonomy

Use these tags in `mistake_tags` and in the `## Mistakes` section of problem notes.

## Understanding

- `constraint-misread`: 读错约束、输入范围或返回要求。
- `example-overfit`: 只按样例想，没有覆盖一般情况。
- `pattern-mismatch`: 模式选择错，比如该用前缀和却用了滑窗。
- `complexity-misread`: 没有达到题目约束需要的复杂度。

## Invariant / State

- `invariant-missing`: 无法说清楚循环、窗口、堆、栈、图搜索或 DP 的不变量。
- `wrong-state`: DP / BFS / DFS 状态定义错。
- `transition-error`: 状态转移、递归返回值或更新顺序错误。
- `termination-error`: 终止条件、base case 或退出循环条件错误。

## Data Structure

- `data-structure-mismatch`: 数据结构选错。
- `canonical-key-error`: 哈希 key 的 canonical representation 错。
- `duplicate-handling`: 去重或重复元素处理错误。
- `ordering-assumption`: 错误假设输入有序或输出顺序。

## Boundary / Implementation

- `off-by-one`: 下标、区间开闭或长度差一。
- `empty-singleton-case`: 空输入、单元素、空字符串、单节点等边界漏掉。
- `mutation-aliasing`: 可变对象复用、浅拷贝、路径回溯撤销错误。
- `python-api-detail`: Python API、排序 key、heap、deque、Counter 等细节错误。
- `initialization-error`: 初始化值、哨兵、dummy node、visited、distance 等错误。

## Debugging / Submission

- `wa`: Wrong Answer。
- `tle`: Time Limit Exceeded。
- `re`: Runtime Error。
- `mle`: Memory Limit Exceeded。
- `test-gap`: 自己没有构造能暴露 bug 的反例。

## Communication

- `explanation-gap`: 代码能写但讲不清。
- `complexity-explanation-gap`: 复杂度能猜但不能证明。
- `tradeoff-gap`: 不能说明和相近模式 / 做法的取舍。
