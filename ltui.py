#!/usr/bin/env python3
"""ltui — a fast, clean TUI for Linear.

Copyright (C) 2026 Gheat
This program is free software licensed under the GNU GPL v3 or later;
you may redistribute and modify it only under those terms. Distributed
WITHOUT ANY WARRANTY. See the LICENSE file.
"""

from __future__ import annotations

__version__ = "0.12.0"

import json
import sys
import tomllib
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

import httpx
from rich.markup import escape
from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.color import Color as TColor
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.theme import Theme
from textual.widgets import Button, Footer, Input, Markdown, OptionList, Static, TextArea
from textual.widgets.option_list import Option
from textual.worker import WorkerState

API_URL = "https://api.linear.app/graphql"
CONFIG = Path.home() / ".config/linear-cli/config.toml"
LTUI_CONFIG = Path.home() / ".config/ltui/config.toml"
STATE_FILE = Path.home() / ".local/state/ltui/state.json"
CACHE_DIR = Path.home() / ".cache/ltui"
AUTO_REFRESH_SECONDS = 180

# ── palette (catppuccin mocha) ────────────────────────────────────────────
C_TEXT = "#cdd6f4"
C_SUB = "#a6adc8"
C_DIM = "#6c7086"
C_FAINT = "#45475a"
C_VFAINT = "#313244"
C_BLUE = "#89b4fa"
C_LAV = "#b4befe"
C_PEACH = "#fab387"
C_GREEN = "#a6e3a1"
C_RED = "#f38ba8"
C_MAUVE = "#cba6f7"

_PALETTE = dict(
    C_TEXT=C_TEXT, C_SUB=C_SUB, C_DIM=C_DIM, C_FAINT=C_FAINT, C_VFAINT=C_VFAINT,
    C_BLUE=C_BLUE, C_LAV=C_LAV, C_PEACH=C_PEACH, C_GREEN=C_GREEN, C_RED=C_RED,
    C_MAUVE=C_MAUVE,
)
_PALETTE_ANSI = dict(
    C_TEXT="default", C_SUB="white", C_DIM="bright_black", C_FAINT="bright_black",
    C_VFAINT="bright_black", C_BLUE="blue", C_LAV="bright_blue", C_PEACH="yellow",
    C_GREEN="green", C_RED="red", C_MAUVE="magenta",
)


def set_palette(ansi: bool) -> None:
    """Swap the chrome palette; `system` draws it in terminal ANSI colors."""
    globals().update(_PALETTE_ANSI if ansi else _PALETTE)

# ── themes ────────────────────────────────────────────────────────────────
_ACCENTS = dict(
    success=C_GREEN, warning="#f9e2af", error=C_RED, dark=True
)

THEMES = [
    Theme(
        name="mocha",
        primary=C_BLUE, secondary=C_MAUVE, accent="#f5c2e7",
        background="#1e1e2e", surface="#313244", panel="#181825",
        foreground=C_TEXT, **_ACCENTS,
        variables={
            "ltui-border": "#45475a",
            "ltui-border-focus": C_BLUE,
            "ltui-border-detail": C_LAV,
            "ltui-modal-bg": "#181825",
            "ltui-cursor": "#3e4869",
            "ltui-overlay": "black 40%",
            "scrollbar": "#313244",
            "scrollbar-hover": "#45475a",
            "scrollbar-active": "#585b70",
            "scrollbar-background": "#181825",
            "screen-selection-background": "#b4befe 35%",
            "input-selection-background": "#b4befe 35%",
        },
    ),
    Theme(
        name="void",
        primary=C_BLUE, secondary=C_MAUVE, accent="#f5c2e7",
        background="#000000", surface="#101018", panel="#070709",
        foreground=C_TEXT, **_ACCENTS,
        variables={
            "ltui-border": "#26262e",
            "ltui-border-focus": C_BLUE,
            "ltui-border-detail": C_LAV,
            "ltui-modal-bg": "#0a0a10",
            "ltui-cursor": "#1e2a4a",
            "ltui-overlay": "black 40%",
            "scrollbar": "#1e1e28",
            "scrollbar-hover": "#2c2c38",
            "scrollbar-active": "#3c3c4a",
            "scrollbar-background": "#0a0a10",
            "screen-selection-background": "#b4befe 30%",
            "input-selection-background": "#b4befe 30%",
        },
    ),
    Theme(
        name="onyx",
        primary="#9aa5b5", secondary="#7d8494", accent="#b8c0cc",
        background="#0e0e11", surface="#1b1b20", panel="#131317",
        foreground="#d4d6dd", **_ACCENTS,
        variables={
            "ltui-border": "#33333c",
            "ltui-border-focus": "#9aa5b5",
            "ltui-border-detail": "#b8c0cc",
            "ltui-modal-bg": "#141419",
            "ltui-cursor": "#2b303b",
            "ltui-overlay": "black 40%",
            "scrollbar": "#2a2a32",
            "scrollbar-hover": "#3a3a44",
            "scrollbar-active": "#4a4a56",
            "scrollbar-background": "#131317",
            "screen-selection-background": "#b8c0cc 30%",
            "input-selection-background": "#b8c0cc 30%",
        },
    ),
    # no background at all — the terminal's own background (and any
    # blur/transparency it has) shows through
    Theme(
        name="clear",
        primary="#8a93a5", secondary="#6f7787", accent="#a9b1c0",
        background="ansi_default", surface="ansi_default", panel="ansi_default",
        foreground=C_TEXT, **_ACCENTS,
        variables={
            "ltui-border": "#3c3f4a",
            "ltui-border-focus": "#8a93a5",
            "ltui-border-detail": "#a9b1c0",
            "ltui-modal-bg": "#16161d",
            "ltui-cursor": "#282c38",
            "ltui-overlay": "transparent",
            "scrollbar": "#3c3f4a",
            "scrollbar-hover": "#4a4e5a",
            "scrollbar-active": "#5a5f6d",
            "scrollbar-background": "transparent",
            "screen-selection-background": "#3f4655",
            "input-selection-background": "#3f4655",
        },
    ),
    # your terminal's own ANSI palette + no background: a custom kitty /
    # alacritty theme becomes the ltui theme
    Theme(
        name="system",
        primary="ansi_blue", secondary="ansi_magenta", accent="ansi_cyan",
        background="ansi_default", surface="ansi_default", panel="ansi_default",
        foreground="ansi_default",
        success="ansi_green", warning="ansi_yellow", error="ansi_red", dark=True,
        variables={
            "ltui-border": "ansi_bright_black",
            "ltui-border-focus": "ansi_blue",
            "ltui-border-detail": "ansi_bright_blue",
            "ltui-modal-bg": "ansi_black",
            "ltui-cursor": "ansi_bright_black",
            "ltui-overlay": "transparent",
            "scrollbar": "ansi_bright_black",
            "scrollbar-hover": "ansi_bright_black",
            "scrollbar-active": "ansi_blue",
            "scrollbar-background": "ansi_default",
            "screen-selection-background": "ansi_cyan",
            "screen-selection-foreground": "ansi_black",
            "input-selection-background": "ansi_cyan",
        },
    ),
]
THEME_NAMES = [t.name for t in THEMES]

TYPE_RANK = {
    "triage": 0,
    "started": 1,
    "unstarted": 2,
    "backlog": 3,
    "completed": 4,
    "canceled": 5,
    "duplicate": 6,
}

PRIORITIES = [(1, "Urgent"), (2, "High"), (3, "Medium"), (4, "Low"), (0, "No priority")]

# ── graphql ───────────────────────────────────────────────────────────────
ISSUE_FIELDS = """
        id identifier title description url priority branchName
        updatedAt createdAt
        state { id name color type position }
        assignee { id displayName }
        labels(first: 6) { nodes { name color } }
        relations(first: 6) { nodes { type relatedIssue { identifier } } }
        inverseRelations(first: 6) { nodes { type issue { identifier } } }
        project { id name color }
        parent { identifier }
"""

QL_BOOT = """
query {
  viewer { id displayName }
  organization { name }
  teams(first: 50) { nodes { id name key color } }
}"""

QL_ISSUES = f"""
query($teamId: String!) {{
  team(id: $teamId) {{
    issues(first: 250, orderBy: updatedAt) {{
      nodes {{ {ISSUE_FIELDS} }}
    }}
    states {{ nodes {{ id name color type position }} }}
  }}
}}"""

M_CREATE = f"""
mutation($teamId: String!, $title: String!, $desc: String) {{
  issueCreate(input: {{teamId: $teamId, title: $title, description: $desc}}) {{
    success
    issue {{ {ISSUE_FIELDS} }}
  }}
}}"""

QL_COMMENTS = """
query($id: String!) {
  issue(id: $id) {
    parent { identifier title }
    children(first: 25) {
      nodes { identifier title state { name color type } }
    }
    comments(first: 50) {
      nodes { id body createdAt user { displayName } botActor { name } }
    }
  }
}"""

QL_MEMBERS = """
query($teamId: String!) {
  team(id: $teamId) {
    members(first: 50) { nodes { id displayName } }
  }
}"""

M_STATE = """
mutation($id: String!, $stateId: String!) {
  issueUpdate(id: $id, input: {stateId: $stateId}) {
    success
    issue { id state { id name color type position } }
  }
}"""

M_ASSIGN = """
mutation($id: String!, $assigneeId: String) {
  issueUpdate(id: $id, input: {assigneeId: $assigneeId}) {
    success
    issue { id assignee { id displayName } }
  }
}"""

M_PRIORITY = """
mutation($id: String!, $p: Int!) {
  issueUpdate(id: $id, input: {priority: $p}) { success }
}"""

M_COMMENT = """
mutation($id: String!, $body: String!) {
  commentCreate(input: {issueId: $id, body: $body}) { success }
}"""


def load_api_key() -> str:
    import os

    if key := os.environ.get("LINEAR_API_KEY"):
        return key
    try:
        if key := tomllib.loads(LTUI_CONFIG.read_text()).get("api_key"):
            return key
    except Exception:
        pass
    cfg = tomllib.loads(CONFIG.read_text())
    return cfg["workspaces"][cfg.get("current", "default")]["api_key"]


