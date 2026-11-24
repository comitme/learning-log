#!/usr/bin/env python3
"""Create today's entry from the template.

Examples:
    python scripts/new_entry.py
    python scripts/new_entry.py --topic "Pandas: groupby and agg"
    python scripts/new_entry.py --date 21-11-2026
"""
import argparse
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATE_FORMAT = "%d-%m-%Y"


def main():
    parser = argparse.ArgumentParser(description="Tworzy wpis z szablonu.")
    parser.add_argument("--topic", "--temat", default="", help="krótki temat wpisu")
    parser.add_argument("--date", "--data", help="DD-MM-YYYY, domyślnie dzisiaj")
    args = parser.parse_args()

    day = datetime.strptime(args.date, DATE_FORMAT).date() if args.date else date.today()
    label = day.strftime(DATE_FORMAT)
    folder = ROOT / "entries" / day.strftime("%m-%Y")
    path = folder / f"{label}.md"

    if path.exists():
        print(f"Wpis już istnieje: {path.relative_to(ROOT)}")
        return

    folder.mkdir(parents=True, exist_ok=True)
    number = len(list((ROOT / "entries").glob("*/*.md"))) + 1
    template = (ROOT / "templates" / "entry.md").read_text(encoding="utf-8")
    content = (
        template.replace("{{DATE}}", label)
        .replace("{{NUMBER}}", str(number))
        .replace("{{TOPIC}}", args.topic)
    )
    path.write_text(content, encoding="utf-8")

    print(f"Utworzono: {path.relative_to(ROOT)}")
    print("Uzupełnij wpis, a potem wyślij go na GitHub:")
    print(f'  git add . && git commit -m "Entry {label}" && git push')


if __name__ == "__main__":
    main()
