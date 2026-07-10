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

import jtui as mod
from jtui import JTUI

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
    {"id": "CORE", "name": "Core", "key": "CORE", "color": "#89b4fa"},
    {"id": "INFRA", "name": "Infra", "key": "INFRA", "color": "#a6e3a1"},
    {"id": "WEB", "name": "Website", "key": "WEB", "color": "#fab387"},
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


PARENT = {"identifier": "CORE-100", "title": "Sync engine v2"}

CHILDREN = [
    {
        "identifier": "CORE-141",
        "title": "Backpressure-aware scheduler core",
        "state": ST["st-dn"],
    },
    {
        "identifier": "CORE-142",
        "title": "Move webhook fan-out onto the new scheduler",
        "state": ST["st-ip"],
    },
]


P_SYNC = {"id": "p-sync", "name": "Sync Engine v2", "color": "#89b4fa"}
P_POLISH = {"id": "p-polish", "name": "Q3 Polish", "color": "#cba6f7"}
P_INFRA = {"id": "p-infra", "name": "Infra Hardening", "color": "#a6e3a1"}


def issue(num, title, state, prio, assignee, labels, up_h, created_d=20, desc=None,
          blocks=(), blocked_by=(), parent=None, project=None, children=()):
    return {
        "id": f"i-{num}",
        "identifier": f"CORE-{num}",
        "title": title,
        "description": desc,
        "url": "https://linear.app/demo/issue/CORE-1",
        "priority": prio,
        "branchName": f"nova/core-{num}-demo-branch",
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
        "parent": parent,
        "project": project,
        "subtasks": list(children),
    }


ISSUES = [
    # in review
    issue(128, "Split sync engine into per-entity pipelines", "st-ir", 1, NOVA, [L_INFRA], 3, desc=DESC, blocked_by=["CORE-134"], parent=PARENT, project=P_SYNC, children=CHILDREN),
    issue(131, "Rate-limit invite spam from unverified workspaces", "st-ir", 2, KAI, [L_BUG], 6, blocked_by=["CORE-130"]),
    issue(119, "New onboarding checklist — empty states + confetti", "st-ir", 3, REI, [L_UX, L_FEAT], 11, project=P_POLISH),
    # in progress
    issue(134, "Streaming exports: cursor pagination for 1M+ row tables", "st-ip", 1, NOVA, [L_FEAT], 1, blocks=["CORE-128"], project=P_SYNC),
    issue(133, "Fix flaky websocket reconnect on laptop sleep", "st-ip", 2, NOVA, [L_BUG], 4),
    issue(127, "Migrate search to the new tokenizer", "st-ip", 2, KAI, [L_INFRA], 9, project=P_SYNC),
    issue(125, "Command palette: fuzzy match on ticket identifiers", "st-ip", 3, REI, [L_FEAT, L_UX], 14, project=P_POLISH),
    issue(122, "Audit log retention policy + admin UI", "st-ip", 4, KAI, [L_FEAT], 26),
    # todo
    issue(136, "Zero-downtime schema migration runbook", "st-td", 2, NOVA, [L_INFRA], 5, project=P_INFRA),
    issue(135, "Keyboard shortcut cheatsheet overlay", "st-td", 3, REI, [L_UX], 8, project=P_POLISH),
    issue(130, "Dedupe webhook deliveries on retry storms", "st-td", 3, None, [L_BUG, L_INFRA], 30, blocks=["CORE-131"]),
    issue(126, "Dark mode for public status page", "st-td", 4, None, [L_UX], 41, project=P_POLISH),
    # backlog
    issue(112, "Self-serve data residency picker (EU/US)", "st-bl", 0, None, [L_FEAT], 70),
    issue(108, "Native ARM builds for the desktop app", "st-bl", 0, None, [L_INFRA], 90, project=P_INFRA),
    issue(104, "Investigate CRDT sync for offline mode", "st-bl", 0, None, [L_FEAT], 120),
    # done
    issue(129, "Ship per-workspace API rate dashboards", "st-dn", 2, NOVA, [L_FEAT], 20),
    issue(124, "Patch session fixation on OAuth callback", "st-dn", 1, KAI, [L_BUG], 32, project=P_INFRA),
    issue(121, "Compress avatar uploads with AVIF", "st-dn", 3, REI, [L_UX], 50),
    # canceled
    issue(97, "Rewrite everything in a weekend", "st-cn", 0, None, [], 200),
]

