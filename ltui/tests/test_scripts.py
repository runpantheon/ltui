import unittest
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).parents[1]))

import ltui  # noqa: E402


def script_bindings(bindings):
    return {b.key: b for b in bindings if b.action.startswith("run_custom_script(")}


class LoadScriptsTest(unittest.TestCase):
    def test_normalises_entries(self) -> None:
        scripts, warnings = ltui.load_scripts({"scripts": [
            {"key": "X", "name": " Claude ", "description": "go", "path": "~/bin/a"},
            {"key": ["ctrl+x", "Z"], "path": "/opt/tools/draft-pr"},
            {"path": "/bin/b"},
        ]})
        self.assertEqual(warnings, [])
        self.assertEqual(
            [(s["keys"], s["name"], s["description"]) for s in scripts],
            [
                (["X"], "Claude", "go"),
                (["ctrl+x", "Z"], "draft-pr", ""),  # name defaults to file name
                ([], "b", ""),                       # no key: palette only
            ],
        )
        self.assertEqual(scripts[0]["path"], "~/bin/a")

    def test_skips_entries_without_path(self) -> None:
        scripts, warnings = ltui.load_scripts({"scripts": [
            {"key": "X"}, "nonsense", {"path": "  "}, {"path": "/bin/ok"},
        ]})
        self.assertEqual([s["name"] for s in scripts], ["ok"])
        self.assertEqual(len(warnings), 3)
        self.assertIn("scripts[0]", warnings[0])

    def test_invalid_key_keeps_script_in_palette(self) -> None:
        scripts, warnings = ltui.load_scripts({"scripts": [{"key": 5, "path": "/bin/a"}]})
        self.assertEqual(scripts[0]["keys"], [])
        self.assertEqual(len(warnings), 1)

    def test_missing_or_bad_section(self) -> None:
        self.assertEqual(ltui.load_scripts({}), ([], []))
        scripts, warnings = ltui.load_scripts({"scripts": {"X": {"path": "/bin/a"}}})
        self.assertEqual(scripts, [])
        self.assertEqual(len(warnings), 1)


class ScriptBindingsTest(unittest.TestCase):
    def test_script_keys_are_bound_to_their_index(self) -> None:
        scripts, _ = ltui.load_scripts({"scripts": [
            {"key": "X", "name": "first", "path": "/bin/a"},
            {"key": ["ctrl+x", "Z"], "path": "/bin/b"},
        ]})
        bound = script_bindings(ltui.build_bindings({}, scripts))
        self.assertEqual(bound["X"].action, "run_custom_script(0)")
        self.assertEqual(bound["X"].description, "first")
        self.assertEqual(bound["ctrl+x"].action, "run_custom_script(1)")
        self.assertEqual(bound["Z"].action, "run_custom_script(1)")

    def test_builtin_and_reserved_keys_win(self) -> None:
        scripts, _ = ltui.load_scripts({"scripts": [
            {"key": ["s", "j", "X"], "name": "a", "path": "/bin/a"},
            {"key": "X", "name": "b", "path": "/bin/b"},
        ]})
        keymap = ltui.merged_keybinds({})
        pairs, warnings = ltui.bind_scripts(scripts, keymap)
        self.assertEqual(pairs, [("X", 0)])
        self.assertEqual(len(warnings), 3)
        bound = script_bindings(ltui.build_bindings({}, scripts))
        self.assertEqual(set(bound), {"X"})

    def test_remapping_a_builtin_frees_its_key(self) -> None:
        scripts, _ = ltui.load_scripts({"scripts": [{"key": "s", "path": "/bin/a"}]})
        bound = script_bindings(ltui.build_bindings({"change_status": "S"}, scripts))
        self.assertEqual(bound["s"].action, "run_custom_script(0)")


class HelpSectionsTest(unittest.TestCase):
    def rows(self, keymap, scripts=()):
        return dict(ltui.help_sections(keymap, list(scripts)))

    def test_defaults_render_like_before(self) -> None:
        rows = self.rows(ltui.merged_keybinds({}))
        self.assertIn(("s", "change status"), rows["ticket"])
        self.assertIn(("[ / ]", "previous / next group"), rows["navigate"])
        self.assertIn(("/", "filter issues"), rows["view"])
        self.assertIn(("?", "this help"), rows["app"])
        self.assertNotIn("scripts", rows)

    def test_remapped_keys_show_as_remapped(self) -> None:
        rows = self.rows(ltui.merged_keybinds({
            "change_status": "S", "yank": ["y", "ctrl+y"], "filter": "f",
        }))
        self.assertIn(("S", "change status"), rows["ticket"])
        self.assertIn(("y/ctrl+y", "yank — copy branch / url / identifier"), rows["ticket"])
        self.assertIn(("f", "filter issues"), rows["view"])

    def test_scripts_section(self) -> None:
        scripts, _ = ltui.load_scripts({"scripts": [
            {"key": "X", "name": "Claude", "description": "start Claude", "path": "/bin/a"},
            {"key": ["s", "ctrl+w"], "name": "Worktree", "path": "/bin/b"},
            {"name": "Draft PR", "path": "/bin/c"},
        ]})
        rows = self.rows(ltui.merged_keybinds({}), scripts)
        self.assertEqual(rows["scripts"], [
            ("X", "start Claude"),
            ("ctrl+w", "Worktree"),   # s was taken, so only ctrl+w is listed
            ("palette", "Draft PR"),
        ])


if __name__ == "__main__":
    unittest.main()
