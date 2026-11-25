"""Build the SVG progress card shown in README.md and on the GitHub profile.

The card adapts to light and dark mode on its own, so it looks right
for every visitor.
"""
from datetime import timedelta
from xml.sax.saxutils import escape

WEEKS = 26
CELL = 15
GAP = 4
STEP = CELL + GAP
PAD = 24
LABEL_W = 32
WIDTH = PAD * 2 + LABEL_W + WEEKS * STEP - GAP
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

STYLE = """
  <style>
    .bg { fill: #ffffff; stroke: #d0d7de; }
    .title { font: 600 18px -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif; fill: #1f2328; }
    .num { font: 600 22px -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif; fill: #1f2328; }
    .lbl { font: 400 12px -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif; fill: #59636e; }
    .txt { font: 400 13px -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif; fill: #1f2328; }
    .sml { font: 400 11px -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif; fill: #59636e; }
    .line { stroke: #d0d7de; }
    .c0 { fill: #ebedf0; }
    .c1 { fill: #40c463; }
    .fut { fill: #f6f8fa; }
    .today { stroke: #1f2328; stroke-width: 1; }
    @media (prefers-color-scheme: dark) {
      .bg { fill: #0d1117; stroke: #30363d; }
      .title, .num, .txt { fill: #e6edf3; }
      .lbl, .sml { fill: #9198a1; }
      .line { stroke: #30363d; }
      .c0 { fill: #161b22; }
      .c1 { fill: #39d353; }
      .fut { fill: #11151b; }
      .today { stroke: #e6edf3; }
    }
  </style>"""


def _shorten(text, limit):
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def build_card(entries, today, current, longest):
    days = {e["date"] for e in entries}
    this_monday = today - timedelta(days=today.weekday())
    first = min(days) if days else today
    start = first - timedelta(days=first.weekday())
    latest_start = this_monday - timedelta(weeks=WEEKS - 1)
    if start < latest_start:
        start = latest_start
    parts = []

    y = PAD + 6
    parts.append(f'<text class="title" x="{PAD}" y="{y + 12}">Learning log</text>')
    if entries:
        last = max(days).strftime("%d-%m-%Y")
        parts.append(f'<text class="lbl" x="{WIDTH - PAD}" y="{y + 12}" text-anchor="end">last entry {last}</text>')

    y += 36
    stats = [(len(entries), "entries"), (current, "day streak"), (longest, "longest streak")]
    col = (WIDTH - PAD * 2) / 3
    for i, (value, label) in enumerate(stats):
        x = PAD + i * col
        parts.append(f'<text class="num" x="{x:.0f}" y="{y + 20}">{value}</text>')
        parts.append(f'<text class="lbl" x="{x:.0f}" y="{y + 38}">{label}</text>')

    y += 62
    grid_x = PAD + LABEL_W
    previous_month = None
    for w in range(WEEKS):
        month = (start + timedelta(weeks=w)).month
        if month != previous_month:
            if w == 0 or w < WEEKS - 2:
                parts.append(f'<text class="sml" x="{grid_x + w * STEP}" y="{y}">{MONTHS[month - 1]}</text>')
            previous_month = month

    y += 6
    for row, name in ((0, "Mon"), (2, "Wed"), (4, "Fri")):
        parts.append(f'<text class="sml" x="{PAD}" y="{y + row * STEP + 11}">{name}</text>')
    for w in range(WEEKS):
        for d in range(7):
            day = start + timedelta(weeks=w, days=d)
            if day > today:
                cls = "fut"
            else:
                cls = "c1" if day in days else "c0"
            extra = ' class="today"' if day == today else ""
            parts.append(
                f'<rect class="{cls}" x="{grid_x + w * STEP}" y="{y + d * STEP}" '
                f'width="{CELL}" height="{CELL}" rx="2"/>'
                + (f'<rect{extra} x="{grid_x + w * STEP + 0.5}" y="{y + d * STEP + 0.5}" '
                   f'width="{CELL - 1}" height="{CELL - 1}" rx="2" fill="none"/>' if extra else "")
            )

    y += 7 * STEP + 8
    lx = WIDTH - PAD - 2 * STEP - 74
    parts.append(f'<text class="sml" x="{lx}" y="{y + 11}">no entry</text>')
    parts.append(f'<rect class="c0" x="{lx + 50}" y="{y}" width="{CELL}" height="{CELL}" rx="2"/>')
    parts.append(f'<rect class="c1" x="{lx + 50 + STEP}" y="{y}" width="{CELL}" height="{CELL}" rx="2"/>')
    parts.append(f'<text class="sml" x="{lx + 50 + 2 * STEP + 4}" y="{y + 11}">entry</text>')

    latest = sorted(entries, key=lambda e: e["date"], reverse=True)[:3]
    if latest:
        y += 28
        parts.append(f'<line class="line" x1="{PAD}" x2="{WIDTH - PAD}" y1="{y}" y2="{y}"/>')
        y += 22
        parts.append(f'<text class="lbl" x="{PAD}" y="{y}">Latest entries</text>')
        for e in latest:
            y += 22
            parts.append(f'<text class="sml" x="{PAD}" y="{y}">{e["date"].strftime("%d-%m-%Y")}</text>')
            parts.append(f'<text class="txt" x="{PAD + 70}" y="{y}">{escape(_shorten(e["topic"], 64))}</text>')

    height = y + PAD
    body = "\n  ".join(parts)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" role="img" aria-label="Learning log progress">{STYLE}\n'
        f'  <rect class="bg" x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" rx="8"/>\n'
        f"  {body}\n</svg>\n"
    )
