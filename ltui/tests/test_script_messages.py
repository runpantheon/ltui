import time
import unittest
from pathlib import Path
import sys
from unittest import mock

sys.path.insert(0, str(Path(__file__).parents[1]))
sys.path.insert(0, str(Path(__file__).parents[1] / "tools"))

import ltui  # noqa: E402


class ScriptErrorTextTest(unittest.TestCase):
    def test_strips_colour_and_keeps_the_tail(self) -> None:
        raw = (b"noise one\n\n noise two\n"
               b"\x1b[31mticket: session SuperIT-sup-1 already exists.\x1b[39m\n"
               b"line four\nline five\n")
        self.assertEqual(
            ltui.script_output_text(raw),
            "ticket: session SuperIT-sup-1 already exists.\nline four\nline five",
        )

    def test_empty_and_blank_stderr(self) -> None:
        self.assertEqual(ltui.script_output_text(b""), "")
        self.assertEqual(ltui.script_output_text(b"\n  \n"), "")

    def test_undecodable_bytes_do_not_raise(self) -> None:
        self.assertIn("bad", ltui.script_output_text(b"bad \xff byte"))


class LoadScriptsMessageTest(unittest.TestCase):
    def test_message_is_normalised(self) -> None:
        scripts, warnings = ltui.load_scripts({"scripts": [
            {"path": "/bin/a", "message": "  Researching {{issue.identifier}}. "},
            {"path": "/bin/b"},
        ]})
        self.assertEqual(warnings, [])
        self.assertEqual(scripts[0]["message"], "Researching {{issue.identifier}}.")
        self.assertEqual(scripts[1]["message"], "")

    def test_done_message_is_normalised(self) -> None:
        scripts, warnings = ltui.load_scripts({"scripts": [
            {"path": "/bin/a", "done_message": " {{stdout}} "},
            {"path": "/bin/b", "done_message": 3},
        ]})
        self.assertEqual(scripts[0]["done_message"], "{{stdout}}")
        self.assertEqual(scripts[1]["done_message"], "")
        self.assertEqual(len(warnings), 1)

    def test_non_string_message_warns_and_is_ignored(self) -> None:
        scripts, warnings = ltui.load_scripts({"scripts": [
            {"path": "/bin/a", "message": ["nope"]},
        ]})
        self.assertEqual(scripts[0]["message"], "")
        self.assertEqual(len(warnings), 1)


class ScriptToastTest(unittest.IsolatedAsyncioTestCase):
    """Run real scripts against the demo board (tools/screenshots.py)."""

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

    def use_script(self, shell: str, **extra) -> None:
        scripts, _ = ltui.load_scripts({"scripts": [
            {"name": "Start ticket", "path": "/bin/sh", "args": ["-c", shell], **extra},
        ]})
        patcher = mock.patch.object(ltui, "SCRIPTS", scripts)
        patcher.start()
        self.addCleanup(patcher.stop)

    def toasts(self) -> list[tuple[str, str, str]]:
        return [(n.severity, n.title, n.message) for n in self.app._notifications]

    async def run_script(self, pilot, settle: float = 1.5) -> str:
        for _ in range(40):
            await pilot.pause(0.1)
            if self.app.query_one("#issues").option_count:
                break
        issue = self.app._current_issue()
        self.app.action_run_custom_script(0)
        deadline = time.monotonic() + settle
        while time.monotonic() < deadline:
            await pilot.pause(0.1)
            if any(sev == "error" for sev, _, _ in self.toasts()):
                break
        return issue["identifier"]

    async def test_custom_message_then_error_from_stderr(self) -> None:
        self.use_script(
            "echo 'not shown' ; printf '\\033[31mCould not create worktree, already exists.\\033[39m\\n' >&2; exit 1",
            message="Researching {{issue.identifier}}.",
        )
        async with self.app.run_test(size=(148, 41)) as pilot:
            ident = await self.run_script(pilot)
            self.assertEqual(self.toasts(), [
                ("information", "", f"Researching {ident}."),
                ("error", "Start ticket failed",
                 "Could not create worktree, already exists."),
            ])

    async def test_success_shows_only_the_launch_toast(self) -> None:
        self.use_script("echo fine >&2; exit 0", message="Researching {{issue.identifier}}.")
        async with self.app.run_test(size=(148, 41)) as pilot:
            ident = await self.run_script(pilot, settle=1.0)
            self.assertEqual(self.toasts(), [("information", "", f"Researching {ident}.")])

    async def test_failure_without_stderr_names_the_exit_code(self) -> None:
        self.use_script("exit 3")
        async with self.app.run_test(size=(148, 41)) as pilot:
            await self.run_script(pilot)
            self.assertIn(("error", "Start ticket failed", "exited with code 3"), self.toasts())

    async def test_background_child_holding_stderr_does_not_delay_the_error(self) -> None:
        # a pipe would stay open while `sleep` lives; a temp file doesn't care
        self.use_script("sleep 10 & echo boom >&2; exit 1")
        async with self.app.run_test(size=(148, 41)) as pilot:
            await self.run_script(pilot, settle=3.0)
            self.assertIn(("error", "Start ticket failed", "boom"), self.toasts())

    async def test_markup_in_output_is_shown_literally(self) -> None:
        self.use_script("echo '[bold]oops[/]' >&2; exit 1", message="[red]{{issue.identifier}}")
        async with self.app.run_test(size=(148, 41)) as pilot:
            ident = await self.run_script(pilot)
            self.assertEqual(self.toasts()[0][2], f"[red]{ident}")
            self.assertIn(("error", "Start ticket failed", "[bold]oops[/]"), self.toasts())


    async def test_done_message_shows_stdout_on_success(self) -> None:
        self.use_script(
            "echo 'Naming the worktree...'; echo 'Creating sup-1-x - 3/20 spots used.';"
            " printf '\\033[32mTicket started in tmux session SuperIT-sup-1.\\033[0m\\n'",
            message="Researching {{issue.identifier}}.",
            done_message="{{issue.identifier}}: {{stdout}}",
        )
        async with self.app.run_test(size=(148, 41)) as pilot:
            ident = await self.run_script(pilot, settle=1.5)
            for _ in range(15):
                if len(self.toasts()) > 1:
                    break
                await pilot.pause(0.1)
            self.assertEqual(self.toasts(), [
                ("information", "", f"Researching {ident}."),
                ("information", "",
                 f"{ident}: Naming the worktree...\nCreating sup-1-x - 3/20 spots used.\n"
                 "Ticket started in tmux session SuperIT-sup-1."),
            ])

    async def test_done_message_is_not_shown_on_failure(self) -> None:
        self.use_script("echo partial; echo broke >&2; exit 1", done_message="{{stdout}}")
        async with self.app.run_test(size=(148, 41)) as pilot:
            await self.run_script(pilot)
            severities = [sev for sev, _, _ in self.toasts()]
            self.assertEqual(severities, ["information", "error"])
            self.assertEqual(self.toasts()[1][2], "broke")

    async def test_empty_done_message_falls_back(self) -> None:
        self.use_script("exit 0", done_message="{{stdout}}")
        async with self.app.run_test(size=(148, 41)) as pilot:
            await self.run_script(pilot, settle=1.0)
            for _ in range(15):
                if len(self.toasts()) > 1:
                    break
                await pilot.pause(0.1)
            self.assertIn(("information", "", "Start ticket finished"), self.toasts())


if __name__ == "__main__":
    unittest.main()
