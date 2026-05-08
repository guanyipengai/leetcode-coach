#!/usr/bin/env python3
"""Dependency-free helper for the LeetCode Coach skill."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

META_RE = re.compile(r"<!--\s*leetcode-meta\s*(\{.*?\})\s*-->", re.DOTALL)
SLUG_RE = re.compile(r"`([a-z0-9][a-z0-9-]*)`")
LC_HEADER_RE = re.compile(r"@lc\s+app=(?P<app>\S+)\s+id=(?P<id>\d+)\s+lang=(?P<lang>\S+)")
LC_CODE_RE = re.compile(
    r"^[ \t#/*.-]*@lc code=start[^\n]*\n(?P<code>.*?)(?=^[ \t#/*.-]*@lc code=end[^\n]*(?:\n|$))",
    re.DOTALL | re.MULTILINE,
)
LOG_ENTRY_RE = re.compile(r"(?ms)^## Log Entry\s*\n(?P<body>.*?)(?=^## Log Entry\s*\n|\Z)")
RAW_LOG_RE = re.compile(r"(?m)^## Raw Log\s*$")
LOG_FIELD_RE = re.compile(r"^- (?P<key>Problems|Summary|Next|Mode|Quality|Duration): (?P<value>.*)$", re.MULTILINE)

STATUSES = {"Todo", "Doing", "AC", "Review"}
MASTERIES = {"new", "shaky", "ok", "solid"}
TRAINING_MODES = {"blind-solve", "guided-solve", "redo-from-memory", "debug-drill", "pattern-contrast"}
PLUGIN_WORKSPACE = Path("workspace") / "leetcode"
ROOT_MARKERS = (Path("study") / "profile.json", Path("problems"), Path("lists"))
REQUIRED_META = [
    "id", "slug", "title", "difficulty", "tags", "lists", "status", "mastery",
    "last_practiced", "next_review", "mistake_tags",
]


def today() -> str:
    return dt.date.today().isoformat()


def parse_date(value: Optional[str]) -> Optional[dt.date]:
    if value in (None, ""):
        return None
    return dt.date.fromisoformat(str(value))


def split_csv(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [x.strip() for x in value.split(",") if x.strip()]


def unique(values: Iterable[Any]) -> List[Any]:
    out: List[Any] = []
    for value in values:
        if value is None:
            continue
        if value not in out:
            out.append(value)
    return out


def clean_lines(values: Iterable[str]) -> List[str]:
    return [v.strip() for v in values if v and v.strip()]


def dump(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)


def bool_arg(value: Optional[str]) -> bool:
    if value is None:
        return True
    lowered = value.lower()
    if lowered in {"1", "true", "t", "yes", "y"}:
        return True
    if lowered in {"0", "false", "f", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError(f"expected true/false, got {value!r}")


def default_stats() -> Dict[str, Any]:
    return {
        "attempts": 0,
        "hint_level_reached": 0,
        "solve_minutes": None,
        "first_try_ac": None,
        "judge_failures": [],
        "recall_score": None,
        "teach_back_done": False,
        "last_mode": None,
    }


def normalize_stats(value: Any) -> Dict[str, Any]:
    stats = default_stats()
    if isinstance(value, dict):
        stats.update(value)
    try:
        stats["attempts"] = int(stats.get("attempts") or 0)
    except (TypeError, ValueError):
        stats["attempts"] = 0
    try:
        stats["hint_level_reached"] = int(stats.get("hint_level_reached") or 0)
    except (TypeError, ValueError):
        stats["hint_level_reached"] = 0
    failures = stats.get("judge_failures") or []
    if isinstance(failures, str):
        failures = split_csv(failures)
    stats["judge_failures"] = unique(failures)
    return stats


def default_links(slug: str) -> Dict[str, str]:
    return {
        "leetcode": f"https://leetcode.com/problems/{slug}/",
        "leetcode_cn": f"https://leetcode.cn/problems/{slug}/",
    }


def normalize_meta(meta: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(meta)
    out["tags"] = unique(out.get("tags") or [])
    out["lists"] = unique(out.get("lists") or [])
    out["mistake_tags"] = unique(out.get("mistake_tags") or [])
    out.setdefault("status", "Todo")
    out.setdefault("mastery", "new")
    out.setdefault("last_practiced", None)
    out.setdefault("next_review", None)
    out["stats"] = normalize_stats(out.get("stats"))
    slug = str(out.get("slug") or "problem-slug")
    links = default_links(slug)
    if isinstance(out.get("links"), dict):
        links.update(out["links"])
    out["links"] = links
    return out


def is_root(path: Path) -> bool:
    return all((path / marker).exists() for marker in ROOT_MARKERS)


def find_root(start: Path) -> Optional[Path]:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if is_root(candidate):
            return candidate
    return None


def root_from_args(args: argparse.Namespace) -> Path:
    if getattr(args, "root", None):
        return Path(args.root).expanduser().resolve()
    return find_root(Path.cwd()) or find_root(Path(__file__).resolve()) or Path.cwd().resolve()


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def profile(root: Path) -> Dict[str, Any]:
    return read_json(root / "study" / "profile.json", {})


def write_meta_block(meta: Dict[str, Any]) -> str:
    clean = {k: v for k, v in meta.items() if not k.startswith("_")}
    return "<!-- leetcode-meta\n" + dump(clean) + "\n-->"


def note_paths(root: Path) -> List[Path]:
    problems = root / "problems"
    if not problems.exists():
        return []
    return sorted(problems.glob("*/*/note.md"))


def read_meta(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    match = META_RE.search(text)
    if not match:
        raise ValueError(f"missing leetcode-meta block: {path}")
    meta = normalize_meta(json.loads(match.group(1)))
    meta["_path"] = str(path)
    return meta


def update_note_meta(path: Path, updates: Dict[str, Any]) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    match = META_RE.search(text)
    if not match:
        raise ValueError(f"missing leetcode-meta block: {path}")
    meta = normalize_meta(json.loads(match.group(1)))
    meta.update(updates)
    meta = normalize_meta(meta)
    new_text = text[: match.start()] + write_meta_block(meta) + text[match.end() :]
    path.write_text(new_text, encoding="utf-8")
    meta["_path"] = str(path)
    return meta


def all_problems(root: Path) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for path in note_paths(root):
        try:
            items.append(read_meta(path))
        except Exception as exc:  # noqa: BLE001
            items.append({"_path": str(path), "_error": str(exc)})
    return sorted(items, key=lambda x: (x.get("id") is None, x.get("id") or 0, x.get("slug") or ""))


def problem_index(root: Path) -> Dict[str, Dict[str, Any]]:
    return {x.get("slug"): x for x in all_problems(root) if x.get("slug") and not x.get("_error")}


def find_problem(root: Path, slug: str) -> Optional[Tuple[Path, Dict[str, Any]]]:
    for path in note_paths(root):
        meta = read_meta(path)
        if meta.get("slug") == slug:
            return path, meta
    return None


def find_problem_by_id(root: Path, problem_id: int) -> Optional[Tuple[Path, Dict[str, Any]]]:
    for path in note_paths(root):
        meta = read_meta(path)
        if meta.get("id") == problem_id:
            return path, meta
    return None


def problem_dir(root: Path, problem_id: int, slug: str) -> Path:
    start = (problem_id // 1000) * 1000
    return root / "problems" / f"{start:04d}-{start + 999:04d}" / f"{problem_id:04d}-{slug}"


def list_slugs(root: Path, list_name: str) -> List[str]:
    path = root / "lists" / f"{list_name}.md"
    if not path.exists():
        return []
    return SLUG_RE.findall(path.read_text(encoding="utf-8"))


def latest_session(root: Path) -> Optional[Path]:
    folder = root / "study" / "sessions"
    if not folder.exists():
        return None
    sessions = sorted(x for x in folder.glob("*.md") if x.name != ".gitkeep")
    return sessions[-1] if sessions else None


def due_problems(root: Path, as_of: Optional[str] = None) -> List[Dict[str, Any]]:
    date = parse_date(as_of) if as_of else dt.date.today()
    due: List[Dict[str, Any]] = []
    for item in all_problems(root):
        if item.get("_error"):
            continue
        try:
            next_review = parse_date(item.get("next_review"))
        except ValueError:
            continue
        if next_review and next_review <= date and item.get("status") in {"AC", "Review"}:
            due.append(item)
    return sorted(due, key=lambda x: (x.get("next_review") or "", x.get("id") or 0))


def active_candidates(root: Path, active_list: str) -> List[Dict[str, Any]]:
    idx = problem_index(root)
    slugs = list_slugs(root, active_list)
    if slugs:
        return [idx[s] for s in slugs if s in idx]
    return [x for x in idx.values() if active_list in x.get("lists", [])]


def uninitialized(slug: str, reason: str) -> Dict[str, Any]:
    return {
        "id": None,
        "slug": slug,
        "title": slug,
        "difficulty": "?",
        "status": "Uninitialized",
        "mastery": "-",
        "next_review": None,
        "_path": None,
        "_reason": reason,
        "needs_mcp": True,
    }


def active_open_candidates(root: Path, active_list: str) -> List[Dict[str, Any]]:
    idx = problem_index(root)
    slugs = list_slugs(root, active_list)
    out: List[Dict[str, Any]] = []
    if slugs:
        for slug in slugs:
            item = idx.get(slug)
            if not item:
                out.append(uninitialized(slug, f"active-list:{active_list}:needs-init"))
            elif item.get("status") in {"Doing", "Todo", "Review"}:
                out.append({**item, "_reason": f"active-list:{active_list}"})
        return out
    for item in idx.values():
        if active_list in item.get("lists", []) and item.get("status") in {"Doing", "Todo", "Review"}:
            out.append({**item, "_reason": f"active-list:{active_list}"})
    return sorted(out, key=lambda x: (x.get("id") is None, x.get("id") or 0, x.get("slug") or ""))


def choose_next(root: Path) -> Optional[Dict[str, Any]]:
    prof = profile(root)
    active_list = prof.get("active_list", "example")
    due = due_problems(root)
    if due:
        return {**due[0], "_reason": "due-review"}
    candidates = active_candidates(root, active_list)
    for status in ("Doing", "Todo", "Review"):
        for item in candidates:
            if item.get("status") == status:
                return {**item, "_reason": f"active-list:{active_list}"}
    known = {x.get("slug") for x in all_problems(root) if not x.get("_error")}
    for slug in list_slugs(root, active_list):
        if slug not in known:
            return uninitialized(slug, f"active-list:{active_list}:needs-init")
    for item in all_problems(root):
        if not item.get("_error") and item.get("status") in {"Doing", "Todo", "Review"}:
            return {**item, "_reason": "any-open-problem"}
    return None


def compact(item: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not item:
        return None
    return {
        "id": item.get("id"),
        "slug": item.get("slug"),
        "title": item.get("title") or item.get("slug"),
        "difficulty": item.get("difficulty"),
        "status": item.get("status"),
        "mastery": item.get("mastery"),
        "next_review": item.get("next_review"),
        "mistake_tags": item.get("mistake_tags", []),
        "stats": item.get("stats", {}),
        "path": item.get("_path"),
        "needs_mcp": bool(item.get("needs_mcp") or item.get("status") == "Uninitialized" or item.get("id") is None),
        "reason": item.get("_reason"),
    }


def print_problem(item: Dict[str, Any]) -> None:
    print(
        f"{item.get('id', '?')}: {item.get('title') or item.get('slug')} "
        f"[{item.get('difficulty', '?')}] {item.get('status', '?')} "
        f"mastery={item.get('mastery', '?')} next_review={item.get('next_review') or '-'} "
        f"slug={item.get('slug', '-')}"
    )


def status_counts(items: Sequence[Dict[str, Any]]) -> Dict[str, int]:
    counts = {x: 0 for x in sorted(STATUSES)}
    for item in items:
        counts[item.get("status", "Todo")] = counts.get(item.get("status", "Todo"), 0) + 1
    return counts


def mastery_counts(items: Sequence[Dict[str, Any]]) -> Dict[str, int]:
    counts = {x: 0 for x in sorted(MASTERIES)}
    for item in items:
        counts[item.get("mastery", "new")] = counts.get(item.get("mastery", "new"), 0) + 1
    return counts


def mistake_summary(root: Path, days: Optional[int] = None, limit: int = 10) -> List[Dict[str, Any]]:
    cutoff = dt.date.today() - dt.timedelta(days=days) if days is not None else None
    counts: Counter[str] = Counter()
    examples: Dict[str, List[str]] = defaultdict(list)
    for item in all_problems(root):
        if item.get("_error"):
            continue
        if cutoff:
            practiced = parse_date(item.get("last_practiced"))
            if not practiced or practiced < cutoff:
                continue
        for tag in item.get("mistake_tags", []):
            counts[tag] += 1
            if len(examples[tag]) < 5:
                examples[tag].append(item.get("slug", "?"))
    return [{"tag": tag, "count": count, "problems": examples[tag]} for tag, count in counts.most_common(limit)]


def plugin_files(root: Path) -> List[Dict[str, Any]]:
    folder = root / PLUGIN_WORKSPACE
    if not folder.exists():
        return []
    out: List[Dict[str, Any]] = []
    for path in folder.iterdir():
        if not path.is_file() or path.name.startswith("."):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        match = LC_HEADER_RE.search(text)
        item = {"path": str(path), "id": None, "lang": None, "app": None, "mtime": path.stat().st_mtime}
        if match:
            group = match.groupdict()
            item.update({"id": int(group["id"]), "lang": group["lang"], "app": group["app"]})
        out.append(item)
    return sorted(out, key=lambda x: (x["id"] is None, x["id"] or 0, x["path"]))


def matching_plugin_files(root: Path, slug: Optional[str], problem_id: Optional[int]) -> List[Dict[str, Any]]:
    expected_id = problem_id
    if expected_id is None and slug:
        found = find_problem(root, slug)
        if found:
            expected_id = found[1].get("id")
    matches: List[Dict[str, Any]] = []
    for item in plugin_files(root):
        path = Path(item["path"])
        if expected_id is not None and item.get("id") == expected_id:
            matches.append(item)
        elif slug and slug in path.stem:
            matches.append(item)
    return sorted(matches, key=lambda x: x.get("mtime", 0), reverse=True)


def extract_code(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = LC_CODE_RE.search(text)
    if match:
        return match.group("code").strip("\n").rstrip() + "\n"
    return text.rstrip() + "\n"


def standalone_code(code: str) -> str:
    additions: List[str] = []
    typing_names = [name for name in ("List", "Optional", "Dict", "Set", "Tuple", "Deque") if re.search(rf"\b{name}\s*\[", code)]
    if typing_names and "from typing import" not in code and "import typing" not in code:
        additions.append("from typing import " + ", ".join(sorted(set(typing_names))))
    collections = [name for name in ("deque", "defaultdict", "Counter") if re.search(rf"\b{name}\b", code)]
    if collections and "from collections import" not in code and "import collections" not in code:
        additions.append("from collections import " + ", ".join(sorted(set(collections))))
    for module in ("heapq", "bisect", "math", "functools", "itertools"):
        if re.search(rf"\b{module}\.", code) and not re.search(rf"(?m)^\s*import\s+{module}\b", code):
            additions.append(f"import {module}")
    if additions:
        return "\n".join(additions) + "\n\n" + code.lstrip("\n")
    return code


def review_days(args: argparse.Namespace, stats: Dict[str, Any], repeated_mistake: bool) -> Optional[int]:
    if args.next_review:
        return None
    if args.review_in_days is not None:
        return args.review_in_days
    if args.status == "Todo":
        return None
    if args.status in {"Doing", "Review"}:
        return 1
    if args.mastery == "solid":
        days = 30
    elif args.mastery == "ok":
        days = 7
    else:
        days = 1
    quality = args.quality if args.quality is not None else stats.get("recall_score")
    hint = args.hint_level if args.hint_level is not None else stats.get("hint_level_reached")
    try:
        quality = int(quality) if quality is not None else None
    except (TypeError, ValueError):
        quality = None
    try:
        hint = int(hint or 0)
    except (TypeError, ValueError):
        hint = 0
    failures = {x.upper() for x in stats.get("judge_failures", [])}
    if quality is not None:
        if quality <= 2:
            days = min(days, 1)
        elif quality == 3:
            days = min(days, 3 if args.mastery != "solid" else 7)
        elif quality == 5 and args.mastery == "ok":
            days = max(days, 14)
    if hint >= 4:
        days = min(days, 1)
    elif hint >= 3:
        days = min(days, 3)
    if failures & {"WA", "TLE", "RE", "MLE"}:
        days = min(days, 7)
    if repeated_mistake:
        days = min(days, 3)
    return max(1, int(days))


def problem_url(prof: Dict[str, Any], slug: str) -> str:
    template = prof.get("problem_url_template") or "https://leetcode.com/problems/{slug}/"
    return template.format(slug=slug) if "{slug}" in template else template.rstrip("/") + f"/{slug}/"


def render_note(root: Path, meta: Dict[str, Any]) -> str:
    template_path = root / "templates" / "problem-note.md"
    if template_path.exists():
        text = template_path.read_text(encoding="utf-8")
    else:
        text = "<!-- leetcode-meta\n{}\n-->\n\n# Problem Title\n\n- Link: https://leetcode.com/problems/{slug}/\n"
    block = write_meta_block(meta)
    text = META_RE.sub(block, text, count=1) if META_RE.search(text) else block + "\n\n" + text
    prof = profile(root)
    slug = str(meta["slug"])
    text = text.replace("Problem Title", str(meta.get("title") or slug), 1)
    for placeholder in ("https://leetcode.com/problems/{slug}/", "https://leetcode.cn/problems/{slug}/"):
        text = text.replace(placeholder, problem_url(prof, slug), 1)
    text = text.replace("problem-slug", slug)
    return text if text.endswith("\n") else text + "\n"


def command_status(args: argparse.Namespace) -> int:
    root = root_from_args(args)
    prof = profile(root)
    items = all_problems(root)
    problems = [x for x in items if not x.get("_error")]
    errors = [x for x in items if x.get("_error")]
    active_list = prof.get("active_list", "example")
    next_item = choose_next(root)
    if args.brief:
        print(f"Root: {root}")
        print(f"Active list: {active_list}")
        print(f"Problems initialized: {len(problems)}")
        print("Status: " + ", ".join(f"{k}={v}" for k, v in sorted(status_counts(problems).items())))
        print("Mastery: " + ", ".join(f"{k}={v}" for k, v in sorted(mastery_counts(problems).items())))
        print(f"Active list initialized items: {len(active_candidates(root, active_list))}")
        print(f"Due reviews: {len(due_problems(root))}")
        top = mistake_summary(root, days=14, limit=3)
        if top:
            print("Top recent mistakes: " + ", ".join(f"{x['tag']}={x['count']}" for x in top))
        if next_item:
            print(
                f"Recommended next: {next_item.get('id', '?')} "
                f"{next_item.get('title') or next_item.get('slug')} ({next_item.get('_reason')})"
            )
        else:
            print("Recommended next: initialize a problem with MCP metadata")
        session = latest_session(root)
        print(f"Latest session: {session.name if session else '-'}")
        if errors:
            print(f"Metadata errors: {len(errors)}")
        return 0
    print(dump({
        "root": str(root),
        "active_list": active_list,
        "problem_count": len(problems),
        "status_counts": status_counts(problems),
        "mastery_counts": mastery_counts(problems),
        "active_list_count": len(active_candidates(root, active_list)),
        "due_reviews": [compact(x) for x in due_problems(root)],
        "recommended_next": compact(next_item),
        "latest_session": str(latest_session(root)) if latest_session(root) else None,
        "top_mistakes_recent": mistake_summary(root, days=14, limit=5),
        "metadata_errors": errors,
    }))
    return 0


def command_next(args: argparse.Namespace) -> int:
    root = root_from_args(args)
    item = choose_next(root)
    if args.json:
        print(dump(compact(item)))
        return 0
    if not item:
        print("No open or due problem found. Initialize the next active-list problem with LeetCode MCP metadata.")
        return 0
    print_problem(item)
    if item.get("needs_mcp"):
        print("needs_mcp=true: fetch id/title/difficulty/tags with LeetCode MCP, then run init-problem.")
    return 0


def command_due(args: argparse.Namespace) -> int:
    root = root_from_args(args)
    items = due_problems(root, args.as_of)
    if args.json:
        print(dump([compact(x) for x in items]))
        return 0
    if not items:
        print("No due reviews.")
        return 0
    for item in items:
        print_problem(item)
    return 0


def command_plan_day(args: argparse.Namespace) -> int:
    root = root_from_args(args)
    prof = profile(root)
    active_list = args.list or prof.get("active_list", "example")
    target = prof.get("daily_target", {}) if isinstance(prof.get("daily_target"), dict) else {}
    review_target = args.review_target if args.review_target is not None else int(target.get("review", 2) or 0)
    new_target = args.new_target if args.new_target is not None else int(target.get("new", 2) or 0)
    due = due_problems(root)
    reviews = due[:review_target] if review_target > 0 else []
    review_slugs = {x.get("slug") for x in reviews}
    open_items = [x for x in active_open_candidates(root, active_list) if x.get("slug") not in review_slugs]
    new_or_open = open_items[:new_target] if new_target > 0 else []
    recommended = reviews[0] if reviews else (new_or_open[0] if new_or_open else choose_next(root))
    suggested_mode = "redo-from-memory" if reviews else "guided-solve"
    if recommended and recommended.get("status") == "Uninitialized":
        suggested_mode = "guided-solve"
    plan = {
        "date": today(),
        "active_list": active_list,
        "daily_target": {"review": review_target, "new": new_target},
        "review_shortfall": max(0, review_target - len(reviews)),
        "due_review_count": len(due),
        "reviews": [compact(x) for x in reviews],
        "new_or_open": [compact(x) for x in new_or_open],
        "mistake_hotspots": mistake_summary(root, days=args.mistake_days, limit=5),
        "recommended_next": compact(recommended),
        "suggested_mode": suggested_mode,
    }
    if args.json:
        print(dump(plan))
        return 0
    print(f"Date: {plan['date']}")
    print(f"Active list: {active_list}")
    print(f"Due reviews: {len(due)}; target today: {review_target}")
    for item in reviews:
        print("Review: ", end="")
        print_problem(item)
    print(f"New/open target today: {new_target}")
    for item in new_or_open:
        print("New/Open: ", end="")
        print_problem(item)
    if recommended:
        print("Recommended next: ", end="")
        print_problem(recommended)
        if recommended.get("needs_mcp"):
            print("Recommended next is not initialized; use MCP metadata before coaching it.")
    top = plan["mistake_hotspots"]
    if top:
        print("Mistake hotspots: " + ", ".join(f"{x['tag']}({x['count']})" for x in top))
    print(f"Suggested mode: {suggested_mode}")
    return 0


def command_mistakes(args: argparse.Namespace) -> int:
    root = root_from_args(args)
    data = mistake_summary(root, days=args.days, limit=args.limit)
    if args.json:
        print(dump(data))
        return 0
    if not data:
        print("No mistake tags found.")
        return 0
    for item in data:
        print(f"{item['tag']}: {item['count']} ({', '.join(item['problems'])})")
    return 0


def command_plugin_files(args: argparse.Namespace) -> int:
    root = root_from_args(args)
    items = matching_plugin_files(root, args.slug, args.id) if (args.slug or args.id) else plugin_files(root)
    if args.json:
        print(dump(items))
        return 0
    if not items:
        print(f"No plugin files found under {root / PLUGIN_WORKSPACE}.")
        return 0
    for item in items:
        pid = item.get("id") if item.get("id") is not None else "?"
        print(f"{pid}\t{item.get('lang') or '?'}\t{item['path']}")
    return 0


def command_init_problem(args: argparse.Namespace) -> int:
    root = root_from_args(args)
    if find_problem(root, args.slug) and not args.force:
        print(f"Problem already exists for slug={args.slug}. Use --force to overwrite metadata/template.", file=sys.stderr)
        return 2
    found_by_id = find_problem_by_id(root, args.id)
    if found_by_id and found_by_id[1].get("slug") != args.slug and not args.force:
        print(f"Problem id={args.id} already exists as slug={found_by_id[1].get('slug')}. Use --force to override.", file=sys.stderr)
        return 2
    lists = unique(split_csv(args.lists) + (args.list or []))
    slug = args.slug.strip()
    meta = normalize_meta({
        "id": int(args.id),
        "slug": slug,
        "title": args.title or slug.replace("-", " ").title(),
        "difficulty": args.difficulty,
        "tags": split_csv(args.tags),
        "lists": lists,
        "status": args.status,
        "mastery": args.mastery,
        "last_practiced": None,
        "next_review": None,
        "mistake_tags": [],
        "stats": default_stats(),
        "links": default_links(slug),
    })
    dest_dir = problem_dir(root, int(args.id), slug)
    dest_dir.mkdir(parents=True, exist_ok=True)
    note = dest_dir / "note.md"
    if note.exists() and not args.force:
        print(f"note.md already exists: {note}. Use --force to overwrite.", file=sys.stderr)
        return 2
    note.write_text(render_note(root, meta), encoding="utf-8")
    solution = dest_dir / "solution.py"
    if not solution.exists():
        tmpl = root / "templates" / "solution.py"
        if tmpl.exists():
            solution.write_text(tmpl.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            solution.write_text("class Solution:\n    pass\n", encoding="utf-8")
    if args.json:
        print(dump({"note": str(note), "solution": str(solution), "metadata": meta}))
    else:
        print(f"Initialized: {note}")
        print(f"Solution placeholder: {solution}")
    return 0


def command_finish(args: argparse.Namespace) -> int:
    root = root_from_args(args)
    found = find_problem(root, args.slug)
    if not found:
        print(f"Unknown problem slug={args.slug}. Run init-problem first.", file=sys.stderr)
        return 2
    path, meta = found
    prof = profile(root)
    stats = normalize_stats(meta.get("stats"))
    stats["attempts"] = int(stats.get("attempts") or 0) + 1
    if args.hint_level is not None:
        stats["hint_level_reached"] = int(args.hint_level)
    if args.solve_minutes is not None:
        stats["solve_minutes"] = int(args.solve_minutes)
    if args.first_try_ac is not None:
        stats["first_try_ac"] = bool(args.first_try_ac)
    if args.judge_failures is not None:
        stats["judge_failures"] = unique(x.upper() for x in split_csv(args.judge_failures))
    if args.quality is not None:
        stats["recall_score"] = int(args.quality)
    if args.teach_back is not None:
        stats["teach_back_done"] = bool(args.teach_back)
    if args.mode:
        stats["last_mode"] = args.mode
    solid_requires_teach_back = bool(prof.get("solid_requires_teach_back", True))
    if (
        args.mastery == "solid"
        and solid_requires_teach_back
        and not args.allow_unverified_solid
        and not bool(stats.get("teach_back_done"))
    ):
        print("Refusing mastery=solid: teach_back_done is false. Add --teach-back true or --allow-unverified-solid.", file=sys.stderr)
        return 2
    old_mistakes = [] if args.clear_mistake_tags else list(meta.get("mistake_tags", []))
    new_mistakes = split_csv(args.mistake_tags)
    repeated = bool(set(old_mistakes) & set(new_mistakes))
    mistakes = unique(old_mistakes + new_mistakes)
    next_review: Optional[str]
    if args.next_review:
        parse_date(args.next_review)  # validate
        next_review = args.next_review
    else:
        days = review_days(args, stats, repeated)
        next_review = (dt.date.today() + dt.timedelta(days=days)).isoformat() if days is not None else None
    updates = {
        "status": args.status,
        "mastery": args.mastery,
        "last_practiced": today(),
        "next_review": next_review,
        "mistake_tags": mistakes,
        "stats": stats,
    }
    updated = update_note_meta(path, updates)
    if args.json:
        print(dump(compact(updated)))
    else:
        print(f"Updated: {path}")
        print(f"status={args.status} mastery={args.mastery} next_review={next_review} attempts={stats['attempts']}")
        if mistakes:
            print("mistake_tags=" + ",".join(mistakes))
    return 0


def session_path(root: Path, date: Optional[str] = None) -> Path:
    date = date or today()
    return root / "study" / "sessions" / f"{date}.md"


def ensure_session(root: Path, date: Optional[str] = None) -> Path:
    date = date or today()
    path = session_path(root, date)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        tmpl = root / "templates" / "session.md"
        if tmpl.exists():
            text = tmpl.read_text(encoding="utf-8").replace("{{date}}", date)
        else:
            text = f"# Study Session {date}\n\n## Plan\n\n## Raw Log\n\n## Summary\n"
        path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
    return path


def command_log_session(args: argparse.Namespace) -> int:
    root = root_from_args(args)
    date = args.date or today()
    path = ensure_session(root, date)
    entry = [
        "\n## Log Entry",
        f"- Problems: {args.problems or ''}",
        f"- Summary: {args.summary or ''}",
        f"- Next: {args.next or ''}",
        f"- Mode: {args.mode or ''}",
        f"- Quality: {args.quality if args.quality is not None else ''}",
        f"- Duration: {args.duration or ''}",
        "",
    ]
    with path.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(entry))
    if args.json:
        print(dump({"session": str(path)}))
    else:
        print(f"Logged session entry: {path}")
    return 0


def raw_log(text: str) -> str:
    match = RAW_LOG_RE.search(text)
    if not match:
        return ""
    return text[match.end() :]


def parse_entries(raw: str) -> List[Dict[str, str]]:
    entries: List[Dict[str, str]] = []
    for match in LOG_ENTRY_RE.finditer(raw):
        body = match.group("body")
        data: Dict[str, str] = {}
        for field in LOG_FIELD_RE.finditer(body):
            data[field.group("key").lower()] = field.group("value").strip()
        if data:
            entries.append(data)
    return entries


def command_finalize_session(args: argparse.Namespace) -> int:
    root = root_from_args(args)
    path = ensure_session(root, args.date or today())
    text = path.read_text(encoding="utf-8")
    entries = parse_entries(text)
    problems = unique(p for entry in entries for p in split_csv(entry.get("problems")))
    quality_values = []
    for entry in entries:
        q = entry.get("quality")
        if q not in (None, ""):
            try:
                quality_values.append(int(q))
            except ValueError:
                pass
    avg_quality = round(sum(quality_values) / len(quality_values), 2) if quality_values else None
    summary = [
        "\n## Auto Summary",
        f"- Entries: {len(entries)}",
        f"- Problems: {', '.join(problems) if problems else '-'}",
        f"- Average quality: {avg_quality if avg_quality is not None else '-'}",
        "- Recent mistake hotspots: " + (", ".join(f"{x['tag']}({x['count']})" for x in mistake_summary(root, days=7, limit=5)) or "-"),
        "",
    ]
    if "## Auto Summary" in text and not args.force:
        print(f"Auto Summary already exists in {path}. Use --force to append another one.", file=sys.stderr)
        return 2
    with path.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(summary))
    if args.json:
        print(dump({"session": str(path), "entries": len(entries), "problems": problems, "average_quality": avg_quality}))
    else:
        print(f"Finalized session: {path}")
    return 0


def command_archive_solution(args: argparse.Namespace) -> int:
    root = root_from_args(args)
    found = find_problem(root, args.slug)
    if not found:
        print(f"Unknown problem slug={args.slug}. Run init-problem first.", file=sys.stderr)
        return 2
    note_path, meta = found
    source: Optional[Path] = Path(args.source).expanduser().resolve() if args.source else None
    if source is None:
        matches = matching_plugin_files(root, args.slug, meta.get("id")) if args.from_plugin else []
        if not matches:
            print("No source solution found. Provide --source PATH or use --from-plugin after submitting in VS Code.", file=sys.stderr)
            return 2
        source = Path(matches[0]["path"])
    if not source.exists():
        print(f"Source does not exist: {source}", file=sys.stderr)
        return 2
    code = extract_code(source)
    if args.mode == "standalone":
        code = standalone_code(code)
    dest = note_path.parent / "solution.py"
    if dest.exists() and not args.no_backup:
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        shutil.copy2(dest, dest.with_suffix(f".py.bak-{stamp}"))
    dest.write_text(code if code.endswith("\n") else code + "\n", encoding="utf-8")
    test_path = None
    if args.with_tests:
        test_path = note_path.parent / "test_solution.py"
        if not test_path.exists():
            test_path.write_text(
                "from solution import Solution\n\n\n"
                "def test_examples():\n"
                "    sol = Solution()\n"
                "    # TODO: add examples and edge cases from your note.md\n"
                "    assert sol is not None\n",
                encoding="utf-8",
            )
    if args.json:
        print(dump({"source": str(source), "dest": str(dest), "mode": args.mode, "test": str(test_path) if test_path else None}))
    else:
        print(f"Archived solution: {dest}")
        print(f"Source: {source}")
        print(f"Mode: {args.mode}")
        if test_path:
            print(f"Test skeleton: {test_path}")
    return 0


def ensure_section(path: Path, heading: str, body: str) -> bool:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(rf"(?m)^##\s+{re.escape(heading)}\s*$")
    if pattern.search(text):
        return False
    addition = f"\n## {heading}\n\n{body.rstrip()}\n"
    if "## Mistakes" in text:
        text = text.replace("\n## Mistakes", addition + "\n## Mistakes", 1)
    else:
        text = text.rstrip() + addition + "\n"
    path.write_text(text, encoding="utf-8")
    return True


def command_migrate(args: argparse.Namespace) -> int:
    root = root_from_args(args)
    changed: List[str] = []
    would_change: List[str] = []
    teach_back_body = (
        "- Key invariant:\n"
        "- Why this data structure / state works:\n"
        "- Complexity and tradeoff:\n"
        "- Easiest edge case to miss:\n"
        "- When this pattern does NOT apply:\n"
    )
    for path in note_paths(root):
        text = path.read_text(encoding="utf-8")
        match = META_RE.search(text)
        if not match:
            continue
        original = json.loads(match.group(1))
        normalized = normalize_meta(original)
        needs_meta = original != {k: v for k, v in normalized.items() if not k.startswith("_")}
        needs_teach = not re.search(r"(?m)^##\s+Teach Back\s*$", text)
        if needs_meta or needs_teach:
            would_change.append(str(path))
        if not args.write:
            continue
        if needs_meta:
            clean = {k: v for k, v in normalized.items() if not k.startswith("_")}
            text = text[: match.start()] + write_meta_block(clean) + text[match.end() :]
            path.write_text(text, encoding="utf-8")
        if needs_teach:
            ensure_section(path, "Teach Back", teach_back_body)
        if needs_meta or needs_teach:
            changed.append(str(path))
    result = {"would_change": would_change, "changed": changed, "write": bool(args.write)}
    if args.json:
        print(dump(result))
    else:
        label = "Changed" if args.write else "Would change"
        print(f"{label}: {len(changed if args.write else would_change)} files")
        for item in (changed if args.write else would_change):
            print(item)
    return 0


def validate_meta(path: Path, strict: bool = False) -> List[str]:
    errors: List[str] = []
    try:
        meta = read_meta(path)
    except Exception as exc:  # noqa: BLE001
        return [str(exc)]
    for key in REQUIRED_META:
        if key not in meta:
            errors.append(f"{path}: missing metadata key {key}")
    if meta.get("status") not in STATUSES:
        errors.append(f"{path}: invalid status {meta.get('status')!r}")
    if meta.get("mastery") not in MASTERIES:
        errors.append(f"{path}: invalid mastery {meta.get('mastery')!r}")
    if not isinstance(meta.get("tags"), list):
        errors.append(f"{path}: tags must be a list")
    if not isinstance(meta.get("lists"), list):
        errors.append(f"{path}: lists must be a list")
    if not isinstance(meta.get("mistake_tags"), list):
        errors.append(f"{path}: mistake_tags must be a list")
    if strict:
        stats = meta.get("stats")
        if not isinstance(stats, dict):
            errors.append(f"{path}: strict mode requires stats object")
        elif meta.get("mastery") == "solid" and not stats.get("teach_back_done"):
            errors.append(f"{path}: mastery=solid requires stats.teach_back_done=true")
    return errors


def validate_templates(root: Path) -> List[str]:
    errors: List[str] = []
    problem_tmpl = root / "templates" / "problem-note.md"
    if problem_tmpl.exists():
        text = problem_tmpl.read_text(encoding="utf-8")
        if not META_RE.search(text):
            errors.append(f"{problem_tmpl}: missing leetcode-meta template block")
        if "## Teach Back" not in text:
            errors.append(f"{problem_tmpl}: missing ## Teach Back")
    else:
        errors.append(f"{problem_tmpl}: missing")
    pattern_tmpl = root / "templates" / "pattern-note.md"
    if pattern_tmpl.exists():
        text = pattern_tmpl.read_text(encoding="utf-8")
        for heading in ("## When To Use", "## Core Invariant", "## Common Mistakes", "## Contrast", "## Problems"):
            if heading not in text:
                errors.append(f"{pattern_tmpl}: missing {heading}")
    return errors


def command_check(args: argparse.Namespace) -> int:
    root = root_from_args(args)
    errors: List[str] = []
    warnings: List[str] = []
    if not (root / "study" / "profile.json").exists():
        warnings.append("study/profile.json not found; copy or merge study/profile.example.json")
    if not (root / "lists").exists():
        warnings.append("lists/ directory not found")
    if not (root / "problems").exists():
        warnings.append("problems/ directory not found")
    for path in note_paths(root):
        errors.extend(validate_meta(path, strict=args.strict))
        if args.strict:
            text = path.read_text(encoding="utf-8")
            if "## Teach Back" not in text:
                errors.append(f"{path}: strict mode requires ## Teach Back")
    errors.extend(validate_templates(root))
    result = {"root": str(root), "ok": not errors, "errors": errors, "warnings": warnings}
    if args.json:
        print(dump(result))
    else:
        for warning in warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            print(f"Check failed: {len(errors)} errors")
        else:
            print("Check passed")
    return 1 if errors else 0


def build_parser() -> argparse.ArgumentParser:
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("--root", help="Repository root. Can also be passed before the subcommand.")

    parser = argparse.ArgumentParser(description="LeetCode Coach helper")
    parser.add_argument("--root", help="Repository root. Can also be passed after the subcommand.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("status", parents=[parent], help="Show compact repo learning status")
    p.add_argument("--brief", action="store_true")
    p.set_defaults(func=command_status)

    p = sub.add_parser("next", parents=[parent], help="Show recommended next problem")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=command_next)

    p = sub.add_parser("due", parents=[parent], help="List due review problems")
    p.add_argument("--as-of")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=command_due)

    p = sub.add_parser("plan-day", parents=[parent], help="Build today's review/new problem plan")
    p.add_argument("--list")
    p.add_argument("--review-target", type=int)
    p.add_argument("--new-target", type=int)
    p.add_argument("--mistake-days", type=int, default=14)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=command_plan_day)

    p = sub.add_parser("mistakes", parents=[parent], help="Summarize recent mistake tags")
    p.add_argument("--days", type=int)
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=command_mistakes)

    p = sub.add_parser("plugin-files", parents=[parent], help="List VS Code LeetCode plugin files")
    p.add_argument("--slug")
    p.add_argument("--id", type=int)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=command_plugin_files)

    p = sub.add_parser("init-problem", parents=[parent], help="Create problem note and solution placeholder")
    p.add_argument("--id", type=int, required=True)
    p.add_argument("--slug", required=True)
    p.add_argument("--title")
    p.add_argument("--difficulty", default="")
    p.add_argument("--tags", default="")
    p.add_argument("--lists", default="")
    p.add_argument("--list", action="append")
    p.add_argument("--status", choices=sorted(STATUSES), default="Todo")
    p.add_argument("--mastery", choices=sorted(MASTERIES), default="new")
    p.add_argument("--force", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=command_init_problem)

    p = sub.add_parser("finish", parents=[parent], help="Mark a practice attempt complete and schedule review")
    p.add_argument("--slug", required=True)
    p.add_argument("--status", choices=sorted(STATUSES), default="AC")
    p.add_argument("--mastery", choices=sorted(MASTERIES), default="ok")
    p.add_argument("--mode", choices=sorted(TRAINING_MODES))
    p.add_argument("--quality", type=int, choices=range(0, 6))
    p.add_argument("--hint-level", type=int, choices=range(0, 5))
    p.add_argument("--solve-minutes", type=int)
    p.add_argument("--first-try-ac", nargs="?", const=True, default=None, type=bool_arg)
    p.add_argument("--judge-failures")
    p.add_argument("--mistake-tags", default="")
    p.add_argument("--clear-mistake-tags", action="store_true")
    p.add_argument("--teach-back", nargs="?", const=True, default=None, type=bool_arg)
    p.add_argument("--allow-unverified-solid", action="store_true")
    p.add_argument("--next-review")
    p.add_argument("--review-in-days", type=int)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=command_finish)

    p = sub.add_parser("log-session", parents=[parent], help="Append a session log entry")
    p.add_argument("--date")
    p.add_argument("--problems")
    p.add_argument("--summary")
    p.add_argument("--next")
    p.add_argument("--mode", choices=sorted(TRAINING_MODES))
    p.add_argument("--quality", type=int, choices=range(0, 6))
    p.add_argument("--duration")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=command_log_session)

    p = sub.add_parser("finalize-session", parents=[parent], help="Append an auto summary to a session note")
    p.add_argument("--date")
    p.add_argument("--force", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=command_finalize_session)

    p = sub.add_parser("archive-solution", parents=[parent], help="Archive solution.py from plugin or source file")
    p.add_argument("--slug", required=True)
    p.add_argument("--from-plugin", action="store_true")
    p.add_argument("--source")
    p.add_argument("--mode", choices=["leetcode", "standalone"], default="standalone")
    p.add_argument("--with-tests", action="store_true")
    p.add_argument("--no-backup", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=command_archive_solution)

    p = sub.add_parser("migrate", parents=[parent], help="Add new metadata defaults and Teach Back sections")
    p.add_argument("--write", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=command_migrate)

    p = sub.add_parser("check", parents=[parent], help="Validate notes/templates")
    p.add_argument("--strict", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=command_check)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args) or 0)
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        return 130
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
