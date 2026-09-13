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


if __name__ == "__main__":
    unittest.main()
