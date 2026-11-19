import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import ltui  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402
from rich.text import Text  # noqa: E402


def render(renderable, width: int) -> list[str]:
    console = Console(
        width=width, record=True, color_system=None, file=io.StringIO()
    )
    console.print(renderable)
    return [line.rstrip() for line in console.export_text().splitlines()]


class HangingRowTest(unittest.TestCase):
    def test_icon_row_wraps_under_its_label(self) -> None:
        row = Text(" Chat-first onboarding and time-to-value for launch")
        lines = render(ltui.hanging(row), 24)
        self.assertGreater(len(lines), 1)
        self.assertTrue(lines[0].startswith(" Chat-first"))
        for line in lines[1:]:
            self.assertTrue(line.startswith("  ") and line[2] != " ", line)

    def test_other_rows_pass_through(self) -> None:
        truncating = Text(" long name", no_wrap=True, overflow="ellipsis")
        self.assertIs(ltui.hanging(truncating), truncating)
        no_icon = Text("me (nova)")
        self.assertIs(ltui.hanging(no_icon), no_icon)
        self.assertIsInstance(ltui.hanging(Text(" x y")), Table)


class FitWidthTest(unittest.TestCase):
    def test_grows_to_the_longest_row_but_not_below_minimum(self) -> None:
        rows = [Text("short"), Text("x" * 60)]
        self.assertEqual(ltui.fit_width(rows, 44, 8), 68)
        self.assertEqual(ltui.fit_width([Text("short")], 44, 8), 44)
        self.assertEqual(ltui.fit_width([], 44, 8), 44)


class HelpBodyTest(unittest.TestCase):
    def test_descriptions_wrap_under_the_description_column(self) -> None:
        sections = [("navigate", [
            ("ctrl+d / ctrl+u", "half page down / up"),
            ("esc", "close panel · dismiss modal · clear filter"),
        ])]
        lines = render(ltui.help_body(sections), 40)
        desc_col = lines[1].index("half")
        wrapped = [l for l in lines[2:] if l and not l.lstrip().startswith("esc")]
        self.assertTrue(wrapped, lines)
        for line in wrapped:
            self.assertEqual(len(line) - len(line.lstrip()), desc_col, lines)


if __name__ == "__main__":
    unittest.main()
