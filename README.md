<div align="center">

# ◐ ltui

**A stupidly fast, actually beautiful TUI for [Linear](https://linear.app).**

Your whole workspace, grouped the way triage actually works —
`In Review` on top, `Done` at the bottom, your tickets first.

[![python](https://img.shields.io/badge/python-3.11+-89b4fa?style=flat-square&logo=python&logoColor=white)](https://www.python.org)
[![built with textual](https://img.shields.io/badge/built%20with-textual-b4befe?style=flat-square)](https://github.com/Textualize/textual)
[![license](https://img.shields.io/badge/license-MIT-a6e3a1?style=flat-square)](LICENSE)
[![linear api](https://img.shields.io/badge/linear-graphql%20api-5e6ad2?style=flat-square&logo=linear&logoColor=white)](https://developers.linear.app)

<img src="assets/hero.png" alt="ltui — issue list with detail panel" width="100%">

<sub>every screenshot in this README is generated from <b>fake demo data</b> by
<a href="tools/screenshots.py"><code>tools/screenshots.py</code></a> — no real tickets were harmed</sub>

</div>

---

## why another Linear TUI?

Because every Linear TUI I tried had the same two problems: **slow** and **ugly**.

The slowness isn't even their fault — Linear's GraphQL API takes 2–5 seconds to
return a decently sized team. Most TUIs just make you eat that wait on every
launch. ltui doesn't:

- 📦 **instant startup** — your last-seen issues render from a local cache in
  ~50ms while fresh data loads in the background. You're scrolling before the
  API has even said hello.
- 🎨 **actually pretty** — rounded borders, three hand-tuned dark themes,
  Linear's own state colors, nerd font icons, priority bars like the real app.
- ⌨️ **keyboard first, mouse welcome** — vim keys everywhere, but everything is
  also clickable: tickets, teams, even the hint bar.

## features

|     |                                                                                     |
| --- | ----------------------------------------------------------------------------------- |
| 🗂️  | **smart grouping** — `In Review` → `In Progress` → `Todo` → `Backlog` → `Done` — sorted by how close work is to shipping, not alphabetically |
| 👤  | **mine first** — your tickets float to the top of every group; press `m` to hide everyone else entirely |
| 📖  | **rich detail panel** — full markdown descriptions (code blocks, checklists, quotes), labels, comments — scrolls with arrows, vim keys, or mouse wheel |
| ✏️  | **write, don't just read** — create tickets, change status & priority, add comments without leaving the terminal |
| 🔍  | **instant filter** — `/` fuzzy-narrows by title, identifier, or assignee as you type |
| 🌚  | **four themes** — `mocha`, pure-black `void`, monochrome `onyx`, and `clear` (no background — your terminal's transparency/blur shows through) — cycle with `t` |
| ⚙️  | **profile & settings** — who you are bottom-left, `,` opens a settings panel with live theme preview, preferences, and cache controls |
| 🧠  | **remembers everything** — last team, theme, filters persist across sessions |
| 🔌  | **zero config** — reuses your [linear-cli](https://github.com/Finesssee/linear-cli) API key, or set `LINEAR_API_KEY` |

## install

**arch, btw** — from the [AUR](https://aur.archlinux.org/packages/ltui):

```sh
yay -S ltui
```

**any linux · macOS · windows** — with [pipx](https://pipx.pypa.io) or [uv](https://docs.astral.sh/uv/):

```sh
pipx install ltui-linear      # or: uv tool install ltui-linear
```

<sub>the PyPI name <code>ltui</code> was taken — the command is still <code>ltui</code></sub>

**bleeding edge** — straight from main:

```sh
pipx install git+https://github.com/Gheat1/ltui
```

then just:

```sh
ltui
```

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

ltui looks for a Linear API key in two places, in order:

1. the `LINEAR_API_KEY` environment variable
2. your existing [linear-cli](https://github.com/Finesssee/linear-cli) config
   (`~/.config/linear-cli/config.toml`) — if you already use linear-cli,
   **ltui works with zero setup**

No linear-cli? Grab a personal API key from
**Linear → Settings → Security & access → API keys** and:

```sh
export LINEAR_API_KEY="lin_api_..."   # add to your shell profile
```

Your key never leaves your machine — ltui talks directly to
`api.linear.app` and nothing else.

## keys

| key      | action                                        |
| -------- | --------------------------------------------- |
| `↑↓` `jk` | move around (lists *and* the detail panel)   |
| `enter` / click | open ticket detail panel                |
| `esc`    | close panel / dismiss modal / clear filter    |
| `n`      | **new ticket** in the current team            |
| `s`      | change **status**                             |
| `p`      | change **priority**                           |
| `c`      | add a **comment** (`ctrl+s` to send)          |
| `o`      | open ticket in **browser**                    |
| `/`      | filter issues                                 |
| `m`      | toggle **mine only**                          |
| `t`      | cycle **theme**                               |
| `,`      | open **settings**                             |
| `r`      | refresh                                       |
| `g` `G`  | jump to top / bottom                          |
| `q`      | quit                                          |

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

And the fourth one can't be screenshotted honestly: **`clear`** paints **no
background at all** — ltui runs on your terminal's own background, so if your
terminal is transparent or blurred, ltui is too. Made for rice.

Not enough? The command palette (`ctrl+p` → *Change theme*) also offers
**every built-in Textual theme** — nord, gruvbox, dracula, tokyo-night,
rose-pine, the whole catppuccin family and more — with live preview. `t` keeps
cycling the four ltui themes; anything else you pick sticks until you change it.

## how it's fast

Linear's API is the bottleneck — a 250-issue team takes **2.5–4.5s** to fetch,
and no client can fix that. So ltui stops pretending the network is fast:

```
launch ──▶ render cached issues (~50ms) ──▶ you're already working
                    │
                    └──▶ background refresh ──▶ rows swap in silently
```

- issue lists cache to `~/.cache/ltui/` per team
- mutations (status, priority, new tickets) update the cache immediately —
  what you see is always what you did
- the `↻ refreshing` badge in the border tells you when fresh data is inbound

## data & privacy

- **reads**: teams, issues, workflow states, comments — for the teams you view
- **writes**: only the mutations you explicitly trigger (create / status /
  priority / comment)
- **talks to**: `api.linear.app` — nothing else, no telemetry, no analytics
- **stores locally**: cache in `~/.cache/ltui/`, UI state in
  `~/.local/state/ltui/state.json`

## faq

<details>
<summary><b>Only ~250 issues show per team?</b></summary>

ltui fetches the 250 most-recently-updated issues per team. For triage that's
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

It uses one API key at a time (the linear-cli "current" workspace, or
<code>LINEAR_API_KEY</code>). Switch workspaces the same way you would with
linear-cli.

</details>

## contributing

It's one Python file. Read it in ten minutes, break it in five:

```sh
git clone https://github.com/Gheat1/ltui && cd ltui
python -m venv .venv && .venv/bin/pip install -e . && .venv/bin/ltui
```

PRs welcome — keep it fast, keep it pretty.

## license

[MIT](LICENSE)

<div align="center">
<sub>not affiliated with Linear — just a fan of good issue trackers and good terminals</sub>
</div>
