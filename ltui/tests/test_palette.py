import unittest
from pathlib import Path
import sys
from unittest import mock

sys.path.insert(0, str(Path(__file__).parents[1]))
sys.path.insert(0, str(Path(__file__).parents[1] / "tools"))

import ltui  # noqa: E402
from textual.command import CommandList, CommandPalette  # noqa: E402


class PaletteKeysTest(unittest.IsolatedAsyncioTestCase):
    """Drive the demo board from tools/screenshots.py (no network)."""

    async def asyncSetUp(self) -> None:
        import screenshots

        state = {"theme": "mocha", "team_id": "t-core", "welcomed": True}
        for name, fn in {
            "load_api_key": lambda: "demo",
            "read_cache": lambda name: None,
            "write_cache": lambda name, data: None,
            "load_state": lambda: dict(state),
            "save_state": lambda data: None,
        }.items():
            patcher = mock.patch.object(ltui, name, fn)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.app = screenshots.DemoApp()

    async def _ready(self, pilot) -> None:
        for _ in range(40):
            await pilot.pause(0.1)
            if self.app.query_one("#issues").option_count:
                return

    async def test_ctrl_p_opens_and_ctrl_n_p_move(self) -> None:
        async with self.app.run_test(size=(148, 41)) as pilot:
            await self._ready(pilot)
            await pilot.press("ctrl+p")
            await pilot.pause(0.3)
            self.assertTrue(CommandPalette.is_open(self.app))
            # a query with several hits ("t" matches theme, quit, ...)
            await pilot.press("t")
            await pilot.pause(0.5)
            commands = self.app.screen.query_one(CommandList)
            self.assertGreater(commands.option_count, 2)

            await pilot.press("ctrl+n")
            await pilot.pause(0.1)
            first = commands.highlighted
            await pilot.press("ctrl+n")
            await pilot.pause(0.1)
            self.assertEqual(commands.highlighted, first + 1)
            await pilot.press("ctrl+p")
            await pilot.pause(0.1)
            self.assertEqual(commands.highlighted, first)
            # ctrl+p inside the palette moves; it doesn't close or reopen it
            self.assertTrue(CommandPalette.is_open(self.app))

    async def test_colon_still_opens(self) -> None:
        async with self.app.run_test(size=(148, 41)) as pilot:
            await self._ready(pilot)
            await pilot.press("colon")
            await pilot.pause(0.3)
            self.assertIsInstance(self.app.screen, ltui.LtuiCommandPalette)


if __name__ == "__main__":
    unittest.main()
