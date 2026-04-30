<!-- leetcode-meta
{
  "id": 1,
  "slug": "two-sum",
  "title": "Two Sum",
  "difficulty": "Easy",
  "tags": [
    "array",
    "hash-table"
  ],
  "lists": [
    "example",
    "hot100"
  ],
  "status": "AC",
  "mastery": "ok",
  "last_practiced": "2026-04-30",
  "next_review": "2026-05-07",
  "mistake_tags": []
}
-->

# Two Sum

## Link

https://leetcode.com/problems/two-sum/

## Restatement

Find two different indices whose values add up to `target`.

## Key Observations

- When visiting `nums[i]`, the needed partner is `target - nums[i]`.
- A hash map can answer "have I seen this partner already?" in average `O(1)`.
- Check the partner before storing the current number so the same element is not used twice.

## Approach

Scan left to right. Keep a map from seen value to its index. For each number, compute its complement. If the complement is already in the map, return that stored index and the current index. Otherwise, store the current number and continue.

## Complexity

- Time: `O(n)`
- Space: `O(n)`

## Mistakes

- None in this AC attempt.

## Pattern

- Pattern: one-pass hash table lookup
- Reusable template: while scanning, store past state and query for the missing partner before adding the current item.

## Review Log

| Date | Result | Notes |
|---|---|---|
| 2026-04-30 | AC | Used one-pass hash map. Review why lookup happens before insert. |

## Similar Problems

- 3Sum
- 4Sum
- Two Sum II - Input Array Is Sorted
