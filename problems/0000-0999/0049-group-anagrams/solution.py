# Archived from VS Code LeetCode plugin file: 49.字母异位词分组.py
# Problem: 49 Group Anagrams

class Solution:
    def groupAnagrams(self, strs: List[str]) -> List[List[str]]:
        anagram_map = {}
        for s in strs:
            sorted_s = ''.join(sorted(s))
            if sorted_s not in anagram_map:
                anagram_map[sorted_s] = []
            anagram_map[sorted_s].append(s)
        return list(anagram_map.values())