def save_api_key(key: str) -> None:
    LTUI_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    LTUI_CONFIG.write_text(f'api_key = "{key}"\n')
    LTUI_CONFIG.chmod(0o600)


async def verify_key(key: str) -> str:
    """Check a key against the API; returns 'viewer @ org' or raises."""
    async with httpx.AsyncClient(
        headers={"Authorization": key, "Content-Type": "application/json"},
        timeout=15,
    ) as client:
        resp = await client.post(
            API_URL,
            json={
                "query": "query { viewer { displayName } organization { name } }"
            },
        )
        data = resp.json()
        if data.get("errors"):
            raise RuntimeError(data["errors"][0].get("message", "invalid key"))
        d = data["data"]
        return f"{d['viewer']['displayName']} @ {d['organization']['name']}"


# ── helpers ───────────────────────────────────────────────────────────────
def parse_dt(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def rel_time(iso: str) -> str:
    s = (datetime.now(timezone.utc) - parse_dt(iso)).total_seconds()
    if s < 60:
        return "now"
    if s < 3600:
        return f"{int(s // 60)}m"
    if s < 86400:
        return f"{int(s // 3600)}h"
    if s < 604800:
        return f"{int(s // 86400)}d"
    if s < 2629800:
        return f"{int(s // 604800)}w"
    if s < 31557600:
        return f"{int(s // 2629800)}mo"
    return f"{int(s // 31557600)}y"


def state_icon(state: dict) -> str:
    t = state["type"]
    if t == "started" and "review" in state["name"].lower():
        return "◑"
    return {
        "triage": "◎",
        "backlog": "◌",
        "unstarted": "○",
        "started": "◐",
        "completed": "●",
        "canceled": "⊘",
        "duplicate": "⊘",
    }.get(t, "○")


def priority_cell(p: int) -> Text:
    t = Text()
    if p == 1:
        t.append(" ", style=f"bold {C_PEACH}")
        t.append("  ")
    elif p in (2, 3, 4):
        lit = {2: 3, 3: 2, 4: 1}[p]
        for i, ch in enumerate("▂▄▆"):
            t.append(ch, style=C_SUB if i < lit else C_VFAINT)
    else:
        t.append("···", style=C_VFAINT)
    return t


def block_info(issue: dict) -> tuple[list[str], list[str]]:
    """Identifiers this issue is blocked by, and identifiers it blocks."""
    blocked_by = [
        r["issue"]["identifier"]
        for r in (issue.get("inverseRelations") or {}).get("nodes", [])
        if r["type"] == "blocks"
    ]
    blocks = [
        r["relatedIssue"]["identifier"]
        for r in (issue.get("relations") or {}).get("nodes", [])
        if r["type"] == "blocks"
    ]
    return blocked_by, blocks


def priority_name(p: int) -> str:
    return dict((n, lbl) for n, lbl in PRIORITIES).get(p, "No priority")


def state_sort_key(s: dict):
    rank = TYPE_RANK.get(s["type"], 9)
    pos = s["position"] or 0
    return (rank, -pos if s["type"] == "started" else pos)


def issue_sort_key(i: dict):
    # most recently updated first within each status group
    return (-parse_dt(i["updatedAt"]).timestamp(),)


def load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {}


def save_state(data: dict) -> None:
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(data))
    except Exception:
        pass


def read_cache(name: str) -> dict | None:
    try:
        return json.loads((CACHE_DIR / f"{name}.json").read_text())
    except Exception:
        return None


def write_cache(name: str, data: dict) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        (CACHE_DIR / f"{name}.json").write_text(json.dumps(data))
    except Exception:
        pass


def clear_cache() -> int:
    count = 0
    try:
        for f in CACHE_DIR.glob("*.json"):
            f.unlink()
            count += 1
    except Exception:
        pass
    return count


# ── widgets ───────────────────────────────────────────────────────────────
def pop_in(widget, duration: float = 0.15) -> None:
    """Fade a freshly mounted container into place.

    (offset/slide animation isn't supported for ScalarOffset in textual 8.x,
    so this is opacity-only — still reads as motion at 150ms.)
    """
    widget.styles.opacity = 0.0
    widget.styles.animate("opacity", 1.0, duration=duration, easing="out_cubic")


SPINNER_FRAMES = "\u280b\u2819\u2839\u2838\u283c\u2834\u2826\u2827\u2807\u280f"

FX_TICK = 0.12  # seconds per animation frame
FX_REST_TICKS = 26  # pause between wave sweeps (~3s)


def wave_markup(s: str, pos: int, base: str, hi: str) -> str:
    """One traveling letter, bolded + capitalized: gheatmc -> gHeatmc -> ..."""
    out = []
    for i, ch in enumerate(s):
        e = escape(ch)
        if i == pos:
            out.append(f"[bold {hi}]{e.upper()}[/]")
        else:
            out.append(f"[{base}]{e}[/]")
    return "".join(out)


class NavList(OptionList):
    BINDINGS = [
        Binding("j", "cursor_down", show=False),
        Binding("k", "cursor_up", show=False),
        Binding("g", "first", show=False),
        Binding("G", "last", show=False),
    ]

    def on_resize(self, event) -> None:
        if self.id == "issues":
            app = self.app
            if getattr(app, "_issues", None):
                app.call_later(app.render_issues)


class DetailScroll(VerticalScroll):
    can_focus = True
    BINDINGS = [
        Binding("j", "scroll_down", show=False),
        Binding("k", "scroll_up", show=False),
    ]


class FilterInput(Input):
    BINDINGS = [Binding("escape", "dismiss_filter", show=False)]

    def action_dismiss_filter(self) -> None:
        self.value = ""
        self.remove_class("visible")
        self.app.query_one("#issues").focus()


