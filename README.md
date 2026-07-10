<div align="center">

# ◐ ltui — the tracker TUI suite

**Fast, beautiful terminal UIs for your issue tracker.**
One codebase, three trackers: **Linear · Jira · Shortcut.**

[![python](https://img.shields.io/badge/python-3.11+-89b4fa?style=flat-square&logo=python&logoColor=white)](https://www.python.org)
[![built with textual](https://img.shields.io/badge/built%20with-textual-b4befe?style=flat-square)](https://github.com/Textualize/textual)
[![license](https://img.shields.io/badge/license-Apache--2.0-a6e3a1?style=flat-square)](LICENSE)

<img src="ltui/assets/hero.png" alt="ltui" width="100%">

</div>

---

| app | tracker | install |
| --- | --- | --- |
| [**ltui**](ltui/) | [Linear](https://linear.app) | `pipx install "git+https://github.com/runpantheon/ltui#subdirectory=ltui"` |
| [**jtui**](jtui/) | [Jira](https://www.atlassian.com/software/jira) | `pipx install "git+https://github.com/runpantheon/ltui#subdirectory=jtui"` |
| [**sctui**](sctui/) | [Shortcut](https://www.shortcut.com) | `pipx install "git+https://github.com/runpantheon/ltui#subdirectory=sctui"` |

The three apps share one muscle memory: status-grouped boards (In Review on
top, Done at the bottom, your tickets first), instant cache-first startup,
a rich detail panel, full write support (status, assignee, labels, epics,
comments, new tickets), five themes including a transparent one, a vim
motion layer, fully remappable keys via `config.json`, and drag-to-resize
panels. Each app's README has the full tour.

## history

Built by [**@Gheat1**](https://github.com/Gheat1) — originally three
repositories on his account (the Linear app earned its stars there) —
now developed under the Pantheon organization. The shared design system
lives in [**ricekit**](https://github.com/Gheat1/ricekit).

## license

[Apache-2.0](LICENSE) · Copyright 2026 Gheat / Pantheon · see [NOTICE](NOTICE)
