import os
import sys
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parents[1]))
sys.path.insert(0, str(Path(__file__).parents[1] / "tools"))

import ltui  # noqa: E402
from textual.widgets import TextArea  # noqa: E402


class EditorHelpersTest(unittest.TestCase):
    def test_visual_wins_over_editor_and_splits_args(self) -> None:
        env = {"VISUAL": "code --wait", "EDITOR": "vim"}
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(ltui.preferred_editor(), ["code", "--wait"])

    def test_falls_back_to_editor_then_none(self) -> None:
        with mock.patch.dict(os.environ, {"VISUAL": " ", "EDITOR": "nvim"}, clear=True):
            self.assertEqual(ltui.preferred_editor(), ["nvim"])
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(ltui.preferred_editor())

    def test_edit_in_editor_round_trips_and_cleans_up(self) -> None:
        seen = {}

        def fake_run(cmd):
            path = Path(cmd[-1])
            seen["path"], seen["before"] = path, path.read_text()
            path.write_text("new body\n")
            return mock.Mock(returncode=0)

        with mock.patch.object(ltui.subprocess, "run", fake_run):
            self.assertEqual(ltui.edit_in_editor(["ed"], "old body\n"), "new body\n")
        self.assertEqual(seen["before"], "old body\n")
        self.assertEqual(seen["path"].suffix, ".md")
        self.assertFalse(seen["path"].exists())

    def test_nonzero_exit_is_a_cancel(self) -> None:
        with mock.patch.object(
            ltui.subprocess, "run", lambda cmd: mock.Mock(returncode=1)
        ):
            self.assertIsNone(ltui.edit_in_editor(["vim"], "x"))

    def test_default_keybinding(self) -> None:
        self.assertTrue(any(
            b.key == "e" and b.action == "edit_description"
            for b in ltui.build_bindings({})
        ))


class EditDescriptionAppTest(unittest.IsolatedAsyncioTestCase):
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
        self.calls = []
        real_gql = self.app.gql

        async def gql(query, variables=None):
            if "description: $description" in query:
                self.calls.append(variables)
            return await real_gql(query, variables)

        self.app.gql = gql

    async def _ready(self, pilot) -> dict:
        for _ in range(40):
            await pilot.pause(0.1)
            if self.app.query_one("#issues").option_count:
                break
        issue = self.app._current_issue()
        self.assertIsNotNone(issue)
        return issue

    async def test_in_app_box_when_no_editor(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            async with self.app.run_test(size=(148, 41)) as pilot:
                issue = await self._ready(pilot)
                await pilot.press("e")
                await pilot.pause(0.3)
                area = self.app.screen.query_one("#comment-input", TextArea)
                self.assertEqual(area.text, (issue.get("description") or "").strip())
                area.text = "rewritten in the box"
                await pilot.press("ctrl+s")
                await pilot.pause(0.3)
                self.assertEqual(
                    self.calls,
                    [{"id": issue["id"], "description": "rewritten in the box"}],
                )
                self.assertEqual(issue["description"], "rewritten in the box")

    async def test_escape_in_box_saves_nothing(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            async with self.app.run_test(size=(148, 41)) as pilot:
                await self._ready(pilot)
                await pilot.press("e")
                await pilot.pause(0.3)
                await pilot.press("escape")
                await pilot.pause(0.3)
                self.assertEqual(self.calls, [])

    async def test_external_editor(self) -> None:
        @contextmanager
        def fake_suspend():
            yield

        edits = []

        def fake_edit(cmd, text, suffix=".md"):
            edits.append((cmd, text))
            return "from the editor\n"

        with mock.patch.dict(os.environ, {"EDITOR": "nvim"}, clear=True), \
                mock.patch.object(ltui, "edit_in_editor", fake_edit):
            async with self.app.run_test(size=(148, 41)) as pilot:
                issue = await self._ready(pilot)
                self.app.suspend = fake_suspend
                await pilot.press("e")
                await pilot.pause(0.3)
                self.assertEqual(edits[0][0], ["nvim"])
                self.assertEqual(
                    self.calls, [{"id": issue["id"], "description": "from the editor"}]
                )
                self.assertEqual(issue["description"], "from the editor")

    async def test_unchanged_text_is_not_sent(self) -> None:
        @contextmanager
        def fake_suspend():
            yield

        with mock.patch.dict(os.environ, {"EDITOR": "nvim"}, clear=True), \
                mock.patch.object(ltui, "edit_in_editor", lambda c, t, suffix=".md": t):
            async with self.app.run_test(size=(148, 41)) as pilot:
                await self._ready(pilot)
                self.app.suspend = fake_suspend
                await pilot.press("e")
                await pilot.pause(0.3)
                self.assertEqual(self.calls, [])


if __name__ == "__main__":
    unittest.main()