class Splitter(Static):
    """A 1-cell drag handle between panels; drag to resize, double-click to reset."""

    can_focus = False
    ALLOW_SELECT = False  # a drag here resizes; it must not start text selection

    def __init__(
        self,
        target: str,
        invert: bool = False,
        min_width: int = 16,
        max_width: int = 100,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._target = target
        self._invert = invert
        self._min = min_width
        self._max = max_width
        self._drag_x: int | None = None
        self._start_w: int = 0

    def on_mouse_down(self, event) -> None:
        self._drag_x = event.screen_x
        self._start_w = self.app.query_one(self._target).outer_size.width
        self.capture_mouse()
        self.add_class("dragging")

    def on_mouse_move(self, event) -> None:
        if self._drag_x is None:
            return
        delta = event.screen_x - self._drag_x
        if self._invert:
            delta = -delta
        cap = min(self._max, self.app.size.width - 50)
        width = max(self._min, min(self._start_w + delta, cap))
        self.app.query_one(self._target).styles.width = width

    def on_mouse_up(self, event) -> None:
        if self._drag_x is None:
            return
        self._drag_x = None
        self.release_mouse()
        self.remove_class("dragging")
        save_layout = getattr(self.app, "_save_layout", None)
        if save_layout is not None:
            save_layout()

    def on_click(self, event) -> None:
        if getattr(event, "chain", 1) == 2:  # double-click: back to default width
            self.app.query_one(self._target).styles.width = None
            save_layout = getattr(self.app, "_save_layout", None)
            if save_layout is not None:
                save_layout(reset=self._target)


class PickerModal(ModalScreen):
    BINDINGS = [Binding("escape", "cancel", show=False)]

    def __init__(self, title: str, options: list[Option]) -> None:
        super().__init__()
        self._title = title
        self._options = options

    def compose(self) -> ComposeResult:
        with Vertical(id="picker-box"):
            yield Static(self._title, id="picker-title")
            yield NavList(*self._options, id="picker-list")

    def on_mount(self) -> None:
        pop_in(self.query_one("#picker-box"))
        self.query_one("#picker-list").focus()

    @on(OptionList.OptionSelected)
    def _selected(self, event: OptionList.OptionSelected) -> None:
        self.dismiss(event.option.id)

    def action_cancel(self) -> None:
        self.dismiss(None)


class CommentModal(ModalScreen):
    BINDINGS = [
        Binding("escape", "cancel", show=False),
        Binding("ctrl+s", "submit", show=False),
    ]

    def __init__(self, title: str) -> None:
        super().__init__()
        self._title = title

    def compose(self) -> ComposeResult:
        with Vertical(id="comment-box"):
            yield Static(self._title, id="comment-title")
            yield TextArea(id="comment-input")
            with Horizontal(id="comment-actions"):
                yield Static(
                    f"[{C_DIM}]ctrl+s to send · esc to cancel[/]", id="comment-hint"
                )
                yield Button("cancel", id="comment-cancel")
                yield Button(" comment", variant="primary", id="comment-send")

    def on_mount(self) -> None:
        pop_in(self.query_one("#comment-box"))
        self.query_one("#comment-input").focus()

    @on(Button.Pressed, "#comment-send")
    def _send(self) -> None:
        self.action_submit()

    @on(Button.Pressed, "#comment-cancel")
    def _cancel(self) -> None:
        self.dismiss(None)

    def action_submit(self) -> None:
        text = self.query_one("#comment-input", TextArea).text.strip()
        self.dismiss(text or None)

    def action_cancel(self) -> None:
        self.dismiss(None)


class NewTicketModal(ModalScreen):
    BINDINGS = [
        Binding("escape", "cancel", show=False),
        Binding("ctrl+s", "submit", show=False),
    ]

    def __init__(self, heading: str) -> None:
        super().__init__()
        self._heading = heading

    def compose(self) -> ComposeResult:
        with Vertical(id="ticket-box"):
            yield Static(self._heading, id="ticket-heading")
            yield Input(placeholder="title", id="ticket-title")
            yield TextArea(id="ticket-desc")
            with Horizontal(id="ticket-actions"):
                yield Static(
                    f"[{C_DIM}]description is optional · ctrl+s to create · esc to cancel[/]",
                    id="ticket-hint",
                )
                yield Button("cancel", id="ticket-cancel")
                yield Button(" create", variant="primary", id="ticket-create")

    def on_mount(self) -> None:
        pop_in(self.query_one("#ticket-box"))
        self.query_one("#ticket-title").focus()

    @on(Input.Submitted, "#ticket-title")
    def _title_done(self) -> None:
        self.query_one("#ticket-desc").focus()

    @on(Button.Pressed, "#ticket-create")
    def _create(self) -> None:
        self.action_submit()

    @on(Button.Pressed, "#ticket-cancel")
    def _cancel(self) -> None:
        self.dismiss(None)

    def action_submit(self) -> None:
        title = self.query_one("#ticket-title", Input).value.strip()
        if not title:
            self.app.notify("a title is required", severity="warning")
            self.query_one("#ticket-title").focus()
            return
        desc = self.query_one("#ticket-desc", TextArea).text.strip()
        self.dismiss((title, desc or None))

    def action_cancel(self) -> None:
        self.dismiss(None)


# ── app ───────────────────────────────────────────────────────────────────
class OnboardModal(ModalScreen):
    """First-run setup: paste a Linear API key, validate it live, save it."""

    BINDINGS = [Binding("escape", "quit_app", show=False)]

    def compose(self) -> ComposeResult:
        with Vertical(id="onboard-box"):
            yield Static(
                f"[bold {C_BLUE}]\uf022  welcome to ltui[/]", id="onboard-title"
            )
            yield Static(
                f"[{C_SUB}]ltui talks to Linear with a personal API key.[/]\n\n"
                f"[{C_DIM}]1.[/] [{C_SUB}]open[/] "
                f"[@click=screen.open_keys][{C_BLUE}]linear.app/settings/api[/][/] "
                f"[{C_DIM}](click it)[/]\n"
                f"[{C_DIM}]2.[/] [{C_SUB}]create a personal API key[/]\n"
                f"[{C_DIM}]3.[/] [{C_SUB}]paste it below and hit enter[/]",
                id="onboard-body",
            )
            yield Input(placeholder="lin_api_\u2026", password=True, id="onboard-key")
            yield Static("", id="onboard-status")
            with Horizontal(id="onboard-actions"):
                yield Static(
                    f"[{C_VFAINT}]saved to ~/.config/ltui/config.toml\n"
                    f"also works: LINEAR_API_KEY env, linear-cli auth[/]",
                    id="onboard-hint",
                )
                yield Button("\uf1e6 connect", variant="primary", id="onboard-connect")

    def on_mount(self) -> None:
        pop_in(self.query_one("#onboard-box"))
        self.query_one("#onboard-key").focus()

    def action_open_keys(self) -> None:
        webbrowser.open("https://linear.app/settings/api")

    def action_quit_app(self) -> None:
        self.app.exit()

    @on(Input.Submitted, "#onboard-key")
    def _submitted(self) -> None:
        self._connect()

    @on(Button.Pressed, "#onboard-connect")
    def _pressed(self) -> None:
        self._connect()

    @work(exclusive=True, group="verify")
    async def _connect(self) -> None:
        status = self.query_one("#onboard-status", Static)
        key = self.query_one("#onboard-key", Input).value.strip()
        if not key:
            status.update(f"[{C_PEACH}]paste a key first[/]")
            return
        status.update(f"[{C_DIM}]\uf017 checking\u2026[/]")
        try:
            who = await verify_key(key)
        except Exception as e:
            status.update(f"[{C_RED}]\uf057 {escape(str(e))}[/]")
            return
        status.update(f"[{C_GREEN}]\uf058 connected \u2014 {escape(who)}[/]")
        self.dismiss(key)


class ThemeModal(ModalScreen):
    """Theme picker — highlighting a theme previews it live."""

    BINDINGS = [Binding("escape", "cancel", show=False)]

    def compose(self) -> ComposeResult:
        with Vertical(id="theme-box"):
            yield Static("theme \u00b7 scroll to preview", id="theme-title")
            yield NavList(id="theme-list")

    def _row(self, name: str, active: str) -> Option:
        row = Text("  ")
        row.append("\u25cf " if name == active else "\u25cb ", style=C_BLUE if name == active else C_DIM)
        row.append(name, style=C_TEXT if name == active else C_SUB)
        return Option(row, id=name)

    def on_mount(self) -> None:
        pop_in(self.query_one("#theme-box"))
        app = self.app
        self._original = app.theme
        ol = self.query_one("#theme-list", NavList)
        opts = [Option(Text(" ltui", style=f"bold {C_SUB}"), disabled=True)]
        index_of = {}
        for name in THEME_NAMES:
            index_of[name] = len(opts)
            opts.append(self._row(name, self._original))
        extra = sorted(n for n in app.available_themes if n not in THEME_NAMES)
        if extra:
            opts.append(Option(Text(" "), disabled=True))
            opts.append(Option(Text(" textual", style=f"bold {C_SUB}"), disabled=True))
            for name in extra:
                index_of[name] = len(opts)
                opts.append(self._row(name, self._original))
        ol.add_options(opts)
        ol.highlighted = index_of.get(self._original, 1)
        ol.focus()

    @on(OptionList.OptionHighlighted, "#theme-list")
    def _preview(self, event: OptionList.OptionHighlighted) -> None:
        if event.option.id:
            self.app.theme = event.option.id

    @on(OptionList.OptionSelected, "#theme-list")
    def _select(self, event: OptionList.OptionSelected) -> None:
        if event.option.id:
            self.app.theme = event.option.id
        self.dismiss(True)
        self.app._save_state()

    def action_cancel(self) -> None:
        self.app.theme = self._original
        self.dismiss(False)


class SettingsModal(ModalScreen):
    BINDINGS = [Binding("escape", "close_modal", show=False)]

    def compose(self) -> ComposeResult:
        with Vertical(id="settings-box"):
            yield Static(id="settings-profile")
            yield NavList(id="settings-list")
            yield Static(id="settings-foot")

    def on_mount(self) -> None:
        pop_in(self.query_one("#settings-box"))
        app = self.app
        profile = Text()
        profile.append(" ", style=C_BLUE)
        profile.append(getattr(app, "_viewer_name", None) or "…", style=f"bold {C_TEXT}")
        org = getattr(app, "_org", None)
        if org:
            profile.append(f"  ·  {org}", style=C_DIM)
        self.query_one("#settings-profile", Static).update(profile)
        foot = Text()
        foot.append(f"ltui {__version__}", style=C_DIM)
        foot.append("  ·  cache ~/.cache/ltui", style=C_VFAINT)
        self.query_one("#settings-foot", Static).update(foot)
        self._build()
        self.query_one("#settings-list").focus()

    def _build(self) -> None:
        app = self.app
        ol = self.query_one("#settings-list", NavList)
        prev = ol.highlighted
        ol.clear_options()
        opts: list[Option] = [
            Option(Text(" preferences", style=f"bold {C_SUB}"), disabled=True)
        ]
        mine = getattr(app, "_mine", False)
        row = Text("   ")
        row.append("● " if mine else "○ ", style=C_GREEN if mine else C_DIM)
        row.append("mine only", style=C_TEXT if mine else C_SUB)
        opts.append(Option(row, id="pref:mine"))
        opts.append(Option(Text(" "), disabled=True))
        opts.append(Option(Text(" maintenance", style=f"bold {C_SUB}"), disabled=True))
        opts.append(Option(Text("    clear cache", style=C_SUB), id="cache:clear"))
        ol.add_options(opts)
        ol.highlighted = prev if prev is not None else 1

    @on(OptionList.OptionSelected)
    def _selected(self, event: OptionList.OptionSelected) -> None:
        app = self.app
        oid = event.option.id or ""
        if oid == "pref:mine":
            app.action_toggle_mine()
        elif oid == "cache:clear":
            count = clear_cache()
            app.notify(f" cleared {count} cached file(s)")
        self._build()

    def action_close_modal(self) -> None:
        self.dismiss(None)


class HelpModal(ModalScreen):
    """Keybinding cheatsheet — press ? anywhere."""

    BINDINGS = [
        Binding("escape", "close_modal", show=False),
        Binding("question_mark", "close_modal", show=False),
        # screen-level binding wins over the app's q → quit while open
        Binding("q", "close_modal", show=False),
    ]

    SECTIONS = [
        ("navigate", [
            ("j/k ↑↓", "move around lists and the detail panel"),
            ("g / G", "jump to top / bottom"),
            ("enter", "open ticket detail (click works too)"),
            ("esc", "close panel · dismiss modal · clear filter"),
        ]),
        ("ticket", [
            ("n", "new ticket in the current team"),
            ("s", "change status"),
            ("p", "change priority"),
            ("a", "change assignee (or unassign)"),
            ("c", "add a comment (ctrl+s to send)"),
            ("y", "yank — copy branch / url / identifier"),
            ("o", "open in browser"),
        ]),
        ("view", [
            ("/", "filter issues"),
            ("m", "toggle mine only"),
            ("v", "group by status / project"),
            ("V", "filter to a single project"),
            ("t", "cycle theme"),
            (",", "settings"),
            ("r", "refresh"),
        ]),
        ("app", [
            ("?", "this help"),
            ("ctrl+p", "command palette"),
            ("q", "quit"),
        ]),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="help-box"):
            yield Static(id="help-title")
            yield Static(id="help-body")
            yield Static(id="help-foot")

    def on_mount(self) -> None:
        pop_in(self.query_one("#help-box"))
        title = Text()
        title.append("\uf11c ", style=C_BLUE)
        title.append("keys", style=f"bold {C_TEXT}")
        self.query_one("#help-title", Static).update(title)
        key_w = max(len(k) for _, rows in self.SECTIONS for k, _ in rows) + 3
        body = Text()
        for section, rows in self.SECTIONS:
            if body:
                body.append("\n")
            body.append(f" {section}\n", style=f"bold {C_DIM}")
            for key, desc in rows:
                body.append(f"   {key.ljust(key_w)}", style=C_BLUE)
                body.append(f"{desc}\n", style=C_SUB)
        body.rstrip()
        self.query_one("#help-body", Static).update(body)
        self.query_one("#help-foot", Static).update(
            Text("? · esc · q to close", style=C_VFAINT)
        )

    def action_close_modal(self) -> None:
        self.dismiss(None)


class WelcomeModal(ModalScreen):
    """One-time first-launch tour — dismissing marks the user as welcomed."""

    BINDINGS = [
        Binding("escape", "close_modal", show=False),
        Binding("enter", "close_modal", show=False),
        Binding("question_mark", "close_to_help", show=False),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="welcome-box"):
            yield Static(
                f"[bold {C_BLUE}]\uf005  welcome to ltui[/]", id="welcome-title"
            )
            yield Static(
                f"[{C_SUB}]you're in — your issues are loading right now.[/]\n\n"
                f"[{C_BLUE}]enter[/] [{C_SUB}]opens a ticket ·[/] "
                f"[{C_BLUE}]n[/] [{C_SUB}]creates one[/]\n"
                f"[{C_BLUE}]s[/] [{C_DIM}]/[/] [{C_BLUE}]a[/] [{C_DIM}]/[/] [{C_BLUE}]c[/] "
                f"[{C_SUB}]— status, assignee, comment[/]\n"
                f"[{C_BLUE}]m[/] [{C_SUB}]shows only yours ·[/] "
                f"[{C_BLUE}]/[/] [{C_SUB}]filters the list[/]\n\n"
                f"[{C_SUB}]and[/] [{C_BLUE}]?[/] [{C_SUB}]anytime for everything else.[/]",
                id="welcome-body",
            )
            with Horizontal(id="welcome-actions"):
                yield Static(f"[{C_DIM}]esc to close[/]", id="welcome-hint")
                yield Button("got it", variant="primary", id="welcome-ok")

    def on_mount(self) -> None:
        pop_in(self.query_one("#welcome-box"))
        self.query_one("#welcome-ok").focus()

    @on(Button.Pressed, "#welcome-ok")
    def _ok(self) -> None:
        self.dismiss(None)

    def action_close_modal(self) -> None:
        self.dismiss(None)

    def action_close_to_help(self) -> None:
        app = self.app
        self.dismiss(None)
        app.call_later(app.action_help)


def hint_markup() -> str:
    return (
        f"[@click=app.change_status][{C_BLUE}]s[/] [{C_DIM}]status[/][/]  "
        f"[@click=app.change_priority][{C_BLUE}]p[/] [{C_DIM}]priority[/][/]  "
        f"[@click=app.add_comment][{C_BLUE}]c[/] [{C_DIM}]comment[/][/]  "
        f"[@click=app.open_browser][{C_BLUE}]o[/] [{C_DIM}]browser[/][/]  "
        f"[@click=app.yank][{C_BLUE}]y[/] [{C_DIM}]yank[/][/]  "
        f"[@click=app.back][{C_BLUE}]esc[/] [{C_DIM}]close[/][/]"
    )


class LTUI(App):
    TITLE = "ltui"

    BINDINGS = [
        Binding("n", "new_ticket", "new"),
        Binding("s", "change_status", "status"),
        Binding("c", "add_comment", "comment"),
        Binding("slash", "filter", "filter"),
        Binding("m", "toggle_mine", "mine"),
        Binding("v", "toggle_group", "group"),
        Binding("V", "pick_project", show=False),
        Binding("t", "cycle_theme", "theme"),
        Binding("comma", "open_settings", show=False),
        Binding("question_mark", "help", "help"),
        Binding("q", "quit", "quit"),
        Binding("r", "refresh", show=False),
        Binding("p", "change_priority", show=False),
        Binding("a", "change_assignee", show=False),
        Binding("o", "open_browser", show=False),
        Binding("y", "yank", show=False),
        Binding("escape", "back", show=False),
    ]

    CSS = f"""
    #appheader {{ height: 1; padding: 0 2; }}
    #main {{ height: 1fr; }}

    #main {{ padding: 0 1 0 0; }}
    #sidebar {{ width: 24; margin: 0 0 0 1; }}
    #split-left, #split-right {{ width: 1; height: 1fr; }}
    #split-left:hover, #split-right:hover,
    #split-left.dragging, #split-right.dragging {{ background: $ltui-border; }}
    #split-right {{ display: none; }}
    #split-right.open {{ display: block; }}
    #teams {{
        height: 1fr;
        border: round $ltui-border; border-title-color: {C_SUB};
    }}
    #teams:focus {{ border: round $ltui-border-focus; border-title-color: $ltui-border-focus; }}
    #profile {{
        height: auto; padding: 0 1;
        border: round $ltui-border; border-title-color: {C_SUB};
    }}

    #centre {{
        width: 1fr;
        border: round $ltui-border;
        border-title-color: {C_TEXT}; border-subtitle-color: {C_DIM};
    }}
    #centre:focus-within {{ border: round $ltui-border-focus; }}

    #detail {{
        display: none; width: 46%; min-width: 44;
        border: round $ltui-border;
        border-title-color: $ltui-border-detail; border-subtitle-color: {C_DIM};
    }}
    #detail.open {{ display: block; }}
    #detail:focus-within {{ border: round $ltui-border-detail; }}

    OptionList {{
        background: transparent; border: none; padding: 0 1;
        scrollbar-size-vertical: 1;
    }}
    OptionList:focus {{ background: transparent; border: none; }}
    OptionList > .option-list--option-highlighted {{ background: $ltui-cursor; }}
    OptionList:focus > .option-list--option-highlighted {{ background: $ltui-cursor; }}

    CommandPalette {{ background: $ltui-overlay; }}
    CommandPalette > Vertical {{ width: 70; max-width: 85%; }}
    CommandPalette #--input {{ background: $ltui-modal-bg; }}
    CommandPalette CommandList {{ background: $ltui-modal-bg; }}

    #filter {{ display: none; height: 3; border: round $ltui-border; background: transparent; }}
    #filter.visible {{ display: block; }}
    #filter:focus {{ border: round $ltui-border-focus; }}

    #d-title {{ padding: 1 1 0 1; }}
    #d-meta {{ padding: 1 1 0 1; }}
    #d-scroll {{ height: 1fr; margin: 1 0 0 0; scrollbar-size-vertical: 1; }}
    #d-parent {{ display: none; height: auto; padding: 0 1; margin: 0 0 1 0; }}
    #d-parent.visible {{ display: block; }}
    #d-children {{ display: none; height: auto; padding: 0 1; margin: 0 0 1 0; }}
    #d-children.visible {{ display: block; }}
    #d-desc {{ background: transparent; padding: 0 1; }}
    Markdown {{ background: transparent; }}
    #d-comments-head {{ padding: 1 1 0 1; }}
    #d-comments {{ height: auto; }}
    .comment {{
        height: auto; border-left: thick {C_VFAINT};
        padding: 0 1; margin: 1 1 0 1;
    }}
    .comment-meta {{ height: auto; }}
    .comment Markdown {{ padding: 0; margin: 0; }}
    #d-hint {{ height: 1; padding: 0 1; margin: 1 0 0 0; }}

    PickerModal {{ align: center middle; background: $ltui-overlay; }}
    #picker-box {{
        width: 44; height: auto; max-height: 80%;
        background: $ltui-modal-bg; border: round $ltui-border-focus; padding: 1 1;
    }}
    #picker-title {{ padding: 0 1 1 1; color: {C_SUB}; text-style: bold; }}
    #picker-list {{ height: auto; max-height: 14; }}

    CommentModal {{ align: center middle; background: $ltui-overlay; }}
    #comment-box {{
        width: 72; height: 20;
        background: $ltui-modal-bg; border: round $ltui-border-focus; padding: 1 2;
    }}
    #comment-title {{ color: {C_SUB}; text-style: bold; padding: 0 0 1 0; }}
    #comment-input {{ height: 1fr; border: round {C_VFAINT}; background: transparent; }}
    #comment-input:focus {{ border: round {C_FAINT}; }}
    #comment-actions {{ height: 3; margin: 1 0 0 0; }}
    #comment-hint {{ width: 1fr; padding: 1 0; }}
    #comment-actions Button {{ margin: 0 0 0 2; min-width: 10; }}

    NewTicketModal {{ align: center middle; background: $ltui-overlay; }}
    #ticket-box {{
        width: 72; height: 24;
        background: $ltui-modal-bg; border: round $ltui-border-focus; padding: 1 2;
    }}
    #ticket-heading {{ color: {C_SUB}; text-style: bold; padding: 0 0 1 0; }}
    #ticket-title {{ border: round {C_VFAINT}; background: transparent; }}
    #ticket-title:focus {{ border: round {C_FAINT}; }}
    #ticket-desc {{ height: 1fr; margin: 1 0 0 0; border: round {C_VFAINT}; background: transparent; }}
    #ticket-desc:focus {{ border: round {C_FAINT}; }}
    #ticket-actions {{ height: 3; margin: 1 0 0 0; }}
    #ticket-hint {{ width: 1fr; padding: 1 0; }}
    #ticket-actions Button {{ margin: 0 0 0 2; min-width: 10; }}

    OnboardModal {{ align: center middle; background: $ltui-overlay; }}
    #onboard-box {{
        width: 62; height: auto;
        background: $ltui-modal-bg; border: round $ltui-border-focus; padding: 1 2;
    }}
    #onboard-title {{ padding: 0 0 1 0; }}
    #onboard-body {{ padding: 0 0 1 0; }}
    #onboard-key {{ border: round {C_VFAINT}; background: transparent; }}
    #onboard-key:focus {{ border: round {C_FAINT}; }}
    #onboard-status {{ height: 1; padding: 0 1; margin: 1 0 0 0; }}
    #onboard-actions {{ height: 3; margin: 1 0 0 0; }}
    #onboard-hint {{ width: 1fr; }}
    #onboard-actions Button {{ margin: 0 0 0 2; min-width: 12; }}

    ThemeModal {{ align: center middle; background: $ltui-overlay; }}
    #theme-box {{
        width: 40; height: auto; max-height: 85%;
        background: $ltui-modal-bg; border: round $ltui-border-focus; padding: 1 1;
    }}
    #theme-title {{ padding: 0 1 1 1; color: {C_SUB}; text-style: bold; }}
    #theme-list {{ height: auto; max-height: 18; }}

    SettingsModal {{ align: center middle; background: $ltui-overlay; }}
    #settings-box {{
        width: 42; height: auto; max-height: 85%;
        background: $ltui-modal-bg; border: round $ltui-border-focus; padding: 1 1;
    }}
    #settings-profile {{ padding: 0 1 1 1; }}
    #settings-list {{ height: auto; max-height: 16; }}
    #settings-foot {{ padding: 1 1 0 1; }}

    HelpModal {{ align: center middle; background: $ltui-overlay; }}
    #help-box {{
        width: 64; height: auto; max-height: 90%;
        background: $ltui-modal-bg; border: round $ltui-border-focus; padding: 1 2;
    }}
    #help-title {{ padding: 0 1 1 1; }}
    #help-body {{ height: auto; }}
    #help-foot {{ padding: 1 1 0 1; }}

    WelcomeModal {{ align: center middle; background: $ltui-overlay; }}
    #welcome-box {{
        width: 56; height: auto;
        background: $ltui-modal-bg; border: round $ltui-border-focus; padding: 1 2;
    }}
    #welcome-title {{ padding: 0 0 1 0; }}
    #welcome-body {{ padding: 0 0 1 0; }}
    #welcome-actions {{ height: 3; }}
    #welcome-hint {{ width: 1fr; padding: 1 0; }}
    #welcome-actions Button {{ margin: 0 0 0 2; min-width: 10; }}
    """

    def __init__(self) -> None:
        super().__init__()
        self.client: httpx.AsyncClient | None = None
        self._teams: list[dict] = []
        self._issues: list[dict] = []
        self._states: list[dict] = []
        self._members: dict[str, list] = {}
        self._team: dict | None = None
        self._viewer_id: str | None = None
        self._viewer_name: str | None = None
        self._boot_data: dict | None = None
        self._org: str | None = None
        self._mine = load_state().get("mine", False)
        self._group_by = load_state().get("group_by", "status")
        self._filter = ""
        self._project_filter: str | None = None  # project id, "" = no-project
        self._detail_issue: dict | None = None
        self._wave_pos = -1
        self._wave_rest = 0
        self._refreshing = False
        self._spin_frame = 0
        self._opt_index: dict[str, int] = {}
        self._issue_by_id: dict[str, dict] = {}

    def _on_theme_changed(self, _theme) -> None:
        # ansi-background themes (clear, ansi-dark, …) need ansi_color mode
        # so default-color codes pass through and the terminal bg shows
        set_palette(self.theme == "system")
        self.ansi_color = self._theme_is_ansi()
        if self._boot_data is not None:
            self._render_boot(self._boot_data)
        self._update_profile()
        try:
            self.query_one("#d-hint", Static).update(hint_markup())
        except Exception:
            pass
        if self._issues:
            self.render_issues()
        if self._detail_issue is not None:
            self.query_one("#d-title", Static).update(
                Text(self._detail_issue["title"], style=f"bold {C_TEXT}")
            )
            self._update_detail_meta(self._detail_issue)
        # persist every path (t, palette, picker) but not mid-preview;
        # ThemeModal commits or reverts on close
        if not isinstance(self.screen, ThemeModal):
            self._save_state()

    def _theme_is_ansi(self) -> bool:
        theme = self.available_themes.get(self.theme)
        if theme is None or theme.background is None:
            return False
        try:
            return TColor.parse(theme.background).ansi is not None
        except Exception:
            return False

    def get_css_variables(self) -> dict[str, str]:
        # ltui-* variables must exist even before our themes are registered
        # (the stylesheet is parsed while the default textual theme is active)
        variables = super().get_css_variables()
        theme = next((t for t in THEMES if t.name == self.theme), THEMES[0])
        for name, value in theme.variables.items():
            variables.setdefault(name, value)
        return variables

    # ── layout ────────────────────────────────────────────────────────
    def compose(self) -> ComposeResult:
        yield Static(id="appheader")
        with Horizontal(id="main"):
            with Vertical(id="sidebar"):
                yield NavList(id="teams")
                yield Static(id="profile")
            yield Splitter("#sidebar", min_width=16, max_width=44, id="split-left")
            with Vertical(id="centre"):
                yield FilterInput(placeholder=" filter issues…", id="filter")
                yield NavList(id="issues")
            yield Splitter("#detail", invert=True, min_width=34, id="split-right")
            with Vertical(id="detail"):
                yield Static(id="d-title")
                yield Static(id="d-meta")
                with DetailScroll(id="d-scroll"):
                    yield Static(id="d-parent")
                    yield Vertical(id="d-children")
                    yield Markdown(id="d-desc")
                    yield Static(id="d-comments-head")
                    yield Vertical(id="d-comments")
                yield Static(hint_markup(), id="d-hint")
        yield Footer()

    def on_mount(self) -> None:
        for t in THEMES:
            self.register_theme(t)
        self.theme_changed_signal.subscribe(self, self._on_theme_changed)
        saved = load_state().get("theme")
        self.theme = saved if saved in self.available_themes else THEME_NAMES[0]
        self.ansi_color = self._theme_is_ansi()
        layout = load_state()
        if w := layout.get("sidebar_w"):
            self.query_one("#sidebar").styles.width = int(w)
        if w := layout.get("detail_w"):
            self.query_one("#detail").styles.width = int(w)
        self.query_one("#teams").border_title = " teams "
        self.query_one("#profile").border_title = " you "
        self.query_one("#centre").border_title = " issues "
        self._update_profile()
        self.set_interval(FX_TICK, self._tick_fx)
        self.query_one("#issues").focus()
        try:
            key = load_api_key()
        except Exception:
            def connected(new_key: str | None) -> None:
                if not new_key:
                    return
                try:
                    save_api_key(new_key)
                except Exception as e:
                    self.notify(f"couldn't save key: {e}", severity="error")
                self._start(new_key)

            self.push_screen(OnboardModal(), connected)
            return
        self._start(key)

    def _start(self, key: str) -> None:
        self.client = httpx.AsyncClient(
            headers={"Authorization": key, "Content-Type": "application/json"},
            timeout=20,
        )
        # render instantly from cache, then refresh live data concurrently
        team = None
        if boot_cache := read_cache("boot"):
            self._render_boot(boot_cache)
            last_id = load_state().get("team_id")
            team = next((t for t in self._teams if t["id"] == last_id), None)
        if team is not None:
            self.query_one("#teams", NavList).highlighted = self._teams.index(team)
            self.load_team(team)
        self.boot(pick_team=team is None)
        self.set_interval(AUTO_REFRESH_SECONDS, self._auto_refresh_board)
        # one-time tour; _start may run inside OnboardModal's dismiss callback
        # (screen still popping), so defer the push a tick
        if not load_state().get("welcomed"):
            self.call_later(self._show_welcome)

    def _show_welcome(self) -> None:
        def done(_: object | None) -> None:
            data = load_state()
            data["welcomed"] = True
            save_state(data)

        self.push_screen(WelcomeModal(), done)

    # ── api ───────────────────────────────────────────────────────────
    async def gql(self, query: str, variables: dict | None = None) -> dict:
        resp = await self.client.post(
            API_URL, json={"query": query, "variables": variables or {}}
        )
        data = resp.json()
        if data.get("errors"):
            raise RuntimeError(data["errors"][0].get("message", "GraphQL error"))
        return data["data"]

    # ── workers ───────────────────────────────────────────────────────
    def _render_boot(self, data: dict) -> None:
        self._boot_data = data
        self._teams = data["teams"]["nodes"]
        self._viewer_id = data["viewer"]["id"]
        self._viewer_name = data["viewer"]["displayName"]
        self._org = data["organization"]["name"]
        self._update_profile()
        self._update_header()

        teams_list = self.query_one("#teams", NavList)
        teams_list.clear_options()
        for t in self._teams:
            row = Text()
            row.append("● ", style=t.get("color") or C_BLUE)
            row.append(t["name"], style=C_TEXT)
            row.append(f"  {t['key']}", style=C_DIM)
            teams_list.add_option(Option(row, id=t["id"]))
        if self._team is not None:
            idx = next(
                (n for n, t in enumerate(self._teams) if t["id"] == self._team["id"]),
                None,
            )
            if idx is not None:
                teams_list.highlighted = idx

    @work(exclusive=True, group="boot")
    async def boot(self, pick_team: bool = True) -> None:
        issues_list = self.query_one("#issues", NavList)
        if pick_team:
            issues_list.loading = True
        try:
            data = await self.gql(QL_BOOT)
        except Exception as e:
            if pick_team:
                issues_list.loading = False
            self.notify(f"linear: {e}", severity="error", timeout=10)
            return
        self._render_boot(data)
        write_cache("boot", data)
        if not pick_team:
            return
        last = load_state().get("team_id")
        team = next((t for t in self._teams if t["id"] == last), None) or (
            self._teams[0] if self._teams else None
        )
        if team is None:
            issues_list.loading = False
            self.notify("no teams found", severity="warning")
            return
        self.query_one("#teams", NavList).highlighted = self._teams.index(team)
        self.load_team(team)

    def _save_layout(self, reset: str | None = None) -> None:
        data = load_state()
        if reset == "#sidebar":
            data.pop("sidebar_w", None)
        else:
            data["sidebar_w"] = self.query_one("#sidebar").outer_size.width
        detail = self.query_one("#detail")
        if reset == "#detail":
            data.pop("detail_w", None)
        elif detail.has_class("open"):
            data["detail_w"] = detail.outer_size.width
        save_state(data)

    def _save_state(self) -> None:
        data = load_state()
        if self._team is not None:
            data["team_id"] = self._team["id"]
        data["mine"] = self._mine
        data["theme"] = self.theme
        data["group_by"] = self._group_by
        save_state(data)

    def _write_team_cache(self) -> None:
        if self._team is not None:
            write_cache(
                f"team-{self._team['id']}",
                {"issues": self._issues, "states": self._states},
            )

    def _set_issues(self, issues: list[dict], states: list[dict]) -> None:
        self._issues = issues
        self._states = states
        self._issue_by_id = {i["id"]: i for i in issues}

    @work(exclusive=True, group="issues")
    async def load_team(self, team: dict) -> None:
        self._team = team
        centre = self.query_one("#centre")
        centre.border_title = f" {team['key']} · {team['name']} "
        centre.border_subtitle = ""
        issues_list = self.query_one("#issues", NavList)
        cached = read_cache(f"team-{team['id']}")
        if cached:
            self._set_issues(cached["issues"], cached["states"])
            self.render_issues()
            centre.border_subtitle = f" {len(self._issues)} · ↻ refreshing "
            self._refreshing = True
        else:
            issues_list.loading = True
        self._save_state()
        try:
            data = await self.gql(QL_ISSUES, {"teamId": team["id"]})
        except Exception as e:
            issues_list.loading = False
            self._refreshing = False
            self.notify(f"linear: {e}", severity="error", timeout=10)
            return
        if self._team is None or self._team["id"] != team["id"]:
            self._refreshing = False
            return  # user switched teams while refreshing
        self._set_issues(
            data["team"]["issues"]["nodes"], data["team"]["states"]["nodes"]
        )
        issues_list.loading = False
        self._refreshing = False
        write_cache(
            f"team-{team['id']}",
            {"issues": self._issues, "states": self._states},
        )
        self.render_issues()
        # a cold load covers the list with a loading overlay, which kicks
        # focus over to the sidebar — pull it back once rows exist
        if not cached and self._detail_issue is None:
            focused = self.focused
            if focused is None or focused.id == "teams":
                issues_list.focus()
        if self._detail_issue is not None:
            fresh = self._issue_by_id.get(self._detail_issue["id"])
            if fresh is not None:
                self._detail_issue = fresh
                self._update_detail_meta(fresh)

    # NOT named _auto_refresh: textual's DOMNode owns that instance attribute
    # (backing field of the auto_refresh property) and would shadow the method
    def _auto_refresh_board(self) -> None:
        # silent background re-sync — load_team's cache-render + exclusive
        # "issues" worker group makes this a quiet swap that preserves the
        # highlight and the open detail panel. Skip whenever it could
        # interrupt the user (modal open) or race a pending mutation.
        if self.client is None or self._team is None:
            return
        if isinstance(self.screen, ModalScreen):
            return
        if any(
            w.group == "mutate" and w.state == WorkerState.RUNNING
            for w in self.workers
        ):
            return
        self.load_team(self._team)

    @work(exclusive=True, group="detail")
    async def load_comments(self, issue: dict) -> None:
        box = self.query_one("#d-comments", Vertical)
        head = self.query_one("#d-comments-head", Static)
        parent_w = self.query_one("#d-parent", Static)
        cbox = self.query_one("#d-children", Vertical)
        parent_w.update("")
        parent_w.remove_class("visible")
        cbox.remove_class("visible")
        await cbox.remove_children()
        await box.remove_children()
        head.update(Text(" comments · loading…", style=C_DIM))
        try:
            data = await self.gql(QL_COMMENTS, {"id": issue["id"]})
        except Exception as e:
            head.update(Text(f" comments · failed: {e}", style=C_RED))
            return
        if self._detail_issue is None or self._detail_issue["id"] != issue["id"]:
            return
        # parent + sub-issues context (old caches / demo stubs lack the keys)
        parent = data["issue"].get("parent")
        if parent:
            line = Text(no_wrap=True, overflow="ellipsis")
            line.append("\uf148 parent ", style=C_DIM)
            line.append(parent["identifier"], style=C_SUB)
            p_title = (parent.get("title") or "").strip()
            if len(p_title) > 60:
                p_title = p_title[:59] + "…"
            if p_title:
                line.append(f" — {p_title}", style=C_DIM)
            parent_w.update(line)
            parent_w.add_class("visible")
        children = (data["issue"].get("children") or {}).get("nodes") or []
        if children:
            done = sum(
                1 for ch in children
                if ch["state"]["type"] in ("completed", "canceled")
            )
            chead = Text("\uf0e8 ", style=C_MAUVE)
            chead.append(f"sub-issues · {done}/{len(children)}", style=f"bold {C_SUB}")
            await cbox.mount(Static(chead))
            for ch in children:
                st = ch["state"]
                row = Text(no_wrap=True, overflow="ellipsis")
                row.append(f"{state_icon(st)} ", style=st["color"] or C_SUB)
                row.append(ch["identifier"], style=C_DIM)
                c_title = ch["title"]
                if len(c_title) > 60:
                    c_title = c_title[:59] + "…"
                row.append(f" {c_title}", style=C_TEXT)
                await cbox.mount(Static(row))
            cbox.add_class("visible")
        comments = sorted(
            data["issue"]["comments"]["nodes"], key=lambda c: c["createdAt"]
        )
        head_text = Text(" ", style=C_MAUVE)
        head_text.append(f" comments · {len(comments)}", style=f"bold {C_SUB}")
        head.update(head_text)
        if not comments:
            await box.mount(Static(Text("   nothing here yet", style=C_DIM)))
            return
        for c in comments:
            author = (c.get("user") or {}).get("displayName") or (
                c.get("botActor") or {}
            ).get("name") or "unknown"
            meta = Text()
            meta.append("● ", style=C_MAUVE)
            meta.append(author, style=f"bold {C_TEXT}")
            meta.append(f"  {rel_time(c['createdAt'])} ago", style=C_DIM)
            wrap = Vertical(classes="comment")
            await box.mount(wrap)
            await wrap.mount(Static(meta, classes="comment-meta"))
            await wrap.mount(Markdown(c["body"] or ""))

    @work(group="mutate")
    async def apply_status(self, issue: dict, state_id: str) -> None:
        try:
            data = await self.gql(M_STATE, {"id": issue["id"], "stateId": state_id})
            new_state = data["issueUpdate"]["issue"]["state"]
        except Exception as e:
            self.notify(f"update failed: {e}", severity="error")
            return
        issue["state"] = new_state
        self._write_team_cache()
        self.render_issues(keep=issue["id"])
        if self._detail_issue and self._detail_issue["id"] == issue["id"]:
            self._update_detail_meta(issue)
        self.notify(f" {issue['identifier']} → {new_state['name']}")

    @work(group="mutate")
    async def apply_priority(self, issue: dict, p: int) -> None:
        try:
            await self.gql(M_PRIORITY, {"id": issue["id"], "p": p})
        except Exception as e:
            self.notify(f"update failed: {e}", severity="error")
            return
        issue["priority"] = p
        self._write_team_cache()
        self.render_issues(keep=issue["id"])
        if self._detail_issue and self._detail_issue["id"] == issue["id"]:
            self._update_detail_meta(issue)
        self.notify(f" {issue['identifier']} → {priority_name(p)}")

    @work(group="mutate")
    async def apply_assignee(self, issue: dict, assignee_id: str | None) -> None:
        try:
            data = await self.gql(
                M_ASSIGN, {"id": issue["id"], "assigneeId": assignee_id}
            )
            new_assignee = data["issueUpdate"]["issue"]["assignee"]
        except Exception as e:
            self.notify(f"update failed: {e}", severity="error")
            return
        issue["assignee"] = new_assignee
        self._write_team_cache()
        self.render_issues(keep=issue["id"])
        if self._detail_issue and self._detail_issue["id"] == issue["id"]:
            self._update_detail_meta(issue)
        name = (new_assignee or {}).get("displayName") or "unassigned"
        self.notify(f"\uf007 {issue['identifier']} → {name}")

    @work(group="mutate")
    async def create_issue(self, team: dict, title: str, desc: str | None) -> None:
        try:
            data = await self.gql(
                M_CREATE, {"teamId": team["id"], "title": title, "desc": desc}
            )
            issue = data["issueCreate"]["issue"]
        except Exception as e:
            self.notify(f"create failed: {e}", severity="error")
            return
        if self._team is None or self._team["id"] != team["id"]:
            self.notify(f" created {issue['identifier']}")
            return
        self._issues.insert(0, issue)
        self._issue_by_id[issue["id"]] = issue
        self._write_team_cache()
        self.render_issues(keep=issue["id"])
        self.notify(f" created {issue['identifier']}")

    @work(group="mutate")
    async def submit_comment(self, issue: dict, body: str) -> None:
        try:
            await self.gql(M_COMMENT, {"id": issue["id"], "body": body})
        except Exception as e:
            self.notify(f"comment failed: {e}", severity="error")
            return
        self.notify(f" comment added to {issue['identifier']}")
        if self._detail_issue and self._detail_issue["id"] == issue["id"]:
            self.load_comments(issue)

    # ── rendering ─────────────────────────────────────────────────────
    def render_issues(self, keep: str | None = None) -> None:
        ol = self.query_one("#issues", NavList)
        if keep is None:
            prev = ol.highlighted
            if prev is not None:
                opt = ol.get_option_at_index(prev)
                keep = opt.id if opt else None

        width = max(ol.content_size.width - 2, 40)
        flt = self._filter.lower()
        issues = self._issues
        if self._mine and self._viewer_id:
            issues = [
                i
                for i in issues
                if (i.get("assignee") or {}).get("id") == self._viewer_id
            ]
        if self._project_filter is not None:
            issues = [
                i
                for i in issues
                if (i.get("project") or {}).get("id", "") == self._project_filter
            ]
        if flt:
            issues = [
                i
                for i in issues
                if flt
                in (
                    i["title"]
                    + " "
                    + i["identifier"]
                    + " "
                    + ((i.get("assignee") or {}).get("displayName") or "")
                ).lower()
            ]

        def mine_first(i: dict):
            is_mine = (i.get("assignee") or {}).get("id") == self._viewer_id
            return (0 if is_mine else 1, *issue_sort_key(i))

        if self._group_by == "project":
            # group by project; inside a project keep the status order,
            # then mine-first + recency
            by_proj: dict[str, list[dict]] = {}
            proj_of: dict[str, dict] = {}
            for i in issues:
                p = i.get("project") or {"id": "", "name": "no project", "color": None}
                by_proj.setdefault(p["id"], []).append(i)
                proj_of[p["id"]] = p
            # biggest projects first, the no-project bucket last
            ordered_groups = sorted(
                proj_of.values(),
                key=lambda p: (p["id"] == "", -len(by_proj[p["id"]])),
            )
            def in_group_key(i: dict):
                return (state_sort_key(i["state"]), *mine_first(i))
            groups = [
                (self._project_header_row(p, len(by_proj[p["id"]]), width),
                 sorted(by_proj[p["id"]], key=in_group_key))
                for p in ordered_groups
            ]
        else:
            by_state: dict[str, list[dict]] = {}
            state_of: dict[str, dict] = {}
            for i in issues:
                sid = i["state"]["id"]
                by_state.setdefault(sid, []).append(i)
                state_of[sid] = i["state"]
            ordered_states = sorted(state_of.values(), key=state_sort_key)
            groups = [
                (self._header_row(st, len(by_state[st["id"]]), width),
                 sorted(by_state[st["id"]], key=mine_first))
                for st in ordered_states
            ]

        id_w = max((len(i["identifier"]) for i in issues), default=6)
        ol.clear_options()
        self._opt_index = {}
        opts: list[Option] = []
        first = True
        for header, group in groups:
            if not first:
                opts.append(Option(Text(" "), disabled=True))
            first = False
            opts.append(Option(header, disabled=True))
            for i in group:
                self._opt_index[i["id"]] = len(opts)
                opts.append(Option(self._issue_row(i, width, id_w), id=i["id"]))
        if not opts:
            msg = "no matches" if flt else "no issues"
            opts.append(Option(Text(f"  {msg}", style=C_DIM), disabled=True))
        ol.add_options(opts)

        mine_tag = " \uf007 mine \u00b7" if self._mine else ""
        proj_tag = ""
        if self._project_filter is not None:
            pname = next(
                ((i.get("project") or {}).get("name") for i in self._issues
                 if (i.get("project") or {}).get("id", "") == self._project_filter),
                "no project",
            ) or "no project"
            proj_tag = f" \uf07b {pname} \u00b7"
        self.query_one("#centre").border_subtitle = (
            f"{mine_tag}{proj_tag} {len(issues)} issues "
        )
        if keep and keep in self._opt_index:
            ol.highlighted = self._opt_index[keep]
        elif self._opt_index:
            ol.highlighted = min(self._opt_index.values())

    def _header_row(self, state: dict, count: int, width: int) -> Text:
        color = state["color"] or C_SUB
        t = Text(no_wrap=True, overflow="ellipsis")
        t.append(f"{state_icon(state)} ", style=color)
        t.append(state["name"], style=f"bold {color}")
        t.append(f" · {count} ", style=C_DIM)
        fill = width - t.cell_len - 1
        if fill > 0:
            t.append("─" * fill, style=C_FAINT)
        return t

    def _project_header_row(self, project: dict, count: int, width: int) -> Text:
        color = project.get("color") or C_DIM
        t = Text(no_wrap=True, overflow="ellipsis")
        t.append("\uf07b ", style=color)
        t.append(project["name"], style=f"bold {color}")
        t.append(f" \u00b7 {count} ", style=C_DIM)
        fill = width - t.cell_len - 1
        if fill > 0:
            t.append("\u2500" * fill, style=C_FAINT)
        return t

    def _issue_row(self, issue: dict, width: int, id_w: int) -> Text:
        st = issue["state"]
        t = Text(no_wrap=True, overflow="ellipsis")
        t.append(f"{state_icon(st)} ", style=st["color"] or C_SUB)
        t.append(issue["identifier"].ljust(id_w), style=C_DIM)
        t.append(" ")

        assignee = (issue.get("assignee") or {}).get("displayName") or ""
        assignee = assignee.split()[0][:10] if assignee else "—"
        time_s = rel_time(issue["updatedAt"])
        labels = issue["labels"]["nodes"][:3]
        blocked_by, blocks = block_info(issue)
        badges = []
        if blocked_by:
            badges.append((" \uf056", C_RED))  # blocked by something
        if blocks:
            badges.append((" \uf06a", C_PEACH))  # blocking something

        right_w = 3 + 2 + 10 + 2 + 4  # prio, gap, assignee, gap, time
        title_w = width - 2 - id_w - 1 - right_w - 1
        dots_w = len(labels) * 2 + len(badges) * 2
        title = issue["title"]
        avail = max(title_w - dots_w, 8)
        if len(title) > avail:
            title = title[: avail - 1] + "…"
        t.append(title, style=C_TEXT)
        for badge, color in badges:
            t.append(badge, style=color)
        for lb in labels:
            t.append(" ●", style=lb["color"] or C_DIM)
        pad = title_w - len(title) - dots_w
        if pad > 0:
            t.append(" " * pad)

        t.append(" ")
        t.append_text(priority_cell(issue["priority"]))
        t.append("  ")
        style = C_SUB if assignee != "—" else C_VFAINT
        t.append(assignee.ljust(10), style=style)
        t.append("  ")
        t.append(time_s.rjust(4), style=C_DIM)
        return t

    # ── detail panel ──────────────────────────────────────────────────
    def show_detail(self, issue: dict) -> None:
        self._detail_issue = issue
        parent_w = self.query_one("#d-parent", Static)
        parent_w.update("")
        parent_w.remove_class("visible")
        children_w = self.query_one("#d-children", Vertical)
        children_w.remove_class("visible")
        children_w.remove_children()
        panel = self.query_one("#detail")
        was_closed = not panel.has_class("open")
        panel.add_class("open")
        self.query_one("#split-right").add_class("open")
        if was_closed:
            pop_in(panel, duration=0.18)
        panel.border_title = f"  {issue['identifier']} "
        panel.border_subtitle = f" {rel_time(issue['updatedAt'])} ago "
        self.query_one("#d-title", Static).update(
            Text(issue["title"], style=f"bold {C_TEXT}")
        )
        self._update_detail_meta(issue)
        desc = issue.get("description") or "*no description*"
        self.query_one("#d-desc", Markdown).update(desc)
        self.query_one("#d-scroll", DetailScroll).scroll_home(animate=False)
        self.load_comments(issue)

    def _update_detail_meta(self, issue: dict) -> None:
        st = issue["state"]
        m = Text()
        m.append(f"{state_icon(st)} ", style=st["color"] or C_SUB)
        m.append(st["name"], style=f"bold {st['color'] or C_SUB}")
        m.append("   ")
        m.append_text(priority_cell(issue["priority"]))
        m.append(f" {priority_name(issue['priority'])}", style=C_SUB)
        m.append("   ")
        m.append(" ", style=C_DIM)
        assignee = (issue.get("assignee") or {}).get("displayName") or "unassigned"
        m.append(assignee, style=C_SUB)
        project = issue.get("project")
        if project:
            m.append("   ")
            m.append("\uf07b ", style=project.get("color") or C_DIM)
            m.append(project["name"], style=C_SUB)
        labels = issue["labels"]["nodes"]
        if labels:
            m.append("\n")
            for lb in labels:
                m.append(" ", style=lb["color"] or C_DIM)
                m.append(f"{lb['name']}  ", style=C_SUB)
        blocked_by, blocks = block_info(issue)
        if blocked_by or blocks:
            m.append("\n")
            if blocked_by:
                m.append("\uf056 ", style=C_RED)
                m.append("blocked by " + " \u00b7 ".join(blocked_by), style=C_RED)
            if blocked_by and blocks:
                m.append("   ")
            if blocks:
                m.append("\uf06a ", style=C_PEACH)
                m.append("blocks " + " \u00b7 ".join(blocks), style=C_PEACH)
        m.append("\n")
        m.append(" ", style=C_DIM)
        m.append(
            f"created {parse_dt(issue['createdAt']).strftime('%b %d')}"
            f" · updated {rel_time(issue['updatedAt'])} ago",
            style=C_DIM,
        )
        self.query_one("#d-meta", Static).update(m)

    def close_detail(self) -> None:
        self._detail_issue = None
        self.query_one("#detail").remove_class("open")
        self.query_one("#split-right").remove_class("open")
        self.query_one("#issues").focus()

    def _current_issue(self) -> dict | None:
        if self._detail_issue is not None:
            return self._detail_issue
        ol = self.query_one("#issues", NavList)
        if ol.highlighted is None:
            return None
        opt = ol.get_option_at_index(ol.highlighted)
        if opt is None or opt.id is None:
            return None
        return self._issue_by_id.get(opt.id)

    # ── events ────────────────────────────────────────────────────────
    @on(OptionList.OptionSelected, "#teams")
    def _team_selected(self, event: OptionList.OptionSelected) -> None:
        team = next((t for t in self._teams if t["id"] == event.option.id), None)
        if team and (self._team is None or team["id"] != self._team["id"]):
            if self._detail_issue:
                self.close_detail()
            self.load_team(team)

    @on(OptionList.OptionSelected, "#issues")
    def _issue_selected(self, event: OptionList.OptionSelected) -> None:
        issue = self._issue_by_id.get(event.option.id or "")
        if issue:
            self.show_detail(issue)
            self.query_one("#d-scroll").focus()

    @on(Input.Changed, "#filter")
    def _filter_changed(self, event: Input.Changed) -> None:
        self._filter = event.value
        self.render_issues()

    @on(Input.Submitted, "#filter")
    def _filter_submitted(self) -> None:
        self.query_one("#issues").focus()

    # ── actions ───────────────────────────────────────────────────────
    def action_refresh(self) -> None:
        if self._team:
            self.load_team(self._team)

    def _tick_fx(self) -> None:
        try:
            self.query_one("#profile")
        except Exception:
            return  # DOM not ready or tearing down — timers can outlive it
        # name wave: sweep, rest, repeat — renders only while sweeping
        if self._viewer_name:
            if self._wave_rest > 0:
                self._wave_rest -= 1
            else:
                self._wave_pos += 1
                if self._wave_pos >= len(self._viewer_name):
                    self._wave_pos = -1
                    self._wave_rest = FX_REST_TICKS
                self._update_profile()
                self._update_header()
        # braille spinner while a background refresh is in flight
        if self._refreshing:
            self._spin_frame = (self._spin_frame + 1) % len(SPINNER_FRAMES)
            frame = SPINNER_FRAMES[self._spin_frame]
            try:
                self.query_one("#centre").border_subtitle = (
                    f" {len(self._issues)} \u00b7 {frame} refreshing "
                )
            except Exception:
                pass

    def _update_header(self) -> None:
        if self._org is None or self._viewer_name is None:
            return
        markup = (
            f"[bold {C_BLUE}] \uf03a [/]"
            + wave_markup("ltui", self._wave_pos, f"bold {C_BLUE}", C_LAV)
            + f"[{C_VFAINT}]  \u00b7  [/][{C_SUB}]{escape(self._org)}[/]"
            + f"[{C_VFAINT}] / [/][{C_DIM}]{escape(self._viewer_name)}[/]"
        )
        self.query_one("#appheader", Static).update(markup)

    def _update_profile(self) -> None:
        if self._viewer_name:
            name = wave_markup(
                self._viewer_name, self._wave_pos, f"bold {C_TEXT}", C_BLUE
            )
        else:
            name = f"[bold {C_TEXT}]\u2026[/]"
        org = escape(self._org or "connecting")
        mine = "on" if self._mine else "off"
        mine_color = C_GREEN if self._mine else C_DIM
        self.query_one("#profile", Static).update(
            " " + name + "\n"
            f"[{C_DIM}] {org}[/]\n"
            f"[@click=app.change_theme][{C_SUB}] [/][{C_SUB}]{self.theme}[/][/]\n"
            f"[@click=app.toggle_mine][{C_SUB}] mine [/][{mine_color}]{mine}[/][/]\n"
            f"[@click=app.open_settings][{C_BLUE}] settings[/][/]"
        )

    def action_open_settings(self) -> None:
        if isinstance(self.screen, SettingsModal):
            return
        self.push_screen(SettingsModal())

    def action_help(self) -> None:
        if isinstance(self.screen, HelpModal):
            return
        self.push_screen(HelpModal())

    def action_change_theme(self) -> None:
        if isinstance(self.screen, ThemeModal):
            return
        self.push_screen(ThemeModal())

    def action_cycle_theme(self) -> None:
        idx = THEME_NAMES.index(self.theme) if self.theme in THEME_NAMES else -1
        self.theme = THEME_NAMES[(idx + 1) % len(THEME_NAMES)]
        self.notify(f" theme → {self.theme}")

    def action_new_ticket(self) -> None:
        team = self._team
        if team is None:
            return

        def done(result: tuple | None) -> None:
            if result:
                self.create_issue(team, result[0], result[1])

        self.push_screen(NewTicketModal(f" new ticket · {team['key']}"), done)

    def action_pick_project(self) -> None:
        projects: dict[str, dict] = {}
        counts: dict[str, int] = {}
        for i in self._issues:
            p = i.get("project") or {"id": "", "name": "no project", "color": None}
            projects[p["id"]] = p
            counts[p["id"]] = counts.get(p["id"], 0) + 1
        opts = []
        row = Text()
        row.append("\uf03a ", style=C_BLUE)
        row.append("all projects", style=C_TEXT)
        if self._project_filter is None:
            row.append("  \uf00c", style=C_GREEN)
        opts.append(Option(row, id="all:"))
        for pid, p in sorted(projects.items(), key=lambda x: (x[0] == "", -counts[x[0]])):
            row = Text()
            row.append("\uf07b ", style=p.get("color") or C_DIM)
            row.append(p["name"], style=C_TEXT)
            row.append(f"  {counts[pid]}", style=C_DIM)
            if self._project_filter == pid:
                row.append("  \uf00c", style=C_GREEN)
            opts.append(Option(row, id=f"proj:{pid}"))

        def done(choice: str | None) -> None:
            if choice is None:
                return
            if choice == "all:":
                self._project_filter = None
            else:
                self._project_filter = choice.removeprefix("proj:")
            self.render_issues()

        self.push_screen(PickerModal("filter by project", opts), done)

    def action_toggle_group(self) -> None:
        self._group_by = "project" if self._group_by == "status" else "status"
        self._save_state()
        self.render_issues()
        self.notify(f"\uf0ca grouping by {self._group_by}")

    def action_toggle_mine(self) -> None:
        self._mine = not self._mine
        self._save_state()
        self._update_profile()
        self.render_issues()

    def action_filter(self) -> None:
        f = self.query_one("#filter", FilterInput)
        f.add_class("visible")
        f.focus()

    def action_back(self) -> None:
        f = self.query_one("#filter", FilterInput)
        if self._detail_issue is not None:
            self.close_detail()
        elif f.has_class("visible"):
            f.action_dismiss_filter()

    def action_change_status(self) -> None:
        issue = self._current_issue()
        if not issue or not self._states:
            return
        opts = []
        for s in sorted(self._states, key=state_sort_key):
            row = Text()
            row.append(f"{state_icon(s)} ", style=s["color"] or C_SUB)
            row.append(s["name"], style=C_TEXT)
            if s["id"] == issue["state"]["id"]:
                row.append("  ", style=C_GREEN)
            opts.append(Option(row, id=s["id"]))

        def done(state_id: str | None) -> None:
            if state_id and state_id != issue["state"]["id"]:
                self.apply_status(issue, state_id)

        self.push_screen(PickerModal(f"move {issue['identifier']}", opts), done)

    def action_change_priority(self) -> None:
        issue = self._current_issue()
        if not issue:
            return
        opts = []
        for p, label in PRIORITIES:
            row = Text()
            row.append_text(priority_cell(p))
            row.append(f" {label}", style=C_TEXT)
            if p == issue["priority"]:
                row.append("  ", style=C_GREEN)
            opts.append(Option(row, id=str(p)))

        def done(pid: str | None) -> None:
            if pid is not None and int(pid) != issue["priority"]:
                self.apply_priority(issue, int(pid))

        self.push_screen(PickerModal(f"priority · {issue['identifier']}", opts), done)

    def action_change_assignee(self) -> None:
        issue = self._current_issue()
        if not issue or self._team is None:
            return
        self.pick_assignee(issue)

    @work(exclusive=True, group="members")
    async def pick_assignee(self, issue: dict) -> None:
        team = self._team
        members = self._members.get(team["id"])
        if members is None:
            try:
                data = await self.gql(QL_MEMBERS, {"teamId": team["id"]})
                members = data["team"]["members"]["nodes"]
            except Exception as e:
                self.notify(f"linear: {e}", severity="error")
                return
            self._members[team["id"]] = members
        if self._team is None or self._team["id"] != team["id"]:
            return  # user switched teams while fetching
        current = (issue.get("assignee") or {}).get("id")
        opts = []
        if self._viewer_id:
            row = Text(no_wrap=True, overflow="ellipsis")
            row.append("\uf007 ", style=C_BLUE)
            row.append(f"me ({self._viewer_name})", style=C_TEXT)
            if self._viewer_id == current:
                row.append("  \uf00c", style=C_GREEN)
            opts.append(Option(row, id=self._viewer_id))
        for m in members:
            if m["id"] == self._viewer_id:
                continue
            row = Text(no_wrap=True, overflow="ellipsis")
            row.append("\uf007 ", style=C_MAUVE)
            row.append(m["displayName"], style=C_TEXT)
            if m["id"] == current:
                row.append("  \uf00c", style=C_GREEN)
            opts.append(Option(row, id=m["id"]))
        row = Text()
        row.append("\uf05e ", style=C_DIM)
        row.append("unassign", style=C_SUB)
        if current is None:
            row.append("  \uf00c", style=C_GREEN)
        opts.append(Option(row, id="none:"))

        def done(assignee_id: str | None) -> None:
            if assignee_id is None:
                return
            new_id = None if assignee_id == "none:" else assignee_id
            if new_id != current:
                self.apply_assignee(issue, new_id)

        self.push_screen(PickerModal(f"assign {issue['identifier']}", opts), done)

    def action_add_comment(self) -> None:
        issue = self._current_issue()
        if not issue:
            return

        def done(body: str | None) -> None:
            if body:
                self.submit_comment(issue, body)

        self.push_screen(CommentModal(f" comment on {issue['identifier']}"), done)

    def action_open_browser(self) -> None:
        issue = self._current_issue()
        if issue and issue.get("url"):
            webbrowser.open(issue["url"])
            self.notify(f" opened {issue['identifier']}")

    def action_yank(self) -> None:
        issue = self._current_issue()
        if not issue:
            return
        # old disk caches predate branchName — fall back to a sane guess
        branch = issue.get("branchName") or issue["identifier"].lower()
        opts = []
        for icon, label, value in (
            ("\ue725", "branch", branch),
            ("\uf0c1", "url", issue.get("url") or ""),
            ("\uf02b", "identifier", issue["identifier"]),
        ):
            if not value:
                continue
            row = Text(no_wrap=True, overflow="ellipsis")
            row.append(f"{icon} ", style=C_MAUVE)
            row.append(label, style=C_TEXT)
            row.append(f"  {value}", style=C_DIM)
            opts.append(Option(row, id=value))

        def done(value: str | None) -> None:
            if not value:
                return
            self.copy_to_clipboard(value)
            disp = value if len(value) <= 50 else value[:49] + "…"
            self.notify(f" copied {escape(disp)}")

        self.push_screen(PickerModal(f"yank · {issue['identifier']}", opts), done)


HELP = """ltui - a fast, clean TUI for Linear   https://github.com/Gheat1/ltui

usage: ltui [--version] [--help]

auth: LINEAR_API_KEY env var, ~/.config/ltui/config.toml, or
      linear-cli's config. no key? ltui asks on first launch.

keys: enter open ticket   n new   s status   p priority   c comment
      a assign   o browser   y yank   / filter   m mine only   v group
      V one project   t theme
      , settings   j/k navigate   g/G top/bottom   r refresh   ? help
      q quit

mouse: everything clicks; drag the panel dividers to resize,
       double-click a divider to reset"""


def main() -> None:
    if "--version" in sys.argv or "-v" in sys.argv:
        print(f"ltui {__version__}")
        return
    if "--help" in sys.argv or "-h" in sys.argv:
        print(f"ltui {__version__}\n{HELP}")
        return
    LTUI().run()


if __name__ == "__main__":
    main()
