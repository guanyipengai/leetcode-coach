#!/usr/bin/env python3
"""Internal helper for the LeetCode Coach skill."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


META_RE = re.compile(r"<!--\s*leetcode-meta\s*(\{.*?\})\s*-->", re.DOTALL)
SLUG_RE = re.compile(r"`([a-z0-9][a-z0-9-]*)`")
LC_HEADER_RE = re.compile(r"@lc\s+app=(?P<app>\S+)\s+id=(?P<id>\d+)\s+lang=(?P<lang>\S+)")
LC_CODE_RE = re.compile(r"(?P<start>^[ \t#/-]*@lc code=start[^\n]*\n)(?P<code>.*?)(?P<end>^[ \t#/-]*@lc code=end[^\n]*\n?)", re.DOTALL | re.MULTILINE)
LOG_ENTRY_RE = re.compile(r"(?ms)^## Log Entry\s*\n(?P<body>.*?)(?=^## Log Entry\s*\n|\Z)")
RAW_LOG_HEADING_RE = re.compile(r"(?m)^## Raw Log\s*$")
LOG_FIELD_RE = re.compile(r"^- (?P<key>Problems|Summary|Next): (?P<value>.*)$", re.MULTILINE)
STATUSES = {"Todo", "Doing", "AC", "Review"}
MASTERIES = {"new", "shaky", "ok", "solid"}
PLUGIN_WORKSPACE = Path("workspace") / "leetcode"
ROOT_MARKERS = (
    Path("study") / "profile.json",
    Path("problems"),
    Path("lists"),
)


def today() -> str:
    return dt.date.today().isoformat()


def parse_date(value: Optional[str]) -> Optional[dt.date]:
    if not value:
        return None
    return dt.date.fromisoformat(value)


def split_csv(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def clean_lines(values: Iterable[str]) -> List[str]:
    return [value.strip() for value in values if value and value.strip()]


def is_workspace_root(path: Path) -> bool:
    return all((path / marker).exists() for marker in ROOT_MARKERS)


def find_workspace_root(start: Path) -> Optional[Path]:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if is_workspace_root(candidate):
            return candidate
    return None


def root_from_args(args: argparse.Namespace) -> Path:
    if getattr(args, "root", None):
        return Path(args.root).expanduser().resolve()
    cwd_root = find_workspace_root(Path.cwd())
    if cwd_root:
        return cwd_root
    script_root = find_workspace_root(Path(__file__).resolve())
    if script_root:
        return script_root
    return Path.cwd().resolve()


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json_block(meta: Dict[str, Any]) -> str:
    return "<!-- leetcode-meta\n" + json.dumps(meta, indent=2, ensure_ascii=False) + "\n-->"


def note_paths(root: Path) -> Iterable[Path]:
    problems_dir = root / "problems"
    if not problems_dir.exists():
        return []
    return problems_dir.glob("*/*/note.md")


def read_meta(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    match = META_RE.search(text)
    if not match:
        raise ValueError(f"missing leetcode-meta block: {path}")
    meta = json.loads(match.group(1))
    meta["_path"] = str(path)
    return meta


def read_note_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def update_note_meta(path: Path, updates: Dict[str, Any]) -> Dict[str, Any]:
    text = read_note_text(path)
    match = META_RE.search(text)
    if not match:
        raise ValueError(f"missing leetcode-meta block: {path}")
    meta = json.loads(match.group(1))
    meta.update(updates)
    new_text = text[: match.start()] + write_json_block(meta) + text[match.end() :]
    path.write_text(new_text, encoding="utf-8")
    meta["_path"] = str(path)
    return meta


def all_problems(root: Path) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for path in note_paths(root):
        try:
            items.append(read_meta(path))
        except Exception as exc:  # noqa: BLE001 - report all metadata errors in check.
            items.append({"_path": str(path), "_error": str(exc)})
    return sorted(items, key=lambda item: (item.get("id") is None, item.get("id") or 0, item.get("slug") or ""))


def problem_index(root: Path) -> Dict[str, Dict[str, Any]]:
    return {item.get("slug"): item for item in all_problems(root) if item.get("slug") and not item.get("_error")}


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
    bucket_start = (problem_id // 1000) * 1000
    bucket_end = bucket_start + 999
    bucket = f"{bucket_start:04d}-{bucket_end:04d}"
    return root / "problems" / bucket / f"{problem_id:04d}-{slug}"


def list_slugs(root: Path, list_name: str) -> List[str]:
    path = root / "lists" / f"{list_name}.md"
    if not path.exists():
        return []
    return SLUG_RE.findall(path.read_text(encoding="utf-8"))


def latest_session(root: Path) -> Optional[Path]:
    session_dir = root / "study" / "sessions"
    if not session_dir.exists():
        return None
    sessions = sorted(path for path in session_dir.glob("*.md") if path.name != ".gitkeep")
    return sessions[-1] if sessions else None


def due_problems(root: Path, as_of: Optional[str] = None) -> List[Dict[str, Any]]:
    date = parse_date(as_of) if as_of else dt.date.today()
    due: List[Dict[str, Any]] = []
    for item in all_problems(root):
        if item.get("_error"):
            continue
        next_review = parse_date(item.get("next_review"))
        if next_review and next_review <= date and item.get("status") in {"AC", "Review"}:
            due.append(item)
    return sorted(due, key=lambda item: (item.get("next_review") or "", item.get("id") or 0))


def active_candidates(root: Path, active_list: str) -> List[Dict[str, Any]]:
    problems = problem_index(root)
    slugs = list_slugs(root, active_list)
    if slugs:
        return [problems[slug] for slug in slugs if slug in problems]
    return [item for item in problems.values() if active_list in item.get("lists", [])]


def compact_problem(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": item.get("id"),
        "slug": item.get("slug"),
        "title": item.get("title") or item.get("slug"),
        "difficulty": item.get("difficulty"),
        "status": item.get("status"),
        "mastery": item.get("mastery"),
        "next_review": item.get("next_review"),
        "path": item.get("_path"),
        "needs_mcp": item.get("status") == "Uninitialized" or item.get("id") is None,
        "reason": item.get("_reason"),
    }


def uninitialized_problem(slug: str, reason: str) -> Dict[str, Any]:
    return {
        "id": None,
        "slug": slug,
        "title": slug,
        "difficulty": "?",
        "status": "Uninitialized",
        "mastery": "-",
        "next_review": None,
        "_reason": reason,
        "_path": None,
    }


def active_open_candidates(root: Path, active_list: str) -> List[Dict[str, Any]]:
    problems = problem_index(root)
    slugs = list_slugs(root, active_list)
    candidates: List[Dict[str, Any]] = []

    if slugs:
        for slug in slugs:
            item = problems.get(slug)
            if not item:
                candidates.append(uninitialized_problem(slug, f"active-list:{active_list}:needs-init"))
            elif item.get("status") in {"Doing", "Todo"}:
                result = dict(item)
                result["_reason"] = f"active-list:{active_list}"
                candidates.append(result)
        return candidates

    for item in problems.values():
        if active_list in item.get("lists", []) and item.get("status") in {"Doing", "Todo"}:
            result = dict(item)
            result["_reason"] = f"active-list:{active_list}"
            candidates.append(result)
    return sorted(candidates, key=lambda item: (item.get("id") is None, item.get("id") or 0, item.get("slug") or ""))


def choose_next(root: Path) -> Optional[Dict[str, Any]]:
    profile = read_json(root / "study" / "profile.json", {})
    active_list = profile.get("active_list", "example")
    due = due_problems(root)
    if due:
        item = dict(due[0])
        item["_reason"] = "due-review"
        return item
    candidates = active_candidates(root, active_list)
    for status in ("Doing", "Todo", "Review"):
        for item in candidates:
            if item.get("status") == status:
                result = dict(item)
                result["_reason"] = f"active-list:{active_list}"
                return result
    known = {item.get("slug") for item in all_problems(root) if not item.get("_error")}
    for slug in list_slugs(root, active_list):
        if slug not in known:
            return uninitialized_problem(slug, f"active-list:{active_list}:needs-init")
    for item in all_problems(root):
        if not item.get("_error") and item.get("status") in {"Doing", "Todo", "Review"}:
            result = dict(item)
            result["_reason"] = "any-open-problem"
            return result
    return None


def print_problem_line(item: Dict[str, Any]) -> None:
    print(
        f"{item.get('id', '?')}: {item.get('title') or item.get('slug')} "
        f"[{item.get('difficulty', '?')}] {item.get('status', '?')} "
        f"mastery={item.get('mastery', '?')} next_review={item.get('next_review') or '-'}"
    )


def plugin_workspace(root: Path) -> Path:
    return root / PLUGIN_WORKSPACE


def read_plugin_header(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    match = LC_HEADER_RE.search(text)
    if not match:
        return {"path": str(path), "id": None, "lang": None, "app": None}
    data = match.groupdict()
    return {
        "path": str(path),
        "id": int(data["id"]),
        "lang": data["lang"],
        "app": data["app"],
    }


def plugin_files(root: Path) -> List[Dict[str, Any]]:
    workspace = plugin_workspace(root)
    if not workspace.exists():
        return []
    files = [path for path in workspace.iterdir() if path.is_file() and not path.name.startswith(".")]
    return sorted((read_plugin_header(path) for path in files), key=lambda item: (item["id"] is None, item["id"] or 0, item["path"]))


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
    return matches


def extract_leetcode_code(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = LC_CODE_RE.search(text)
    if not match:
        raise ValueError(f"missing @lc code=start/end block: {path}")
    code = match.group("code").strip("\n")
    return code.rstrip() + "\n"


def command_status(args: argparse.Namespace) -> int:
    root = root_from_args(args)
    profile = read_json(root / "study" / "profile.json", {})
    problems = [item for item in all_problems(root) if not item.get("_error")]
    errors = [item for item in all_problems(root) if item.get("_error")]
    counts = {status: 0 for status in sorted(STATUSES)}
    for item in problems:
        counts[item.get("status", "Todo")] = counts.get(item.get("status", "Todo"), 0) + 1
    active_list = profile.get("active_list", "example")
    active = active_candidates(root, active_list)
    due = due_problems(root)
    next_item = choose_next(root)
    session = latest_session(root)

    if args.brief:
        print(f"Active list: {active_list}")
        print(f"Problems initialized: {len(problems)}")
        print("Status: " + ", ".join(f"{key}={value}" for key, value in sorted(counts.items())))
        print(f"Active list initialized items: {len(active)}")
        print(f"Due reviews: {len(due)}")
        if next_item:
            print(
                "Recommended next: "
                f"{next_item.get('id', '?')} {next_item.get('title') or next_item.get('slug')} "
                f"({next_item.get('_reason')})"
            )
        else:
            print("Recommended next: initialize a problem with MCP metadata")
        print(f"Latest session: {session.name if session else '-'}")
        if errors:
            print(f"Metadata errors: {len(errors)}")
        return 0

    print(json.dumps({
        "active_list": active_list,
        "problem_count": len(problems),
        "status_counts": counts,
        "active_list_count": len(active),
        "due_reviews": due,
        "recommended_next": next_item,
        "latest_session": str(session) if session else None,
        "metadata_errors": errors,
    }, indent=2, ensure_ascii=False))
    return 0


def command_next(args: argparse.Namespace) -> int:
    root = root_from_args(args)
    item = choose_next(root)
    if not item:
        print("No initialized problem is ready. Use init-problem after fetching metadata with MCP.")
        return 1
    print_problem_line(item)
    print(f"Reason: {item.get('_reason')}")
    print(f"Path: {item.get('_path') or '-'}")
    if item.get("status") == "Uninitialized":
        print("Initialize this slug with MCP metadata before coaching.")
    return 0


def command_due(args: argparse.Namespace) -> int:
    root = root_from_args(args)
    items = due_problems(root, args.date)
    if not items:
        print("No reviews due.")
        return 0
    for item in items:
        print_problem_line(item)
    return 0


def int_from_profile(value: Any, default: int) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return default


def daily_targets(profile: Dict[str, Any]) -> Tuple[int, int]:
    target = profile.get("daily_target", {})
    new_target = int_from_profile(target.get("new_problems"), 1)
    review_target = int_from_profile(target.get("review_problems"), 1)
    return new_target, review_target


def status_counts(problems: List[Dict[str, Any]]) -> Dict[str, int]:
    counts = {status: 0 for status in sorted(STATUSES)}
    for item in problems:
        counts[item.get("status", "Todo")] = counts.get(item.get("status", "Todo"), 0) + 1
    return counts


def plan_day_data(root: Path, as_of: Optional[str] = None) -> Dict[str, Any]:
    date = as_of or today()
    profile = read_json(root / "study" / "profile.json", {})
    active_list = profile.get("active_list", "example")
    new_target, review_target = daily_targets(profile)
    problems = [item for item in all_problems(root) if not item.get("_error")]
    due_all = []
    for item in due_problems(root, date):
        result = dict(item)
        result["_reason"] = "due-review"
        due_all.append(result)
    due_selected = due_all[:review_target]
    review_shortfall = max(0, review_target - len(due_selected))
    new_pool = active_open_candidates(root, active_list)
    new_candidates = new_pool[:new_target]
    extra_new_candidates = new_pool[new_target:new_target + review_shortfall]
    as_of_date = parse_date(date)
    upcoming_reviews = [
        dict(item, _reason="upcoming-review") for item in problems
        if item.get("status") in {"AC", "Review"}
        and parse_date(item.get("next_review")) is not None
        and parse_date(item.get("next_review")) > as_of_date
    ]
    upcoming_reviews = sorted(upcoming_reviews, key=lambda item: (item.get("next_review") or "", item.get("id") or 0))
    recommended_next = due_selected[0] if due_selected else (new_candidates[0] if new_candidates else (extra_new_candidates[0] if extra_new_candidates else None))

    return {
        "date": date,
        "active_list": active_list,
        "targets": {
            "new_problems": new_target,
            "review_problems": review_target,
        },
        "problem_count": len(problems),
        "status_counts": status_counts(problems),
        "active_list_total_slugs": len(list_slugs(root, active_list)),
        "due_reviews": [compact_problem(item) for item in due_selected],
        "due_review_total": len(due_all),
        "review_shortfall": review_shortfall,
        "new_candidates": [compact_problem(item) for item in new_candidates],
        "extra_new_candidates": [compact_problem(item) for item in extra_new_candidates],
        "upcoming_reviews": [compact_problem(item) for item in upcoming_reviews[:5]],
        "recommended_next": compact_problem(recommended_next) if recommended_next else None,
    }


def command_plan_day(args: argparse.Namespace) -> int:
    root = root_from_args(args)
    print(json.dumps(plan_day_data(root, args.date), indent=2, ensure_ascii=False))
    return 0


def session_path(root: Path, date: str) -> Path:
    return root / "study" / "sessions" / f"{date}.md"


def extract_raw_log(text: str) -> str:
    raw_match = RAW_LOG_HEADING_RE.search(text)
    if raw_match:
        return text[raw_match.end():].strip()
    entries = []
    for match in LOG_ENTRY_RE.finditer(text):
        body = match.group("body").strip()
        entries.append("## Log Entry\n\n" + body)
    return "\n\n".join(entries).strip()


def parse_log_entries(raw_log: str) -> List[Dict[str, str]]:
    entries: List[Dict[str, str]] = []
    for match in LOG_ENTRY_RE.finditer(raw_log):
        fields: Dict[str, str] = {}
        for field in LOG_FIELD_RE.finditer(match.group("body")):
            fields[field.group("key").lower()] = field.group("value").strip()
        if fields:
            entries.append(fields)
    return entries


def markdown_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def slug_refs(value: str) -> str:
    backticked = SLUG_RE.findall(value)
    if backticked:
        return ", ".join(f"`{slug}`" for slug in backticked)
    parts = split_csv(value)
    if not parts:
        parts = [part.strip() for part in value.split() if part.strip()]
    return ", ".join(f"`{part}`" if re.fullmatch(r"[a-z0-9][a-z0-9-]*", part) else part for part in parts)


def result_from_summary(summary: str) -> str:
    upper = summary.upper()
    if "AC" in upper:
        return "AC"
    if "REVIEW" in upper:
        return "Review"
    if "WA" in upper or "TLE" in upper or "RE" in upper:
        return "Debug"
    return "Logged"


def format_bullets(items: List[str]) -> str:
    cleaned = clean_lines(items)
    if not cleaned:
        return "- None recorded.\n"
    return "\n".join(f"- {item}" for item in cleaned) + "\n"


def format_problem_rows(entries: List[Dict[str, str]]) -> str:
    rows = ["| Problem | Action | Result | Notes |", "|---|---|---|---|"]
    if not entries:
        rows.append("| - | - | - | No problem log entries recorded. |")
        return "\n".join(rows) + "\n"
    for entry in entries:
        problems = slug_refs(entry.get("problems", "-"))
        summary = entry.get("summary", "")
        rows.append(
            "| "
            + " | ".join([
                markdown_cell(problems or "-"),
                "Practice",
                markdown_cell(result_from_summary(summary)),
                markdown_cell(summary or "-"),
            ])
            + " |"
        )
    return "\n".join(rows) + "\n"


def command_finalize_session(args: argparse.Namespace) -> int:
    root = root_from_args(args)
    date = args.date or today()
    path = session_path(root, date)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        text = path.read_text(encoding="utf-8")
    else:
        template = (root / "templates" / "session.md").read_text(encoding="utf-8")
        text = template.replace("YYYY-MM-DD", date)

    raw_log = extract_raw_log(text)
    entries = parse_log_entries(raw_log)
    plan = plan_day_data(root, date)
    status = ", ".join(f"{key}={value}" for key, value in sorted(plan["status_counts"].items()))
    due = ", ".join(f"`{item['slug']}`" for item in plan["due_reviews"]) or "0"
    recommended = plan.get("recommended_next")
    recommended_text = f"`{recommended['slug']}` ({recommended['reason']})" if recommended else "None"
    goal = args.goal or (
        f"Active list `{plan['active_list']}`: "
        f"{plan['targets']['new_problems']} new, {plan['targets']['review_problems']} review."
    )
    takeaways = args.takeaways or [entry.get("summary", "") for entry in entries]
    next_values = clean_lines([entry.get("next", "") for entry in entries])
    next_text = args.next.strip() if args.next.strip() else (next_values[-1] if next_values else f"Continue with {recommended_text}.")

    output = [
        f"# Study Session - {date}",
        "",
        "## Goal",
        "",
        f"- {goal}",
        "",
        "## Progress Snapshot",
        "",
        f"- Active list: `{plan['active_list']}`",
        f"- Daily target: {plan['targets']['new_problems']} new, {plan['targets']['review_problems']} review",
        f"- Problems initialized: {plan['problem_count']}",
        f"- Status: {status}",
        f"- Due reviews: {due}",
        f"- Recommended next: {recommended_text}",
        "",
        "## Problems",
        "",
        format_problem_rows(entries).rstrip(),
        "",
        "## Takeaways",
        "",
        format_bullets(takeaways).rstrip(),
        "",
        "## Next Session",
        "",
        f"- {next_text}",
        "",
        "## Raw Log",
        "",
        raw_log or "No raw log entries recorded.",
        "",
    ]
    path.write_text("\n".join(output), encoding="utf-8")
    print(f"Finalized session: {path}")
    return 0


def command_plugin_files(args: argparse.Namespace) -> int:
    root = root_from_args(args)
    matches = matching_plugin_files(root, args.slug, args.problem_id)
    items = matches if (args.slug or args.problem_id is not None) else plugin_files(root)
    if not items:
        print("No plugin files found.")
        return 1
    for item in items:
        print(f"{item.get('id') or '?'} [{item.get('lang') or '?'}] {item['path']}")
    return 0


def render_note(template: str, meta: Dict[str, Any]) -> str:
    text = META_RE.sub(write_json_block(meta), template, count=1)
    title = meta.get("title") or meta["slug"]
    link = f"https://leetcode.com/problems/{meta['slug']}/"
    text = text.replace("# Problem Title", f"# {title}", 1)
    text = text.replace("https://leetcode.com/problems/", link, 1)
    return text


def command_init_problem(args: argparse.Namespace) -> int:
    root = root_from_args(args)
    existing = find_problem(root, args.slug)
    lists = list(dict.fromkeys(args.lists or []))
    tags = split_csv(args.tags)

    if existing:
        path, meta = existing
        merged_lists = list(dict.fromkeys(list(meta.get("lists", [])) + lists))
        merged_tags = list(dict.fromkeys(list(meta.get("tags", [])) + tags))
        updates = {
            "id": args.problem_id if args.problem_id is not None else meta.get("id"),
            "title": args.title or meta.get("title") or args.slug,
            "difficulty": args.difficulty or meta.get("difficulty") or "",
            "tags": merged_tags,
            "lists": merged_lists,
        }
        updated = update_note_meta(path, updates)
        print(f"Updated existing problem: {updated.get('slug')} -> {path}")
        return 0

    if args.problem_id is None:
        print("--id is required when creating a new problem", file=sys.stderr)
        return 2

    meta = {
        "id": args.problem_id,
        "slug": args.slug,
        "title": args.title or args.slug,
        "difficulty": args.difficulty or "",
        "tags": tags,
        "lists": lists,
        "status": "Todo",
        "mastery": "new",
        "last_practiced": None,
        "next_review": None,
        "mistake_tags": [],
    }

    folder = problem_dir(root, args.problem_id, args.slug)
    folder.mkdir(parents=True, exist_ok=True)
    note_path = folder / "note.md"
    solution_path = folder / "solution.py"
    note_template = (root / "templates" / "problem-note.md").read_text(encoding="utf-8")
    note_path.write_text(render_note(note_template, meta), encoding="utf-8")
    template_solution = root / "templates" / "solution.py"
    if template_solution.exists() and not solution_path.exists():
        shutil.copyfile(template_solution, solution_path)
    print(f"Created problem: {args.slug} -> {folder}")
    return 0


def next_review_from_args(args: argparse.Namespace) -> Optional[str]:
    if args.next_review:
        return args.next_review
    if args.review_in_days is not None:
        return (dt.date.today() + dt.timedelta(days=args.review_in_days)).isoformat()
    if args.status == "Review":
        return (dt.date.today() + dt.timedelta(days=1)).isoformat()
    if args.mastery == "solid":
        return (dt.date.today() + dt.timedelta(days=30)).isoformat()
    if args.mastery == "ok":
        return (dt.date.today() + dt.timedelta(days=7)).isoformat()
    if args.mastery == "shaky":
        return (dt.date.today() + dt.timedelta(days=1)).isoformat()
    return None


def command_finish(args: argparse.Namespace) -> int:
    root = root_from_args(args)
    found = find_problem(root, args.slug)
    if not found:
        print(f"Problem not found: {args.slug}", file=sys.stderr)
        return 1
    path, meta = found
    mistake_tags = split_csv(args.mistake_tags)
    merged_mistakes = list(dict.fromkeys(list(meta.get("mistake_tags", [])) + mistake_tags))
    updates = {
        "status": args.status,
        "mastery": args.mastery,
        "last_practiced": args.date or today(),
        "next_review": next_review_from_args(args),
        "mistake_tags": merged_mistakes,
    }
    updated = update_note_meta(path, updates)
    print("Updated progress:")
    print_problem_line(updated)
    return 0


def command_log_session(args: argparse.Namespace) -> int:
    root = root_from_args(args)
    date = args.date or today()
    session_dir = root / "study" / "sessions"
    session_dir.mkdir(parents=True, exist_ok=True)
    path = session_dir / f"{date}.md"
    if not path.exists():
        template = (root / "templates" / "session.md").read_text(encoding="utf-8")
        path.write_text(template.replace("YYYY-MM-DD", date), encoding="utf-8")
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n## Log Entry\n\n")
        if args.problems:
            handle.write(f"- Problems: {args.problems}\n")
        if args.summary:
            handle.write(f"- Summary: {args.summary}\n")
        if args.next:
            handle.write(f"- Next: {args.next}\n")
    print(f"Updated session: {path}")
    return 0


def command_archive_solution(args: argparse.Namespace) -> int:
    root = root_from_args(args)
    found = find_problem(root, args.slug)
    if not found:
        print(f"Problem not found: {args.slug}. Initialize it before archiving.", file=sys.stderr)
        return 1
    note_path, meta = found
    problem_id = meta.get("id")

    source_path: Optional[Path] = Path(args.source).expanduser().resolve() if args.source else None
    if args.from_plugin:
        matches = matching_plugin_files(root, args.slug, problem_id)
        if not matches:
            print(f"No plugin file found for {args.slug} / id={problem_id}", file=sys.stderr)
            return 1
        if len(matches) > 1 and not args.source:
            print("Multiple plugin files matched; pass --source:", file=sys.stderr)
            for item in matches:
                print(f"- {item['path']}", file=sys.stderr)
            return 2
        source_path = Path(matches[0]["path"])

    if source_path is None:
        print("Provide --from-plugin or --source", file=sys.stderr)
        return 2
    if not source_path.exists():
        print(f"Source file not found: {source_path}", file=sys.stderr)
        return 1

    code = extract_leetcode_code(source_path) if args.extract_lc_block else source_path.read_text(encoding="utf-8")
    solution_path = note_path.parent / "solution.py"
    header = (
        f"# Archived from VS Code LeetCode plugin file: {source_path.name}\n"
        f"# Problem: {meta.get('id')} {meta.get('title') or meta.get('slug')}\n\n"
    )
    solution_path.write_text(header + code, encoding="utf-8")
    print(f"Archived solution: {solution_path}")
    return 0


def validate_meta(path: Path, meta: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    required = ["id", "slug", "title", "difficulty", "tags", "lists", "status", "mastery"]
    for key in required:
        if key not in meta:
            errors.append(f"{path}: missing {key}")
    if meta.get("status") not in STATUSES:
        errors.append(f"{path}: invalid status {meta.get('status')}")
    if meta.get("mastery") not in MASTERIES:
        errors.append(f"{path}: invalid mastery {meta.get('mastery')}")
    if not isinstance(meta.get("tags", []), list):
        errors.append(f"{path}: tags must be a list")
    if not isinstance(meta.get("lists", []), list):
        errors.append(f"{path}: lists must be a list")
    for key in ("last_practiced", "next_review"):
        value = meta.get(key)
        if value:
            try:
                parse_date(value)
            except ValueError:
                errors.append(f"{path}: invalid date in {key}: {value}")
    return errors


def command_check(args: argparse.Namespace) -> int:
    root = root_from_args(args)
    errors: List[str] = []
    seen_slugs: Dict[str, str] = {}
    list_refs: Dict[str, set[str]] = {}
    for list_path in (root / "lists").glob("*.md"):
        list_refs[list_path.stem] = set(list_slugs(root, list_path.stem))

    for path in note_paths(root):
        try:
            meta = read_meta(path)
            errors.extend(validate_meta(path, meta))
            slug = meta.get("slug")
            if slug in seen_slugs:
                errors.append(f"duplicate slug {slug}: {seen_slugs[slug]} and {path}")
            seen_slugs[slug] = str(path)
            problem_id = meta.get("id")
            if isinstance(problem_id, int) and problem_id >= 0:
                expected_parent = problem_dir(root, problem_id, slug)
                if path.parent != expected_parent:
                    errors.append(f"{path}: expected directory {expected_parent}")
            for list_name in meta.get("lists", []):
                if list_name in list_refs and slug not in list_refs[list_name]:
                    errors.append(f"{path}: list '{list_name}' does not reference `{slug}`")
        except Exception as exc:  # noqa: BLE001 - check should report any broken note.
            errors.append(f"{path}: {exc}")

    if errors:
        print("Workspace check failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Workspace check passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage a LeetCode study workspace.")
    parser.add_argument("--root", help="Workspace root. Defaults to the parent of this script.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    status = subparsers.add_parser("status", help="Show study progress.")
    status.add_argument("--brief", action="store_true")
    status.set_defaults(func=command_status)

    next_cmd = subparsers.add_parser("next", help="Recommend the next problem.")
    next_cmd.set_defaults(func=command_next)

    due = subparsers.add_parser("due", help="List reviews due today.")
    due.add_argument("--date", help="Override date in YYYY-MM-DD format.")
    due.set_defaults(func=command_due)

    plan = subparsers.add_parser("plan-day", help="Plan today's reviews and new problems.")
    plan.add_argument("--date", help="Override date in YYYY-MM-DD format.")
    plan.set_defaults(func=command_plan_day)

    plugin = subparsers.add_parser("plugin-files", help="List VS Code LeetCode plugin files.")
    plugin.add_argument("--slug", help="Filter by local problem slug.")
    plugin.add_argument("--id", dest="problem_id", type=int, help="Filter by LeetCode frontend ID.")
    plugin.set_defaults(func=command_plugin_files)

    init = subparsers.add_parser("init-problem", help="Create or update a problem note.")
    init.add_argument("--id", dest="problem_id", type=int, help="LeetCode frontend ID.")
    init.add_argument("--slug", required=True)
    init.add_argument("--title", default="")
    init.add_argument("--difficulty", default="")
    init.add_argument("--tags", default="", help="Comma-separated tags.")
    init.add_argument("--list", dest="lists", action="append", default=[], help="Study list name. Repeatable.")
    init.set_defaults(func=command_init_problem)

    finish = subparsers.add_parser("finish", help="Update progress for a problem.")
    finish.add_argument("--slug", required=True)
    finish.add_argument("--status", choices=sorted(STATUSES), required=True)
    finish.add_argument("--mastery", choices=sorted(MASTERIES), required=True)
    finish.add_argument("--mistake-tags", default="", help="Comma-separated mistake tags.")
    finish.add_argument("--next-review", help="Explicit next review date YYYY-MM-DD.")
    finish.add_argument("--review-in-days", type=int, help="Set next review relative to today.")
    finish.add_argument("--date", help="Practice date YYYY-MM-DD. Defaults to today.")
    finish.set_defaults(func=command_finish)

    log = subparsers.add_parser("log-session", help="Append a daily session log entry.")
    log.add_argument("--date", help="Session date YYYY-MM-DD. Defaults to today.")
    log.add_argument("--problems", default="")
    log.add_argument("--summary", default="")
    log.add_argument("--next", default="")
    log.set_defaults(func=command_log_session)

    finalize = subparsers.add_parser("finalize-session", help="Rewrite a daily session into structured form.")
    finalize.add_argument("--date", help="Session date YYYY-MM-DD. Defaults to today.")
    finalize.add_argument("--goal", default="")
    finalize.add_argument("--takeaway", dest="takeaways", action="append", default=[], help="Session takeaway. Repeatable.")
    finalize.add_argument("--next", default="")
    finalize.set_defaults(func=command_finalize_session)

    archive = subparsers.add_parser("archive-solution", help="Archive a solution into the problem folder.")
    archive.add_argument("--slug", required=True)
    archive.add_argument("--from-plugin", action="store_true", help="Find the matching plugin file under workspace/leetcode.")
    archive.add_argument("--source", help="Explicit source file path.")
    archive.add_argument("--extract-lc-block", action=argparse.BooleanOptionalAction, default=True)
    archive.set_defaults(func=command_archive_solution)

    check = subparsers.add_parser("check", help="Validate workspace consistency.")
    check.set_defaults(func=command_check)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
