<!-- leetcode-meta
{
  "id": 49,
  "slug": "group-anagrams",
  "title": "Group Anagrams",
  "difficulty": "Medium",
  "tags": [
    "array",
    "hash-table",
    "string",
    "sorting"
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

# Group Anagrams

## Link

https://leetcode.com/problems/group-anagrams/

## Restatement

Group strings that are anagrams of each other. The order of groups and the order inside each group do not matter.

## Key Observations

- Anagrams contain the same letters with the same frequencies.
- Sorting each string gives all anagrams the same canonical key, e.g. `eat`, `tea`, and `ate` all become `aet`.
- Use a hash map from canonical key to the list of original strings in that group.
- A 26-letter count tuple can also be used as the key. Sorting is simpler to write; counting is asymptotically faster per string when strings are long.

## Approach

Iterate through `strs`. For each string, sort its characters and join them into a key. Append the original string to `anagram_map[key]`. Return all map values at the end.

Alternative key: build a length-26 count array for each string and convert it to a tuple, because lists are mutable and cannot be dictionary keys.

## Complexity

- Time: `O(n * k log k)`, where `n` is the number of strings and `k` is the maximum string length.
- Space: `O(n * k)` for the grouped output and hash map keys.

## Mistakes

- None in this AC attempt.

## Pattern

- Pattern: hash table with canonical representation
- Reusable template: transform each item into a stable key, then group original items by that key.

## Review Log

| Date | Result | Notes |
|---|---|---|
| 2026-04-30 | AC | Used sorted string as canonical key. Review the alternative 26-count tuple key. |

## Similar Problems

- Valid Anagram
- Group Shifted Strings
- Find Resultant Array After Removing Anagrams