BOOT = {
    "viewer": {"id": "u-nova", "displayName": "nova"},
    "organization": {"name": "nebula labs"},
    "teams": {"nodes": TEAMS},
}


class DemoApp(JTUI):
    async def api(self, method, path, **kwargs):
        await asyncio.sleep(0.02)
        if path.endswith("/myself"):
            return {"accountId": "u-nova", "displayName": "nova"}
        if "project/search" in path:
            return {"values": [{"key": t["key"], "name": t["name"]} for t in TEAMS]}
        if path.endswith("/transitions") and method == "GET":
            return {"transitions": [
                {"id": "11", "name": "To Do",
                 "to": {"id": "1", "name": "To Do", "statusCategory": {"key": "new"}}},
                {"id": "21", "name": "Start progress",
                 "to": {"id": "2", "name": "In Progress", "statusCategory": {"key": "indeterminate"}}},
                {"id": "31", "name": "Done",
                 "to": {"id": "3", "name": "Done", "statusCategory": {"key": "done"}}},
            ]}
        if "assignable" in path:
            return [
                {"accountId": u["id"], "displayName": u["displayName"]}
                for u in (NOVA, KAI, REI)
            ]
        if path.endswith("/comment") and method == "GET":
            return {"comments": [
                {"id": c["id"], "body": c["body"], "created": c["createdAt"],
                 "author": {"displayName": c["user"]["displayName"]}}
                for c in COMMENTS
            ]}
        if "/rest/api/2/label" in path:
            return {"values": ["bug", "feature", "infra", "design"]}
        if "issuetype = Epic" in (kwargs.get("params") or {}).get("jql", ""):
            return {"issues": [
                {"key": "CORE-100", "fields": {"summary": "Sync engine v2"}},
                {"key": "CORE-200", "fields": {"summary": "Q3 Polish"}},
            ]}
        if method == "PUT" and "/rest/api/2/issue/" in path:
            return None  # 204-style: labels / parent updates
        if method == "POST" and path.endswith("/rest/api/2/issue"):
            fields = (kwargs.get("json") or {}).get("fields") or {}
            if (fields.get("issuetype") or {}).get("name") == "Epic":
                return {"key": "CORE-900"}
        return {}

    async def fetch_issues(self, project_key):
        await asyncio.sleep(0.02)
        return ISSUES  # already in normalized shape


def patch(theme="mocha"):
    mod.load_credentials = lambda: ("demo.atlassian.net", "demo@nebula.dev", "token")
    mod.read_cache = lambda name: None
    mod.write_cache = lambda name, data: None
    mod.load_state = lambda: {"theme": theme, "mine": False, "team_id": "CORE", "welcomed": True}
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
    def no_creds():
        raise FileNotFoundError("no credentials configured")
    mod.load_credentials = no_creds
    app = DemoApp()
    async with app.run_test(size=size) as pilot:
        await pilot.pause(0.6)
        app.save_screenshot(str(ASSETS / f"{name}.svg"))
    print(f"  \u2713 {name}.svg")


async def welcome_shot(name, size=(148, 41)):
    patch("mocha")
    # no "welcomed" key → the first-launch tour card shows
    mod.load_state = lambda: {"theme": "mocha", "mine": False, "team_id": "CORE"}
    app = DemoApp()
    async with app.run_test(size=size) as pilot:
        for _ in range(40):
            await pilot.pause(0.1)
            if app.query_one("#issues").option_count > 0:
                break
        await pilot.pause(0.3)
        app.save_screenshot(str(ASSETS / f"{name}.svg"))
    print(f"  ✓ {name}.svg")


async def open_projects(app, pilot):
    await pilot.press("v")
    await pilot.pause(0.3)


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
    await shot("projects", size=(148, 41), drive=open_projects)
    await onboard_shot("onboard")
    await welcome_shot("welcome")
    await shot("theme-void", size=(148, 41), theme="void")
    await shot("theme-onyx", size=(148, 41), theme="onyx")
    print("done — convert with: for f in assets/*.svg; rsvg-convert -w 1600 $f -o (string replace .svg .png $f); end")


if __name__ == "__main__":
    asyncio.run(main())
