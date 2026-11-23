import unittest
from pathlib import Path
import sys
from unittest import mock

sys.path.insert(0, str(Path(__file__).parents[1]))
sys.path.insert(0, str(Path(__file__).parents[1] / "tools"))

import ltui  # noqa: E402


def issue(state_id: str, name: str) -> dict:
    return {"state": {"id": state_id, "name": name}}


class HideStateTest(unittest.TestCase):
    def test_matches_by_name_across_teams(self) -> None:
        hidden = {"duplicate"}
        # same status name, different team-scoped ids
        self.assertTrue(ltui.hide_state(issue("st-a", "Duplicate"), hidden))
        self.assertTrue(ltui.hide_state(issue("st-b", "duplicate"), hidden))
        self.assertFalse(ltui.hide_state(issue("st-c", "Done"), hidden))

    def test_missing_state_is_never_hidden(self) -> None:
        self.assertFalse(ltui.hide_state({}, {"duplicate"}))

    def test_default_keybindings(self) -> None:
        pairs = {(b.key, b.action) for b in ltui.build_bindings({})}
        self.assertIn(("h", "toggle_hidden"), pairs)
        self.assertIn(("H", "pick_hidden_states"), pairs)


class HiddenStatesAppTest(unittest.IsolatedAsyncioTestCase):
    """Drive the demo board from tools/screenshots.py (no network)."""

    async def asyncSetUp(self) -> None:
        import screenshots

        self.saved: dict = {}
        state = {"theme": "mocha", "team_id": "t-core", "welcomed": True,
                 "hidden_states": ["Done"]}
        for name, fn in {
            "load_api_key": lambda: "demo",
            "read_cache": lambda name: None,
            "write_cache": lambda name, data: None,
            "load_state": lambda: dict(state),
            "save_state": self.saved.update,
        }.items():
            patcher = mock.patch.object(ltui, name, fn)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.app = screenshots.DemoApp()

    def statuses(self) -> set[str]:
        return {i["state"]["name"] for i in self.shown()}

    def shown(self) -> list[dict]:
        ol = self.app.query_one("#issues")
        by_id = self.app._issue_by_id
        return [
            by_id[o.id]
            for o in (ol.get_option_at_index(n) for n in range(ol.option_count))
            if o.id in by_id
        ]

    async def test_hide_toggle_and_pick(self) -> None:
        async with self.app.run_test(size=(148, 41)) as pilot:
            for _ in range(40):
                await pilot.pause(0.1)
                if self.app.query_one("#issues").option_count:
                    break
            sub = lambda: str(self.app.query_one("#centre").border_subtitle)

            # saved choice applies on start
            self.assertNotIn("Done", self.statuses())
            self.assertIn("hidden", sub())

            # h shows them again without forgetting the choice
            await pilot.press("h")
            self.assertIn("Done", self.statuses())
            self.assertIn("showing hidden", sub())
            self.assertEqual(self.saved["hidden_states"], ["done"])
            self.assertFalse(self.saved["hide_states"])

            # H: add Backlog, apply — hiding switches back on
            await pilot.press("H")
            await pilot.pause(0.2)
            ol = self.app.screen.query_one("#labels-list")
            ids = [ol.get_option_at_index(n).id for n in range(ol.option_count)]
            ol.highlighted = ids.index("backlog")
            await pilot.press("enter")
            await pilot.press("ctrl+s")
            await pilot.pause(0.2)
            self.assertEqual(set(self.saved["hidden_states"]), {"done", "backlog"})
            self.assertTrue(self.saved["hide_states"])
            self.assertFalse({"Done", "Backlog"} & self.statuses())
            self.assertIn("In Progress", self.statuses())


    async def test_pick_from_settings_saves(self) -> None:
        # the picker opened from settings must outlive settings closing
        async with self.app.run_test(size=(148, 41)) as pilot:
            for _ in range(40):
                await pilot.pause(0.1)
                if self.app.query_one("#issues").option_count:
                    break
            await pilot.press("comma")
            await pilot.pause(0.3)
            ol = self.app.screen.query_one("#settings-list")
            ids = [ol.get_option_at_index(n).id for n in range(ol.option_count)]
            ol.highlighted = ids.index("pref:hide-pick")
            await pilot.press("enter")
            await pilot.pause(0.3)
            lo = self.app.screen.query_one("#labels-list")
            ids = [lo.get_option_at_index(n).id for n in range(lo.option_count)]
            lo.highlighted = ids.index("backlog")
            await pilot.press("enter")
            await pilot.click("#labels-apply")
            await pilot.pause(0.3)
            self.assertEqual(set(self.saved["hidden_states"]), {"done", "backlog"})
            self.assertNotIn("Backlog", self.statuses())

if __name__ == "__main__":
    unittest.main()
