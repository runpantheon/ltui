import unittest
from pathlib import Path
import sys
from unittest import mock

sys.path.insert(0, str(Path(__file__).parents[1]))
sys.path.insert(0, str(Path(__file__).parents[1] / "tools"))

import ltui  # noqa: E402


class SidebarToggleTest(unittest.IsolatedAsyncioTestCase):
    """Drive the demo board from tools/screenshots.py (no network)."""

    async def asyncSetUp(self) -> None:
        self.state = {"theme": "mocha", "team_id": "t-core", "welcomed": True}
        self.saved: list[dict] = []
        await self._make_app()

    async def _make_app(self) -> None:
        import screenshots

        for name, fn in {
            "load_api_key": lambda: "demo",
            "read_cache": lambda name: None,
            "write_cache": lambda name, data: None,
            "load_state": lambda: dict(self.state),
            "save_state": self._save,
        }.items():
            patcher = mock.patch.object(ltui, name, fn)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.app = screenshots.DemoApp()

    def _save(self, data: dict) -> None:
        self.saved.append(dict(data))
        self.state = dict(data)

    async def _ready(self, pilot) -> None:
        for _ in range(40):
            await pilot.pause(0.1)
            if self.app.query_one("#issues").option_count:
                return

    async def test_b_hides_and_shows_the_sidebar(self) -> None:
        async with self.app.run_test(size=(148, 41)) as pilot:
            await self._ready(pilot)
            sidebar = self.app.query_one("#sidebar")
            self.assertTrue(sidebar.display)
            width = sidebar.outer_size.width

            await pilot.press("b")
            await pilot.pause(0.1)
            self.assertFalse(sidebar.display)
            self.assertFalse(self.app.query_one("#split-left").display)
            self.assertTrue(self.saved[-1]["sidebar_hidden"])

            await pilot.press("b")
            await pilot.pause(0.1)
            self.assertTrue(sidebar.display)
            self.assertEqual(sidebar.outer_size.width, width)
            self.assertFalse(self.saved[-1]["sidebar_hidden"])

    async def test_left_arrow_skips_a_hidden_sidebar(self) -> None:
        async with self.app.run_test(size=(148, 41)) as pilot:
            await self._ready(pilot)
            await pilot.press("left")
            await pilot.pause(0.1)
            self.assertEqual(self.app.focused.id, "teams")

            # hiding it while focused hands focus back to the issues
            await pilot.press("b")
            await pilot.pause(0.1)
            self.assertEqual(self.app.focused.id, "issues")
            await pilot.press("left")
            await pilot.pause(0.1)
            self.assertEqual(self.app.focused.id, "issues")

    async def test_hidden_state_is_restored_on_start(self) -> None:
        self.state["sidebar_hidden"] = True
        await self._make_app()
        async with self.app.run_test(size=(148, 41)) as pilot:
            await self._ready(pilot)
            self.assertFalse(self.app.query_one("#sidebar").display)


if __name__ == "__main__":
    unittest.main()
