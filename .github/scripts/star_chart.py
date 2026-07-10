#!/usr/bin/env python3
"""Render assets/star-history-{dark,light}.svg from GitHub stargazer data.

Self-hosted replacement for the star-history.com embed: their SVG endpoint
runs on a shared GitHub-token pool and 503s whenever it gets rate-limited,
which makes the README image disappear. This pulls starred_at timestamps
straight from the GitHub API and draws the chart itself. Stdlib only.
"""

import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = os.environ.get("REPO", "runpantheon/ltui")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT_DIR = Path(__file__).resolve().parents[2] / "assets"

W, H = 800, 420
ML, MR, MT, MB = 60, 36, 46, 52  # margins

THEMES = {
    "dark": {
        "bg": "#0d0d0d",
        "line": "#e8e8e8",
        "fill": "#e8e8e8",
        "grid": "#262626",
        "axis": "#3a3a3a",
        "text": "#a0a0a0",
        "title": "#e8e8e8",
    },
    "light": {
        "bg": "#ffffff",
        "line": "#0d0d0d",
        "fill": "#0d0d0d",
        "grid": "#ececec",
        "axis": "#d0d0d0",
        "text": "#666666",
        "title": "#0d0d0d",
    },
}


def fetch_star_dates() -> list[datetime]:
    dates, page = [], 1
    while True:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{REPO}/stargazers"
            f"?per_page=100&page={page}",
            headers={
                "Accept": "application/vnd.github.star+json",
                "X-GitHub-Api-Version": "2022-11-28",
                **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            batch = json.load(resp)
        if not batch:
            break
        dates += [
            datetime.fromisoformat(s["starred_at"].replace("Z", "+00:00"))
            for s in batch
        ]
        if len(batch) < 100:
            break
        page += 1
    return sorted(dates)


def nice_ceiling(n: int) -> int:
    if n <= 10:
        return max(n, 4)
    for step in (5, 10, 20, 25, 50, 100, 200, 250, 500, 1000):
        if n <= step * 5:
            return ((n + step - 1) // step) * step
    return n


def render(dates: list[datetime], theme: dict) -> str:
    now = datetime.now(timezone.utc)
    total = len(dates)
    t0, t1 = dates[0], now
    span = max((t1 - t0).total_seconds(), 1.0)
    y_max = nice_ceiling(total)

    def x(t: datetime) -> float:
        return ML + (t - t0).total_seconds() / span * (W - ML - MR)

    def y(n: float) -> float:
        return H - MB - n / y_max * (H - MT - MB)

    # cumulative step points, extended to "now"
    pts = [(x(t0), y(0))]
    for i, d in enumerate(dates):
        pts.append((x(d), y(i)))
        pts.append((x(d), y(i + 1)))
    pts.append((x(t1), y(total)))
    path = " ".join(f"{px:.1f},{py:.1f}" for px, py in pts)
    area = f"{ML},{y(0):.1f} {path} {x(t1):.1f},{y(0):.1f}"

    grid, labels = [], []
    for i in range(5):  # horizontal gridlines + y labels
        n = y_max * i / 4
        gy = y(n)
        grid.append(
            f'<line x1="{ML}" y1="{gy:.1f}" x2="{W - MR}" y2="{gy:.1f}" '
            f'stroke="{theme["grid"]}" stroke-width="1"/>'
        )
        labels.append(
            f'<text x="{ML - 10}" y="{gy + 4:.1f}" text-anchor="end" '
            f'fill="{theme["text"]}" font-size="12">{int(n)}</text>'
        )
    for i in range(4):  # x date labels
        t = t0 + (t1 - t0) * i / 3
        anchor = ("start", "middle", "middle", "end")[i]
        labels.append(
            f'<text x="{x(t):.1f}" y="{H - MB + 22}" text-anchor="{anchor}" '
            f'fill="{theme["text"]}" font-size="12">{t.strftime("%b %d, %Y")}</text>'
        )

    ex, ey = x(t1), y(total)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="ui-monospace, 'JetBrains Mono', 'SFMono-Regular', Menlo, monospace">
  <rect width="{W}" height="{H}" rx="10" fill="{theme["bg"]}"/>
  <text x="{ML}" y="28" fill="{theme["title"]}" font-size="15" font-weight="bold">{REPO}</text>
  <text x="{W - MR}" y="28" text-anchor="end" fill="{theme["text"]}" font-size="13">github stars</text>
  {"".join(grid)}
  <line x1="{ML}" y1="{MT}" x2="{ML}" y2="{H - MB}" stroke="{theme["axis"]}" stroke-width="1"/>
  <line x1="{ML}" y1="{H - MB}" x2="{W - MR}" y2="{H - MB}" stroke="{theme["axis"]}" stroke-width="1"/>
  <polygon points="{area}" fill="{theme["fill"]}" opacity="0.08"/>
  <polyline points="{path}" fill="none" stroke="{theme["line"]}" stroke-width="2" stroke-linejoin="round"/>
  <circle cx="{ex:.1f}" cy="{ey:.1f}" r="4" fill="{theme["line"]}"/>
  <text x="{min(ex, W - MR - 8):.1f}" y="{ey - 12:.1f}" text-anchor="end" fill="{theme["title"]}" font-size="14" font-weight="bold">&#9733; {total}</text>
  {"".join(labels)}
  <text x="{W - MR}" y="{H - 14}" text-anchor="end" fill="{theme["text"]}" font-size="10">updated {now.strftime("%Y-%m-%d")}</text>
</svg>
'''


def stale(dates: list[datetime]) -> bool:
    """Rewrite only when the count changed or the chart is a week old —
    otherwise the daily cron would commit every run (the 'now' endpoint
    of the line always moves a little)."""
    try:
        old = (OUT_DIR / "star-history-dark.svg").read_text()
        count = int(re.search(r"&#9733; (\d+)<", old)[1])
        drawn = datetime.strptime(
            re.search(r"updated (\d{4}-\d{2}-\d{2})<", old)[1], "%Y-%m-%d"
        ).replace(tzinfo=timezone.utc)
    except Exception:
        return True
    return count != len(dates) or (datetime.now(timezone.utc) - drawn).days >= 7


def main() -> None:
    dates = fetch_star_dates()
    if not dates:
        print("no stargazers returned — leaving existing charts alone")
        return
    if not stale(dates):
        print(f"chart already current ({len(dates)} stars) — skipping")
        return
    OUT_DIR.mkdir(exist_ok=True)
    for name, theme in THEMES.items():
        out = OUT_DIR / f"star-history-{name}.svg"
        out.write_text(render(dates, theme))
        print(f"wrote {out} ({len(dates)} stars)")


if __name__ == "__main__":
    sys.exit(main())
