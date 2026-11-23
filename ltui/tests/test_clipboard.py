import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parents[1]))
sys.path.insert(0, str(Path(__file__).parents[1] / "tools"))

import ltui  # noqa: E402


def which_only(*present):
    return lambda name: f"/usr/bin/{name}" if name in present else None


class NativeCopyCommandTest(unittest.TestCase):
    def test_macos_uses_pbcopy(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True), \
                mock.patch.object(ltui.sys, "platform", "darwin"), \
                mock.patch.object(ltui.shutil, "which", which_only("pbcopy")):
            self.assertEqual(ltui.native_copy_command(), ["pbcopy"])

    def test_skipped_over_ssh(self) -> None:
        with mock.patch.dict(os.environ, {"SSH_CONNECTION": "1 2 3 4"}, clear=True), \
                mock.patch.object(ltui.sys, "platform", "darwin"), \
                mock.patch.object(ltui.shutil, "which", which_only("pbcopy")):
            self.assertIsNone(ltui.native_copy_command())

    def test_linux_prefers_wayland_then_x11(self) -> None:
        env = {"WAYLAND_DISPLAY": "wayland-0", "DISPLAY": ":0"}
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch.object(ltui.sys, "platform", "linux"):
            with mock.patch.object(ltui.shutil, "which", which_only("wl-copy", "xclip")):
                self.assertEqual(ltui.native_copy_command(), ["wl-copy"])
            with mock.patch.object(ltui.shutil, "which", which_only("xsel")):
                self.assertEqual(
                    ltui.native_copy_command(), ["xsel", "--clipboard", "--input"]
                )

    def test_none_without_a_display_or_tool(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True), \
                mock.patch.object(ltui.sys, "platform", "linux"), \
                mock.patch.object(ltui.shutil, "which", which_only("xclip")):
            self.assertIsNone(ltui.native_copy_command())


class CopyNativelyTest(unittest.TestCase):
    def test_pipes_text_to_the_tool(self) -> None:
        run = mock.Mock(return_value=mock.Mock(returncode=0))
        with mock.patch.object(ltui, "native_copy_command", lambda: ["pbcopy"]), \
                mock.patch.object(ltui.subprocess, "run", run):
            self.assertTrue(ltui.copy_natively("CORE-128"))
        self.assertEqual(run.call_args.args[0], ["pbcopy"])
        self.assertEqual(run.call_args.kwargs["input"], b"CORE-128")

    def test_failures_are_quiet(self) -> None:
        with mock.patch.object(ltui, "native_copy_command", lambda: ["pbcopy"]):
            for err in (OSError("gone"), subprocess.TimeoutExpired("pbcopy", 2)):
                with mock.patch.object(ltui.subprocess, "run", side_effect=err):
                    self.assertFalse(ltui.copy_natively("x"))
        with mock.patch.object(ltui, "native_copy_command", lambda: None):
            self.assertFalse(ltui.copy_natively("x"))


class YankTest(unittest.IsolatedAsyncioTestCase):
    """y → identifier on the demo board reaches both OSC 52 and the tool."""

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

    async def test_yank_identifier(self) -> None:
        natively = mock.Mock(return_value=True)
        with mock.patch.object(ltui, "copy_natively", natively):
            async with self.app.run_test(size=(148, 41)) as pilot:
                for _ in range(40):
                    await pilot.pause(0.1)
                    if self.app.query_one("#issues").option_count:
                        break
                issue = self.app._current_issue()
                await pilot.press("y")
                await pilot.pause(0.3)
                await pilot.press("down", "down", "enter")
                await pilot.pause(0.3)
                natively.assert_called_once_with(issue["identifier"])
                self.assertEqual(self.app.clipboard, issue["identifier"])


if __name__ == "__main__":
    unittest.main()
