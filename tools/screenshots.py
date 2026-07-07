#!/usr/bin/env python3
"""Generate README screenshots from fake demo data.

No API key needed and no network calls are made — the Linear client is
mocked, so the images never contain real workspace data.

    python tools/screenshots.py            # writes SVGs into assets/
    rsvg-convert -w 1600 assets/hero.svg -o assets/hero.png
"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ltui as mod
from ltui import LTUI

ASSETS = Path(__file__).resolve().parent.parent / "assets"

NOW = datetime.now(timezone.utc)


def ago(**kw) -> str:
    return (NOW - timedelta(**kw)).isoformat().replace("+00:00", "Z")


STATES = [
    {"id": "st-bl", "name": "Backlog", "color": "#95a2b3", "type": "backlog", "position": 0},
    {"id": "st-td", "name": "Todo", "color": "#e2e2e2", "type": "unstarted", "position": 1},
    {"id": "st-ip", "name": "In Progress", "color": "#f2c94c", "type": "started", "position": 2},
    {"id": "st-ir", "name": "In Review", "color": "#26b36b", "type": "started", "position": 3},
    {"id": "st-dn", "name": "Done", "color": "#5e6ad2", "type": "completed", "position": 4},
    {"id": "st-cn", "name": "Canceled", "color": "#95a2b3", "type": "canceled", "position": 5},
]
ST = {s["id"]: s for s in STATES}

L_BUG = {"name": "bug", "color": "#f38ba8"}
L_FEAT = {"name": "feature", "color": "#89b4fa"}
L_INFRA = {"name": "infra", "color": "#a6e3a1"}
L_UX = {"name": "design", "color": "#cba6f7"}

NOVA = {"id": "u-nova", "displayName": "nova"}
KAI = {"id": "u-kai", "displayName": "kai"}
REI = {"id": "u-rei", "displayName": "rei"}

TEAMS = [
    {"id": "t-core", "name": "Core", "key": "CORE", "color": "#89b4fa"},
    {"id": "t-infra", "name": "Infra", "key": "INFRA", "color": "#a6e3a1"},
    {"id": "t-web", "name": "Website", "key": "WEB", "color": "#fab387"},
]

DESC = """Split the monolithic sync engine into per-entity pipelines so a slow
webhook can't stall the whole queue.

## plan

1. Extract `SyncPipeline` interface with backpressure
2. Move webhook fan-out onto the new scheduler
3. Delete the old queue once soak tests pass

```rust
pub trait SyncPipeline {
    fn enqueue(&self, event: Event) -> Result<(), Backpressure>;
    fn drain(&self) -> impl Stream<Item = Event>;
}
```

> Soak test target: 50k events/min for 2h with zero drops.

