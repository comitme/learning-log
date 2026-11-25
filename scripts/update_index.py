#!/usr/bin/env python3
"""Refresh the stats and the entry index in README.md.

Usage: python scripts/update_index.py
"""
import argparse
import re
import sys
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from card import build_card  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ENTRIES = ROOT / "entries"
README = ROOT / "README.md"
START = "<!-- INDEX:START -->"
END = "<!-- INDEX:END -->"
FILE_NAME = re.compile(r"^(\d{2})-(\d{2})-(\d{4})\.md$")
DATE_FORMAT = "%d-%m-%Y"
CARD_PATH = "assets/card.svg"
CARD = ROOT / CARD_PATH


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


def safe(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("|", "\\|")


def tag_badges(tags):
    return " ".join(f"`{t}`&nbsp;{c}" for t, c in tags)


def build_block(entries, today):
    if not entries:
        return "The first entry is coming soon."

    lines = [
        '<p align="center">',
        f'  <img src="{CARD_PATH}" alt="Learning log progress: entries, streak and activity">',
        "</p>",
        "",
    ]

    tags = Counter(t for e in entries for t in e["tags"])
    if tags:
        lines += [f"**Most used tags:** {tag_badges(tags.most_common(8))}", ""]

    lines += [
        "### Latest entries",
        "",
        "| Date | Topic | Tags |",
        "| :--- | :--- | :--- |",
    ]
    for e in sorted(entries, key=lambda x: x["date"], reverse=True)[:10]:
        tag_cells = " ".join(f"`{t}`" for t in e["tags"])
        lines.append(f"| [{e['date'].strftime(DATE_FORMAT)}]({e['path']}) | {safe(e['topic'])} | {tag_cells} |")

    lines += ["", "<details>", "<summary><b>All entries by month</b></summary>", ""]
    months = {}
    for e in entries:
        months.setdefault((e["date"].year, e["date"].month), []).append(e)
    for (year, month), items in sorted(months.items(), reverse=True):
        count = len(items)
        lines += ["", f"**{month:02d}-{year}** ({count} {plural(count, 'entry', 'entries')})", ""]
        for e in sorted(items, key=lambda x: x["date"], reverse=True):
            lines.append(f"- [{e['date'].strftime(DATE_FORMAT)}]({e['path']}) {safe(e['topic'])}")
    lines += ["", "</details>"]

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Odświeża spis wpisów w README.md.")
    parser.add_argument("--today", "--dzis", help="DD-MM-YYYY, tylko do testów")
    args = parser.parse_args()
    today = datetime.strptime(args.today, DATE_FORMAT).date() if args.today else date.today()

    text = README.read_text(encoding="utf-8")
    before, rest = text.split(START, 1)
    _, after = rest.split(END, 1)
    entries = load_entries()
    current, longest = streaks([e["date"] for e in entries], today)
    CARD.parent.mkdir(exist_ok=True)
    CARD.write_text(build_card(entries, today, current, longest), encoding="utf-8")
    block = build_block(entries, today)
    README.write_text(f"{before}{START}\n{block}\n{END}{after}", encoding="utf-8")
    print("README.md i assets/card.svg odświeżone.")


if __name__ == "__main__":
    main()
