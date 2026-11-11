import unittest
from pathlib import Path
import sys

from rich.cells import cell_len

sys.path.insert(0, str(Path(__file__).parents[1]))

import ltui  # noqa: E402


class PriorityCellTest(unittest.TestCase):
    def test_urgent_has_a_visible_icon(self) -> None:
        self.assertTrue(ltui.priority_cell(1).plain.strip())

    def test_every_priority_is_the_same_width(self) -> None:
        widths = {p: cell_len(ltui.priority_cell(p).plain) for p in range(5)}
        self.assertEqual(set(widths.values()), {3}, widths)


if __name__ == "__main__":
    unittest.main()
