import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parents[1]))
sys.path.insert(0, str(Path(__file__).parents[1] / "tools"))

import ltui  # noqa: E402


class PickerFilterTest(unittest.IsolatedAsyncioTestCase):
    """Drive the demo board's `V` project picker (no network)."""

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

    async def _open_picker(self, pilot) -> None:
        for _ in range(40):
            await pilot.pause(0.1)
            if self.app.query_one("#issues").option_count:
                break
        await pilot.press("V")
        await pilot.pause(0.3)
        self.assertIsInstance(self.app.screen, ltui.PickerModal)

    def _list(self):
        return self.app.screen.query_one("#picker-list", ltui.NavList)

    def _ids(self) -> list[str]:
        ol = self._list()
        return [ol.get_option_at_index(i).id for i in range(ol.option_count)]

    def _highlighted_id(self) -> str:
        ol = self._list()
        return ol.get_option_at_index(ol.highlighted).id

    async def test_slash_filters_and_keeps_pinned_rows(self) -> None:
        async with self.app.run_test(size=(148, 41)) as pilot:
            await self._open_picker(pilot)
            everything = self._ids()
            self.assertIn("proj:p-sync", everything)
            self.assertIn("proj:p-polish", everything)

            await pilot.press("slash")
            await pilot.pause(0.1)
            self.assertIsInstance(self.app.focused, ltui.PickerSearch)
            await pilot.press(*"sync")
            await pilot.pause(0.2)
            ids = self._ids()
            self.assertIn("all:", ids)
            self.assertIn("proj:p-sync", ids)
            self.assertNotIn("proj:p-polish", ids)
            if "proj:" in everything:  # the no-project row stays too
                self.assertIn("proj:", ids)
            # enter takes the first real match, not the pinned row above it
            self.assertEqual(self._highlighted_id(), "proj:p-sync")
            await pilot.press("enter")
            await pilot.pause(0.3)
            self.assertNotIsInstance(self.app.screen, ltui.PickerModal)
            self.assertEqual(self.app._project_filter, "p-sync")

    async def test_counts_are_not_matched(self) -> None:
        async with self.app.run_test(size=(148, 41)) as pilot:
            await self._open_picker(pilot)
            await pilot.press("slash", "3")
            await pilot.pause(0.2)
            # "Sync Engine v2" and "Infra Hardening" have 3 tickets each, so
            # "3" is in their labels; only "Q3 Polish" has it in its name.
            self.assertEqual(
                [i for i in self._ids() if i not in ("all:", "proj:")],
                ["proj:p-polish"],
            )

    async def test_ctrl_n_p_and_arrows_move_while_typing(self) -> None:
        async with self.app.run_test(size=(148, 41)) as pilot:
            await self._open_picker(pilot)
            ol = self._list()
            start = ol.highlighted
            await pilot.press("ctrl+n")
            self.assertEqual(ol.highlighted, start + 1)
            await pilot.press("ctrl+p")
            self.assertEqual(ol.highlighted, start)
            # still the picker, not the command palette
            self.assertIsInstance(self.app.screen, ltui.PickerModal)

            await pilot.press("slash")
            await pilot.pause(0.1)
            await pilot.press("down")
            self.assertEqual(ol.highlighted, start + 1)
            await pilot.press("ctrl+p")
            self.assertEqual(ol.highlighted, start)
            self.assertIsInstance(self.app.focused, ltui.PickerSearch)

    async def test_move_picker_keeps_new_and_none(self) -> None:
        async with self.app.run_test(size=(148, 41)) as pilot:
            for _ in range(40):
                await pilot.pause(0.1)
                if self.app.query_one("#issues").option_count:
                    break
            await pilot.press("P")
            await pilot.pause(0.5)
            self.assertIsInstance(self.app.screen, ltui.PickerModal)
            await pilot.press("slash", *"zzz")
            await pilot.pause(0.2)
            self.assertEqual(sorted(self._ids()), ["new:", "none:"])

    async def test_escape_clears_filter_then_closes(self) -> None:
        async with self.app.run_test(size=(148, 41)) as pilot:
            await self._open_picker(pilot)
            everything = self._ids()
            await pilot.press("slash", *"polish")
            await pilot.pause(0.2)
            self.assertLess(len(self._ids()), len(everything))

            await pilot.press("escape")
            await pilot.pause(0.2)
            self.assertIsInstance(self.app.screen, ltui.PickerModal)
            self.assertEqual(self._ids(), everything)
            self.assertIsInstance(self.app.focused, ltui.NavList)

            await pilot.press("escape")
            await pilot.pause(0.2)
            self.assertNotIsInstance(self.app.screen, ltui.PickerModal)
            self.assertIsNone(self.app._project_filter)


if __name__ == "__main__":
    unittest.main()
