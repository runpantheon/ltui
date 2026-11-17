import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parents[1]))
sys.path.insert(0, str(Path(__file__).parents[1] / "tools"))

import ltui  # noqa: E402


class ClearFiltersTest(unittest.IsolatedAsyncioTestCase):
    """Drive the demo board from tools/screenshots.py (no network)."""

    async def asyncSetUp(self) -> None:
        import screenshots

        self.saved = []
        state = {"theme": "mocha", "team_id": "t-core", "welcomed": True}
        for name, fn in {
            "load_api_key": lambda: "demo",
            "read_cache": lambda name: None,
            "write_cache": lambda name, data: None,
            "load_state": lambda: dict(state),
            "save_state": lambda data: self.saved.append(dict(data)),
        }.items():
            patcher = mock.patch.object(ltui, name, fn)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.app = screenshots.DemoApp()
        self.toasts = []
        real_notify = self.app.notify

        def notify(message, *args, **kwargs):
            self.toasts.append(str(message))
            return real_notify(message, *args, **kwargs)

        self.app.notify = notify

    async def _ready(self, pilot) -> int:
        issues = self.app.query_one("#issues")
        for _ in range(40):
            await pilot.pause(0.1)
            if issues.option_count:
                break
        return issues.option_count

    async def test_clears_project_mine_and_text_at_once(self) -> None:
        async with self.app.run_test(size=(148, 41)) as pilot:
            full = await self._ready(pilot)
            issues = self.app.query_one("#issues")

            self.app._project_filter = "p-sync"
            await pilot.press("m")
            await pilot.press("slash", *"zzz", "enter")
            await pilot.pause(0.3)
            self.assertLess(issues.option_count, full)

            await pilot.press("C")
            await pilot.pause(0.3)
            self.assertIsNone(self.app._project_filter)
            self.assertFalse(self.app._mine)
            self.assertEqual(self.app._filter, "")
            self.assertFalse(self.app.query_one("#filter").has_class("visible"))
            self.assertEqual(issues.option_count, full)
            self.assertFalse(self.saved[-1]["mine"])  # mine-only stays off
            self.assertIn("project", self.toasts[-1])
            self.assertIn("mine only", self.toasts[-1])
            self.assertIn("zzz", self.toasts[-1])

            # the point of it: then / straight to one ticket
            await pilot.press("slash", *"core-1")
            await pilot.pause(0.3)
            self.assertGreater(issues.option_count, 0)

    async def test_nothing_on_says_so(self) -> None:
        async with self.app.run_test(size=(148, 41)) as pilot:
            await self._ready(pilot)
            await pilot.press("C")
            await pilot.pause(0.2)
            self.assertEqual(self.toasts[-1], "no filters on")

    def test_default_keybinding(self) -> None:
        self.assertTrue(any(
            b.key == "C" and b.action == "clear_filters"
            for b in ltui.build_bindings({})
        ))


if __name__ == "__main__":
    unittest.main()