- [x] design review
- [ ] scheduler swap behind flag
- [ ] delete legacy queue
"""

COMMENTS = [
    {
        "id": "c1",
        "body": "Benchmarks look great — the new scheduler holds **52k events/min** "
        "with p99 latency at 41ms. Ship it behind the flag.",
        "createdAt": ago(hours=7),
        "user": {"displayName": "kai"},
        "botActor": None,
    },
    {
        "id": "c2",
        "body": "Flag `sync.pipeline.v2` is live on staging. Soak test running, "
        "dashboard here: `grafana/sync-v2-soak`",
        "createdAt": ago(hours=3),
        "user": {"displayName": "nova"},
        "botActor": None,
    },
]


def issue(num, title, state, prio, assignee, labels, up_h, created_d=20, desc=None,
          blocks=(), blocked_by=()):
    return {
        "id": f"i-{num}",
        "identifier": f"CORE-{num}",
        "title": title,
        "description": desc,
        "url": "https://linear.app/demo/issue/CORE-1",
        "priority": prio,
        "updatedAt": ago(hours=up_h),
        "createdAt": ago(days=created_d),
        "state": ST[state],
        "assignee": assignee,
        "labels": {"nodes": labels},
        "relations": {"nodes": [
            {"type": "blocks", "relatedIssue": {"identifier": b}} for b in blocks
        ]},
        "inverseRelations": {"nodes": [
            {"type": "blocks", "issue": {"identifier": b}} for b in blocked_by
        ]},
    }


ISSUES = [
    # in review
    issue(128, "Split sync engine into per-entity pipelines", "st-ir", 1, NOVA, [L_INFRA], 3, desc=DESC, blocked_by=["CORE-134"]),
    issue(131, "Rate-limit invite spam from unverified workspaces", "st-ir", 2, KAI, [L_BUG], 6, blocked_by=["CORE-130"]),
    issue(119, "New onboarding checklist — empty states + confetti", "st-ir", 3, REI, [L_UX, L_FEAT], 11),
    # in progress
    issue(134, "Streaming exports: cursor pagination for 1M+ row tables", "st-ip", 1, NOVA, [L_FEAT], 1, blocks=["CORE-128"]),
    issue(133, "Fix flaky websocket reconnect on laptop sleep", "st-ip", 2, NOVA, [L_BUG], 4),
    issue(127, "Migrate search to the new tokenizer", "st-ip", 2, KAI, [L_INFRA], 9),
    issue(125, "Command palette: fuzzy match on ticket identifiers", "st-ip", 3, REI, [L_FEAT, L_UX], 14),
    issue(122, "Audit log retention policy + admin UI", "st-ip", 4, KAI, [L_FEAT], 26),
    # todo
    issue(136, "Zero-downtime schema migration runbook", "st-td", 2, NOVA, [L_INFRA], 5),
    issue(135, "Keyboard shortcut cheatsheet overlay", "st-td", 3, REI, [L_UX], 8),
    issue(130, "Dedupe webhook deliveries on retry storms", "st-td", 3, None, [L_BUG, L_INFRA], 30, blocks=["CORE-131"]),
    issue(126, "Dark mode for public status page", "st-td", 4, None, [L_UX], 41),
    # backlog
    issue(112, "Self-serve data residency picker (EU/US)", "st-bl", 0, None, [L_FEAT], 70),
    issue(108, "Native ARM builds for the desktop app", "st-bl", 0, None, [L_INFRA], 90),
    issue(104, "Investigate CRDT sync for offline mode", "st-bl", 0, None, [L_FEAT], 120),
    # done
    issue(129, "Ship per-workspace API rate dashboards", "st-dn", 2, NOVA, [L_FEAT], 20),
    issue(124, "Patch session fixation on OAuth callback", "st-dn", 1, KAI, [L_BUG], 32),
    issue(121, "Compress avatar uploads with AVIF", "st-dn", 3, REI, [L_UX], 50),
    # canceled
    issue(97, "Rewrite everything in a weekend", "st-cn", 0, None, [], 200),
]

BOOT = {
    "viewer": {"id": "u-nova", "displayName": "nova"},
    "organization": {"name": "nebula labs"},
    "teams": {"nodes": TEAMS},
}


class DemoApp(LTUI):
    async def gql(self, query, variables=None):
        await asyncio.sleep(0.02)
        if "organization" in query:
            return BOOT
        if "issues(first" in query:
            return {"team": {"issues": {"nodes": ISSUES}, "states": {"nodes": STATES}}}
        if "comments(first" in query:
            return {"issue": {"comments": {"nodes": COMMENTS}}}
        return {}


def patch(theme="mocha"):
    mod.load_api_key = lambda: "demo"
    mod.read_cache = lambda name: None
    mod.write_cache = lambda name, data: None
    mod.load_state = lambda: {"theme": theme, "mine": False, "team_id": "t-core"}
    mod.save_state = lambda data: None


async def shot(name, size=(148, 41), theme="mocha", drive=None):
    patch(theme)
    app = DemoApp()
    async with app.run_test(size=size) as pilot:
        for _ in range(40):
            await pilot.pause(0.1)
            if app.query_one("#issues").option_count > 0:
                break
        await pilot.pause(0.3)
        if drive:
            await drive(app, pilot)
        await pilot.pause(0.4)
        app.save_screenshot(str(ASSETS / f"{name}.svg"))
    print(f"  ✓ {name}.svg")


async def open_detail(app, pilot):
    await pilot.press("enter")
    for _ in range(20):
        await pilot.pause(0.15)
        if app.query_one("#d-comments").children:
            break


async def open_picker(app, pilot):
    await open_detail(app, pilot)
    await pilot.press("s")


async def open_new(app, pilot):
    await pilot.press("n")
    await pilot.pause(0.2)
    for ch in "Add per-team webhook signing secrets":
        await pilot.press(ch if ch != " " else "space")
    await pilot.press("enter")
    for ch in "Rotate on demand, verify with `X-Signature` header.":
        if ch == " ":
            await pilot.press("space")
        elif ch.isalnum() or ch in "-,.`X":
            await pilot.press(ch)


async def open_comment(app, pilot):
    await open_detail(app, pilot)
    await pilot.press("c")


async def open_settings(app, pilot):
    await pilot.press("comma")


async def onboard_shot(name, size=(148, 41)):
    patch("mocha")
    def no_key():
        raise FileNotFoundError("no key configured")
    mod.load_api_key = no_key
    app = DemoApp()
    async with app.run_test(size=size) as pilot:
        await pilot.pause(0.6)
        app.save_screenshot(str(ASSETS / f"{name}.svg"))
    print(f"  \u2713 {name}.svg")


async def open_themes(app, pilot):
    app.action_change_theme()
    await pilot.pause(0.3)
    await pilot.press("j")  # preview the next theme live


async def main():
    ASSETS.mkdir(exist_ok=True)
    print("generating demo screenshots (fake data, no network)…")
    await shot("hero", size=(168, 44), drive=open_detail)
    await shot("list", size=(148, 41))
    await shot("picker", size=(148, 41), drive=open_picker)
    await shot("new-ticket", size=(148, 41), drive=open_new)
    await shot("comment", size=(148, 41), drive=open_comment)
    await shot("settings", size=(148, 41), drive=open_settings)
    await shot("themes", size=(148, 41), drive=open_themes)
    await onboard_shot("onboard")
    await shot("theme-void", size=(148, 41), theme="void")
    await shot("theme-onyx", size=(148, 41), theme="onyx")
    print("done — convert with: for f in assets/*.svg; rsvg-convert -w 1600 $f -o (string replace .svg .png $f); end")


if __name__ == "__main__":
    asyncio.run(main())
