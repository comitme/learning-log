#!/usr/bin/env python3
"""Refresh the stats and the entry index in README.md.

Usage: python scripts/update_index.py
"""
import argparse
import re
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRIES = ROOT / "entries"
README = ROOT / "README.md"
START = "<!-- INDEX:START -->"
END = "<!-- INDEX:END -->"
FILE_NAME = re.compile(r"^(\d{2})-(\d{2})-(\d{4})\.md$")
DATE_FORMAT = "%d-%m-%Y"


def field(text, name):
    match = re.search(rf"^- \*\*{name}:\*\*[ \t]*(.*)$", text, re.M)
    return match.group(1).strip() if match else ""


def load_entries():
    entries = []
    for path in ENTRIES.glob("*/*.md"):
        match = FILE_NAME.match(path.name)
        if not match:
            continue
        text = path.read_text(encoding="utf-8")
        entries.append(
            {
                "date": date(int(match[3]), int(match[2]), int(match[1])),
                "path": path.relative_to(ROOT).as_posix(),
                "topic": field(text, "Topic") or "untitled",
                "tags": [t.strip() for t in field(text, "Tags").split(",") if t.strip()],
            }
        )
    return sorted(entries, key=lambda e: e["date"])


def plural(n, one, many):
    return one if n == 1 else many


def streaks(dates, today):
    days = set(dates)
    longest = current_run = 0
    for d in sorted(days):
        current_run = current_run + 1 if (d - timedelta(days=1)) in days else 1
        longest = max(longest, current_run)
    day = today if today in days else today - timedelta(days=1)
    current = 0
    while day in days:
        current += 1
        day -= timedelta(days=1)
    return current, longest


def activity_bar(dates, today, weeks=4):
    days = set(dates)
    span = [today - timedelta(days=i) for i in range(weeks * 7 - 1, -1, -1)]
    marks = ["■" if d in days else "·" for d in span]
    rows = [" ".join(marks[i : i + 7]) for i in range(0, len(marks), 7)]
    return "\n".join(rows)


def build_block(entries, today):
    if not entries:
        return (
            "No entries yet. Create the first one with:\n\n"
            '    python scripts/new_entry.py --topic "First entry"'
        )

    dates = [e["date"] for e in entries]
    current, longest = streaks(dates, today)
    total = len(entries)
    last = max(dates).strftime(DATE_FORMAT)

    lines = [
        f"**{total}** {plural(total, 'entry', 'entries')} · "
        f"streak: **{current}** {plural(current, 'day', 'days')} · "
        f"longest streak: **{longest}** {plural(longest, 'day', 'days')} · "
        f"last entry: {last}",
        "",
        "Last 4 weeks (■ marks a day with an entry):",
        "",
        "```",
        activity_bar(dates, today),
        "```",
        "",
    ]

    tags = Counter(t for e in entries for t in e["tags"])
    if tags:
        top = ", ".join(f"`{t}` ({c})" for t, c in tags.most_common(6))
        lines += [f"Most used tags: {top}", ""]

    lines += [
        "### Latest entries",
        "",
        "| Date | Topic | Tags |",
        "| --- | --- | --- |",
    ]
    for e in sorted(entries, key=lambda x: x["date"], reverse=True)[:10]:
        lines.append(
            f"| [{e['date'].strftime(DATE_FORMAT)}]({e['path']}) | {e['topic']} | {', '.join(e['tags'])} |"
        )

    lines += ["", "### All entries", ""]
    months = {}
    for e in entries:
        months.setdefault((e["date"].year, e["date"].month), []).append(e)
    for i, ((year, month), items) in enumerate(sorted(months.items(), reverse=True)):
        count = len(items)
        open_attr = " open" if i == 0 else ""
        lines.append(f"<details{open_attr}>")
        lines.append(f"<summary>{month:02d}-{year} ({count} {plural(count, 'entry', 'entries')})</summary>")
        lines.append("")
        for e in sorted(items, key=lambda x: x["date"], reverse=True):
            lines.append(f"- [{e['date'].strftime(DATE_FORMAT)}]({e['path']}) {e['topic']}")
        lines += ["", "</details>", ""]

    return "\n".join(lines).rstrip()


def main():
    parser = argparse.ArgumentParser(description="Odświeża spis wpisów w README.md.")
    parser.add_argument("--today", "--dzis", help="DD-MM-YYYY, tylko do testów")
    args = parser.parse_args()
    today = datetime.strptime(args.today, DATE_FORMAT).date() if args.today else date.today()

    text = README.read_text(encoding="utf-8")
    before, rest = text.split(START, 1)
    _, after = rest.split(END, 1)
    block = build_block(load_entries(), today)
    README.write_text(f"{before}{START}\n{block}\n{END}{after}", encoding="utf-8")
    print("README.md odświeżony.")


if __name__ == "__main__":
    main()
