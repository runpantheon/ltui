import unittest
from datetime import date
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).parents[1]))

import ltui  # noqa: E402


class DueDateHelpersTest(unittest.TestCase):
    today = date(2026, 9, 12)

    def test_relative_labels(self) -> None:
        self.assertEqual(ltui.due_date_label("2026-09-12", self.today), "today")
        self.assertEqual(ltui.due_date_label("2026-09-13", self.today), "tomorrow")
        self.assertEqual(ltui.due_date_label("2026-09-20", self.today), "Sep 20")
        self.assertEqual(
            ltui.due_date_label("2027-01-01", self.today), "Jan 01, 2027"
        )

    def test_row_cell_is_compact(self) -> None:
        self.assertEqual(ltui.due_date_cell("2026-12-31"), "\uf13312/31")

    def test_active_overdue_issue_is_red(self) -> None:
        issue = {"dueDate": "2026-09-11", "state": {"type": "started"}}
        self.assertEqual(ltui.due_date_style(issue, self.today), ltui.C_RED)

    def test_completed_overdue_issue_is_dimmed(self) -> None:
        issue = {"dueDate": "2026-09-11", "state": {"type": "completed"}}
        self.assertEqual(ltui.due_date_style(issue, self.today), ltui.C_DIM)

    def test_default_keybinding_opens_due_date_editor(self) -> None:
        bindings = ltui.build_bindings({})
        self.assertTrue(
            any(
                binding.key == "d" and binding.action == "change_due_date"
                for binding in bindings
            )
        )


class _RowStub:
    """Just enough of LTUI for `_issue_row`, which needs no live app."""

    _all_teams = False

    def _identifier_style(self, issue: dict) -> str:
        return ltui.C_DIM


def make_issue(due: str | None = None) -> dict:
    return {
        "identifier": "LIN-71",
        "title": "Vertical uplift analysis",
        "dueDate": due,
        "updatedAt": "2026-09-14T00:00:00.000Z",
        "priority": 2,
        "state": {"type": "started", "name": "In Progress", "color": "#f9e2af"},
        "assignee": {"id": "u", "displayName": "Ada Lovelace"},
        "labels": {"nodes": []},
        "relations": {"nodes": []},
        "inverseRelations": {"nodes": []},
    }


class IssueRowColumnsTest(unittest.TestCase):
    """A due date is a column of its own, never a stand-in for `updated`."""

    def row(self, issue: dict, show_due: bool, width: int = 100) -> str:
        return ltui.LTUI._issue_row(_RowStub(), issue, width, 7, show_due).plain

    def test_due_date_does_not_replace_the_update_time(self) -> None:
        row = self.row(make_issue("2026-12-31"), show_due=True)
        self.assertIn(ltui.rel_time("2026-09-14T00:00:00.000Z"), row)
        self.assertIn(ltui.due_date_cell("2026-12-31"), row)

    def test_column_is_dropped_when_nothing_asks_for_it(self) -> None:
        row = self.row(make_issue("2026-12-31"), show_due=False)
        self.assertNotIn("\uf133", row)
        self.assertIn(ltui.rel_time("2026-09-14T00:00:00.000Z"), row)

    def test_rows_stay_aligned_with_and_without_a_date(self) -> None:
        dated = ltui.LTUI._issue_row(_RowStub(), make_issue("2026-12-31"), 100, 7, True)
        undated = ltui.LTUI._issue_row(_RowStub(), make_issue(), 100, 7, True)
        self.assertEqual(dated.cell_len, undated.cell_len)

    def test_the_column_costs_the_title_its_own_width(self) -> None:
        wide = self.row(make_issue("2026-12-31"), show_due=False)
        narrow = self.row(make_issue("2026-12-31"), show_due=True)
        self.assertEqual(len(wide), len(narrow))


class DueDateModalLayoutTest(unittest.IsolatedAsyncioTestCase):
    """Every preset has to land inside the box, not past its right edge."""

    async def _preset_regions(self, width: int):
        from textual.app import App
        from textual.widgets import Static

        class Harness(App):
            CSS = ltui.LTUI.CSS

            def __init__(self) -> None:
                super().__init__()
                for theme in ltui.THEMES:
                    self.register_theme(theme)
                self.theme = ltui.THEME_NAMES[0]

            def compose(self):
                yield Static("")

        app = Harness()
        async with app.run_test(size=(width, 30)) as pilot:
            app.push_screen(ltui.DueDateModal("LIN-71", None))
            await pilot.pause()
            await pilot.pause()
            box = app.screen.query_one("#duedate-box").region
            return box, {
                name: app.screen.query_one(f"#duedate-{name}").region
                for name in ("today", "tomorrow", "week", "clear", "save")
            }

    async def test_presets_fit_the_box(self) -> None:
        for width in (120, 80, 50):
            with self.subTest(terminal_width=width):
                box, regions = await self._preset_regions(width)
                for name, region in regions.items():
                    self.assertTrue(
                        box.contains_region(region),
                        f"{name} at {region} escapes the box at {box}",
                    )


if __name__ == "__main__":
    unittest.main()
