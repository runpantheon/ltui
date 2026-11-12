import unittest
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).parents[1]))

import ltui  # noqa: E402


def issue(ident: str, priority: int, updated: str) -> dict:
    return {"identifier": ident, "priority": priority, "updatedAt": updated}


class SortKeyTest(unittest.TestCase):
    issues = [
        issue("none", 0, "2026-11-10T00:00:00Z"),
        issue("low", 4, "2026-11-09T00:00:00Z"),
        issue("urgent-old", 1, "2026-11-01T00:00:00Z"),
        issue("urgent-new", 1, "2026-11-05T00:00:00Z"),
        issue("high", 2, "2026-11-02T00:00:00Z"),
    ]

    def order(self, sort_by: str) -> list[str]:
        ranked = sorted(self.issues, key=lambda i: ltui.issue_sort_key(i, sort_by))
        return [i["identifier"] for i in ranked]

    def test_recent_is_default(self) -> None:
        self.assertEqual(
            sorted(self.issues, key=ltui.issue_sort_key),
            sorted(self.issues, key=lambda i: ltui.issue_sort_key(i, "recent")),
        )
        self.assertEqual(
            self.order("recent"),
            ["none", "low", "urgent-new", "high", "urgent-old"],
        )

    def test_priority_puts_urgent_first_and_no_priority_last(self) -> None:
        self.assertEqual(
            self.order("priority"),
            ["urgent-new", "urgent-old", "high", "low", "none"],
        )

    def test_default_keybinding_toggles_sort(self) -> None:
        self.assertTrue(
            any(
                b.key == "S" and b.action == "toggle_sort"
                for b in ltui.build_bindings({})
            )
        )


if __name__ == "__main__":
    unittest.main()
