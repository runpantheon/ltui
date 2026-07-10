<div align="center">

# ◐ sctui

**A stupidly fast, actually beautiful TUI for [Shortcut](https://www.shortcut.com).**

Your whole workspace, grouped the way triage actually works —
`In Review` on top, `Done` at the bottom, your tickets first.

[![python](https://img.shields.io/badge/python-3.11+-89b4fa?style=flat-square&logo=python&logoColor=white)](https://www.python.org)
[![built with textual](https://img.shields.io/badge/built%20with-textual-b4befe?style=flat-square)](https://github.com/Textualize/textual)
[![license](https://img.shields.io/badge/license-GPLv3%20%2B%20commercial-a6e3a1?style=flat-square)](LICENSE)
[![shortcut api](https://img.shields.io/badge/shortcut-rest%20api%20v3-58b1e4?style=flat-square)](https://developer.shortcut.com/api/rest/v3)

<img src="assets/hero.png" alt="sctui — issue list with detail panel" width="100%">

<sub>every screenshot in this README is generated from <b>fake demo data</b> by
<a href="tools/screenshots.py"><code>tools/screenshots.py</code></a> — no real tickets were harmed</sub>

</div>

---

> [!NOTE]
> **not on Shortcut?** this repo also ships [**ltui**](../ltui/) for Linear and
> [**jtui**](../jtui/) for Jira — same app, same speed, same themes.

## why another Shortcut TUI?

Because every Shortcut TUI I tried had the same two problems: **slow** and **ugly**.

The slowness isn't even their fault — big issue trackers take seconds to
return a decently sized team. Most TUIs just make you eat that wait on every
launch. sctui doesn't:

- 📦 **instant startup** — your last-seen issues render from a local cache in
  ~50ms while fresh data loads in the background. You're scrolling before the
  API has even said hello.
- 🎨 **actually pretty** — rounded borders, five themes,
  Shortcut's own state colors, nerd font icons, priority bars like the real app,
  and subtle fade animations on panels and modals.
- ⌨️ **keyboard first, mouse welcome** — vim keys everywhere, but everything is
  also clickable: tickets, teams, even the hint bar. The panel dividers
  **drag to resize** (double-click to reset), and your layout sticks.

## features

|     |                                                                                     |
| --- | ----------------------------------------------------------------------------------- |
| 🗂️  | **smart grouping** — `In Review` → `In Progress` → `Todo` → `Backlog` → `Done` — sorted by how close work is to shipping, freshest tickets first inside every group |
| 👤  | **mine first** — your tickets float to the top of every group; press `m` to hide everyone else entirely |
| 📁  | **project view** — `v` regroups the whole board by **epic** (color-coded, status-ordered inside); the detail panel names each ticket's epic |
| 🌿  | **`y` yanks a git branch** — a clean generated branch name (key + slug) straight to your clipboard (or the URL / identifier); ticket → `git checkout -b` in seconds |
| 👥  | **assign without leaving** — `a` reassigns to anyone on the team, or you, or nobody |
| 🌳  | **hierarchy aware** — the detail panel shows the parent issue and all subtasks with a done-count, next to blocked/blocking relations |
| 🔄  | **never stale** — the board silently re-syncs every 3 minutes |
| 📖  | **rich detail panel** — full markdown descriptions (code blocks, checklists, quotes), labels, comments — scrolls with arrows, vim keys, or mouse wheel |
| ✏️  | **write, don't just read** — create tickets, change status & priority, add comments without leaving the terminal |
| 🚧  | **blocked & blocking at a glance** — a red badge on tickets that are blocked, an orange one on tickets holding others up; the detail panel names the exact tickets |
| 🔍  | **instant filter** — `/` fuzzy-narrows by title, identifier, or assignee as you type |
| 🌚  | **five themes** — `mocha`, pure-black `void`, monochrome `onyx`, `clear` (no background — your terminal's transparency/blur shows through), and `system` (drawn in your terminal's own ANSI palette: your kitty theme *is* the sctui theme) — cycle with `t` |
| ⚙️  | **profile & settings** — who you are bottom-left, `,` opens a settings panel with live theme preview, preferences, and cache controls |
| 🧠  | **remembers everything** — last team, theme, filters persist across sessions |
| 🎛️  | **fully remappable** — every key rebindable via `~/.config/sctui/config.json` (`sctui --init-config`), with a vim motion layer (`ctrl+d/u`, `[`/`]` group jumps, `:` palette) out of the box |
| 🔌  | **one-time setup** — site + email + API token, asked for in-app on first launch |

## install

works on any linux · macOS · windows, straight from this repo.
grab [uv](https://docs.astral.sh/uv/) or [pipx](https://pipx.pypa.io) and:

```sh
uv tool install "git+https://github.com/runpantheon/ltui#subdirectory=sctui"
# or
pipx install "git+https://github.com/runpantheon/ltui#subdirectory=sctui"
```

or build it yourself from source:

```sh
git clone https://github.com/runpantheon/ltui && cd ltui/sctui
pip install .
```

either way you now have the command:

```sh
sctui
```

upgrading later: `uv tool upgrade sctui` / `pipx reinstall sctui`.

<details>
<summary><b>platform notes</b></summary>

- **linux** — any terminal that isn't from 1985 works: kitty, alacritty,
  ghostty, wezterm, foot…
- **macOS** — `brew install pipx` first if you don't have it. iTerm2, ghostty,
  kitty, or WezTerm recommended over stock Terminal.app.
- **windows** — Python 3.11+ (`winget install Python.Python.3.12`), then pipx.
  Run it in **Windows Terminal** — legacy conhost will not do it justice.
- everywhere: needs **python ≥ 3.11**.

</details>

> [!TIP]
> Use a terminal with a [nerd font](https://www.nerdfonts.com/) for the icons.
> Everything else degrades gracefully without one.

## auth

**one token, once.** launch `sctui` and it asks for a Shortcut API token
(click the link in the app — it opens Shortcut → Settings → API Tokens).
validated live, stored in `~/.config/sctui/config.toml` (permissions `600`).
or set `SHORTCUT_API_TOKEN` and it never asks.

<div align="center">
<img src="assets/onboard.png" alt="first-run onboarding" width="70%">
</div>

Your token never leaves your machine — sctui talks directly to
`api.app.shortcut.com` and nothing else.

First launch also greets you with a 20-second tour card (once, never again),
and `?` opens the full keybinding cheatsheet whenever you need it.

<div align="center">
<img src="assets/welcome.png" alt="first-run welcome" width="60%">
</div>

## keys

| key      | action                                        |
| -------- | --------------------------------------------- |
| `↑↓` `jk` | move around (lists *and* the detail panel)   |
| `enter` / click | open ticket detail panel                |
| `esc`    | close panel / dismiss modal / clear filter    |
| `n`      | **new ticket** in the current team            |
| `s`      | change **status**                             |
| `p`      | change **story type** (bug / feature / chore) |
| `a`      | change **assignee** (or unassign)             |
| `l`      | edit **labels** (multi-select)                |
| `P`      | move to an **epic** — or create one inline    |
| `c`      | add a **comment** (`ctrl+s` to send)          |
| `o`      | open ticket in **browser**                    |
| `y`      | **yank** — copy branch name / url / id        |
| `/`      | filter issues                                 |
| `m`      | toggle **mine only**                          |
| `v`      | group by **status / epic**                 |
| `V`      | filter to a **single epic**                |
| `t`      | cycle **theme**                               |
| `,`      | open **settings**                             |
| `r`      | refresh                                       |
| `g` `G`  | jump to top / bottom                          |
| `ctrl+d/u` `ctrl+f/b` | half page / full page             |
| `[` `]`  | previous / next **group**                     |
| `:`      | command palette                               |
| `?`      | **help** — keybinding cheatsheet              |
| `q`      | quit                                          |

## epic view

`v` flips the board from status columns to **epics** — each epic gets a
color-coded section (freshest work first, status order inside), with tickets
that belong to no epic collected at the bottom. Press `v` again to go back —
or `V` to zoom into a **single epic** (works in either grouping).

<div align="center">
<img src="assets/projects.png" alt="group by project" width="80%">
</div>

## make it yours

every keybind is remappable, vim-style motions included:

```sh
sctui --init-config    # writes ~/.config/sctui/config.json
```

```jsonc
{
  "keybinds": {
    "new_ticket": "n",            // any action -> any key
    "yank": ["y", "ctrl+y"]       // or several keys
  },
  "options": {
    "auto_refresh_seconds": 180,  // 0 disables background sync
    "animations": true            // false = no fades, no name wave
  }
}
```

key names are [Textual key names](https://textual.textualize.io/guide/input/#key)
(`slash`, `comma`, `question_mark`, `ctrl+x`, …). unknown or invalid entries
fall back to the defaults; changes apply on restart.

## the detail panel

`enter` (or a click) opens any ticket in a side panel — markdown description
rendered properly, comments threaded underneath, and every action one key away.
The footer hints are clickable too.

<div align="center">
<img src="assets/picker.png" alt="status picker" width="80%">
</div>

## creating tickets

`n` opens a minimal composer: title, optional markdown description, `ctrl+s`.
The ticket lands in your list already highlighted, ready for `s` / `p` to
slot it into the right column.

<div align="center">
<img src="assets/new-ticket.png" alt="new ticket modal" width="80%">
</div>

## settings

Your profile lives bottom-left — name, org, and one-click toggles for theme
and mine-only. Press `,` (or click ` settings`) for the panel:
flip preferences, clear the cache.

<div align="center">
<img src="assets/settings.png" alt="settings panel" width="80%">
</div>

## themes

Cycle with `t`. Your choice sticks.

|  `mocha` — catppuccin warmth | `void` — pure black, OLED bait | `onyx` — monochrome steel |
| --- | --- | --- |
| ![mocha](assets/list.png) | ![void](assets/theme-void.png) | ![onyx](assets/theme-onyx.png) |

Two of them can't be screenshotted honestly:

- **`clear`** paints **no background at all** — sctui runs on your terminal's
  own background, so if your terminal is transparent or blurred, sctui is too.
- **`system`** goes further: the whole UI chrome is drawn in your terminal's
  **ANSI palette** (plus the transparent background) — whatever theme your
  kitty/alacritty/ghostty is running, sctui matches it automatically. Ticket
  data (state colors, labels) stays true to Shortcut.

Made for rice.

Not enough? `ctrl+p` → *Change theme* opens the theme picker with **every
built-in Textual theme** — nord, gruvbox, dracula, tokyo-night, rose-pine, the
whole catppuccin family and more. The whole app **restyles live as you scroll**
the list; `enter` keeps it, `esc` puts everything back. `t` keeps cycling the
four sctui themes.

<div align="center">
<img src="assets/themes.png" alt="theme picker with live preview" width="80%">
</div>

## how it's fast

Shortcut's API is the bottleneck — fetching a busy project takes seconds,
and no client can fix that. So sctui stops pretending the network is fast:

```
launch ──▶ render cached issues (~50ms) ──▶ you're already working
                    │
                    └──▶ background refresh ──▶ rows swap in silently
```

- issue lists cache to `~/.cache/sctui/` per team
- mutations (status, priority, new tickets) update the cache immediately —
  what you see is always what you did
- the `↻ refreshing` badge in the border tells you when fresh data is inbound
- the board silently re-syncs every 3 minutes, so it never goes stale

## data & privacy

- **reads**: teams, issues, workflow states, comments — for the teams you view
- **writes**: only the mutations you explicitly trigger (create / status /
  priority / comment)
- **talks to**: your own Shortcut site — nothing else, no telemetry, no analytics
- **stores locally**: cache in `~/.cache/sctui/`, UI state in
  `~/.local/state/sctui/state.json`

## faq

<details>
<summary><b>Only ~250 issues show per team?</b></summary>

sctui fetches the 250 most-recently-updated issues per team. For triage that's
effectively everything alive; ancient `Done` tickets fall off the bottom,
which is where they belong.

</details>

<details>
<summary><b>Why do the screenshots look fake?</b></summary>

Because they are! They're generated by <code>tools/screenshots.py</code> with a
mocked API — fake org, fake tickets, fake people. Run it yourself; it never
touches the network.

</details>

<details>
<summary><b>Some icons render as boxes</b></summary>

Install a <a href="https://www.nerdfonts.com/">nerd font</a> and set it as your
terminal font. Everything else degrades gracefully.

</details>

<details>
<summary><b>Does it work with multiple workspaces?</b></summary>

One site at a time (whatever is in <code>~/.config/sctui/config.toml</code>
or the <code>JIRA_*</code> environment variables). Point the env vars at
another site to switch.

</details>

## contributing

It's one Python file. Read it in ten minutes, break it in five:

```sh
git clone https://github.com/runpantheon/ltui && cd ltui/sctui
python -m venv .venv && .venv/bin/pip install -e . && .venv/bin/sctui
```

PRs welcome — keep it fast, keep it pretty.

## shortcut-flavoured notes

- the sidebar lists your Shortcut **Teams** (groups); `v` groups the board
  by **epic**, `V` filters to one epic.
- there's no priority field in Shortcut, so `p` sets the **story type**
  instead — bug / feature / chore, riding the same picker.
- the detail panel shows the story's **task checklist** with a done-count,
  plus blockers from story links.
- **fresh port**: sctui shares its entire UI with the battle-tested
  [ltui](https://github.com/runpantheon/ltui/tree/main/ltui), but the Shortcut layer is young —
  if your workspace does something exotic, open an issue with the error
  text (it surfaces the API's own messages).

## credits

made by [**@Gheat1**](https://github.com/Gheat1) — issues, ideas, and PRs
welcome over at [Gheat1/sctui](https://github.com/runpantheon/ltui/tree/main/sctui).

sctui is the Shortcut sibling of [**ltui**](https://github.com/runpantheon/ltui/tree/main/ltui) (Linear) and [**jtui**](https://github.com/runpantheon/ltui/tree/main/jtui) (Jira);
the shared design system lives in [**ricekit**](https://github.com/Gheat1/ricekit).

standing on the shoulders of [textual](https://github.com/Textualize/textual)
and the [Shortcut REST API](https://developer.shortcut.com/api/rest/v3).

## license

**Dual-licensed.** [GPL-3.0](../LICENSE) for everyone — free to use anywhere,
work included; forks and redistributions must stay open source with credit,
so closed-source rebranding/resale is not permitted. Need it outside GPL
terms? Pantheon offers commercial licenses — open an issue or reach out.

<div align="center">
<sub>not affiliated with Shortcut — just a fan of good issue trackers and good terminals</sub>
</div>
