# Troubleshooting

## `study/profile.json not found`

This overlay provides `study/profile.example.json` to avoid overwriting your personal profile. Copy or merge it manually:

```bash
cp study/profile.example.json study/profile.json
```

If you already have `study/profile.json`, merge only the new keys you want, especially:

```json
{
  "problem_url_template": "https://leetcode.cn/problems/{slug}/",
  "solid_requires_teach_back": true
}
```

## `No plugin files found`

The VS Code LeetCode plugin writes transient files under `workspace/leetcode/`. Submit or open a problem through the plugin first, then run:

```bash
python3 .codex/skills/leetcode-coach/scripts/study.py plugin-files
```

## `Refusing mastery=solid`

The optimized skill treats `solid` as interview-ready. Run finish with teach-back evidence:

```bash
python3 .codex/skills/leetcode-coach/scripts/study.py finish --slug <slug> --mastery solid --teach-back true
```

Use `--allow-unverified-solid` only for migration or exceptional cases.

## Existing notes do not have `stats` or `Teach Back`

Preview migration:

```bash
python3 .codex/skills/leetcode-coach/scripts/study.py migrate
```

Apply migration:

```bash
python3 .codex/skills/leetcode-coach/scripts/study.py migrate --write
```

## `check --strict` fails on old solid problems

Old notes may be marked `solid` without `stats.teach_back_done=true`. Either review them again and finish with `--teach-back true`, or temporarily use non-strict `check` until migration is complete.
