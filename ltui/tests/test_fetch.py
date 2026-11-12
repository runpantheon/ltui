import asyncio
import unittest
from pathlib import Path
import sys
from unittest import mock

sys.path.insert(0, str(Path(__file__).parents[1]))
sys.path.insert(0, str(Path(__file__).parents[1] / "tools"))

import ltui  # noqa: E402

STATES = [{"id": "s1", "name": "Todo", "type": "unstarted", "position": 0}]


def issues(prefix: str, n: int) -> list[dict]:
    return [{"id": f"{prefix}{k}"} for k in range(n)]


class FakeLinear:
    """Answers the two board queries: open issues in pages, closed in one go."""

    def __init__(self, open_pages: list[list[dict]], closed: list[dict]) -> None:
        self.open_pages = open_pages
        self.closed = closed
        self.calls: list[tuple[str, dict]] = []

    async def gql(self, query: str, variables: dict) -> dict:
        self.calls.append((query, dict(variables)))
        if query is ltui.QL_CLOSED_ISSUES:
            return {"team": {"issues": {"nodes": self.closed}}}
        assert query is ltui.QL_OPEN_ISSUES
        n = int(variables.get("after") or 0)
        last = n == len(self.open_pages) - 1
        return {"team": {
            "issues": {
                "nodes": self.open_pages[n],
                "pageInfo": {"hasNextPage": not last,
                             "endCursor": None if last else str(n + 1)},
            },
            "states": {"nodes": STATES},
        }}

    def open_calls(self) -> list[dict]:
        return [v for q, v in self.calls if q is ltui.QL_OPEN_ISSUES]


def fetch(fake: FakeLinear):
    return asyncio.run(ltui.fetch_team_issues(fake.gql, "team-1"))


class FetchTeamIssuesTest(unittest.TestCase):
    def test_pages_through_every_open_issue_and_adds_closed(self) -> None:
        fake = FakeLinear([issues("a", 250), issues("b", 250), issues("c", 46)],
                          issues("x", 50))
        got, states, truncated = fetch(fake)
        self.assertEqual(len(got), 546 + 50)
        self.assertEqual(states, STATES)
        self.assertFalse(truncated)
        self.assertEqual([v.get("after") for v in fake.open_calls()], [None, "1", "2"])

    def test_closed_issue_seen_twice_is_kept_once(self) -> None:
        moved = {"id": "a0", "state": "closed now"}
        fake = FakeLinear([issues("a", 3)], [moved, *issues("x", 2)])
        got, _, _ = fetch(fake)
        self.assertEqual(len(got), 5)
        self.assertIn(moved, got)

    def test_stops_at_the_open_issue_limit(self) -> None:
        pages = [issues(f"p{n}-", 250) for n in range(12)]
        with mock.patch.object(ltui, "MAX_OPEN_ISSUES", 1000):
            got, _, truncated = fetch(FakeLinear(pages, []))
        self.assertTrue(truncated)
        self.assertEqual(len(got), 1000)

    def test_missing_team_raises(self) -> None:
        async def gql(query, variables):
            return {"team": None}

        with self.assertRaises(RuntimeError):
            asyncio.run(ltui.fetch_team_issues(gql, "gone"))

    def test_queries_split_on_closed_types(self) -> None:
        self.assertIn("nin:", ltui.QL_OPEN_ISSUES)
        self.assertIn('"duplicate"', ltui.QL_OPEN_ISSUES)
        self.assertIn("in:", ltui.QL_CLOSED_ISSUES)
        self.assertNotIn("nin:", ltui.QL_CLOSED_ISSUES)


class DemoBoardLoadTest(unittest.IsolatedAsyncioTestCase):
    """The demo board still loads every ticket through the split fetch."""

    async def test_demo_board_loads_open_and_closed(self) -> None:
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
        app = screenshots.DemoApp()
        async with app.run_test(size=(148, 41)) as pilot:
            for _ in range(40):
                await pilot.pause(0.1)
                if app.query_one("#issues").option_count:
                    break
            expected = {i["id"] for i in screenshots.TEAM_ISSUES["t-core"]}
            self.assertEqual({i["id"] for i in app._issues}, expected)
            types = {i["state"]["type"] for i in app._issues}
            self.assertIn("completed", types)
            self.assertIn("started", types)


if __name__ == "__main__":
    unittest.main()
