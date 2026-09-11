import os
import unittest

from env_checker import (
    compare_env_files,
    find_typos,
    is_healthy,
    parse_env_file,
    scan_portfolio,
    scan_project,
)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
GOOD_PROJECT = os.path.join(FIXTURES_DIR, "good_project")
BROKEN_PROJECT = os.path.join(FIXTURES_DIR, "broken_project")


class TestParseEnvFile(unittest.TestCase):
    def test_parses_key_value_pairs(self):
        variables = parse_env_file(os.path.join(GOOD_PROJECT, ".env"))
        self.assertEqual(variables["DEBUG"], "true")
        self.assertEqual(variables["DATABASE_URL"], "sqlite:///app.db")

    def test_missing_file_returns_empty_dict(self):
        self.assertEqual(parse_env_file("/nonexistent/path/.env"), {})


class TestFindTypos(unittest.TestCase):
    def test_detects_near_miss_key_names(self):
        typos = find_typos({"SECRET_KEY"}, {"SECRETKEY", "OLD_UNUSED_VAR"})
        self.assertEqual(typos, [("SECRET_KEY", "SECRETKEY")])

    def test_does_not_pair_up_unrelated_keys(self):
        typos = find_typos({"DATABASE_URL"}, {"OLD_UNUSED_VAR"})
        self.assertEqual(typos, [])


class TestCompareEnvFiles(unittest.TestCase):
    def test_healthy_project_reports_no_problems(self):
        report = compare_env_files(
            os.path.join(GOOD_PROJECT, ".env.example"),
            os.path.join(GOOD_PROJECT, ".env"),
        )
        self.assertTrue(is_healthy(report))

    def test_broken_project_flags_missing_extra_typo_and_empty(self):
        # This is the project's Definition of Done: correctly flag every
        # kind of problem in a deliberately broken .env fixture.
        report = compare_env_files(
            os.path.join(BROKEN_PROJECT, ".env.example"),
            os.path.join(BROKEN_PROJECT, ".env"),
        )
        self.assertFalse(is_healthy(report))
        self.assertEqual(report["missing"], ["DATABASE_URL"])
        self.assertEqual(report["extra"], ["OLD_UNUSED_VAR"])
        self.assertEqual(report["typos"], [("SECRET_KEY", "SECRETKEY")])
        self.assertEqual(report["empty"], ["DEBUG_MODE"])


class TestScanProject(unittest.TestCase):
    def test_scan_project_without_env_example_returns_none(self):
        with_no_example = os.path.join(FIXTURES_DIR)  # fixtures/ itself has no .env.example
        self.assertIsNone(scan_project(with_no_example))

    def test_scan_project_on_good_project(self):
        report = scan_project(GOOD_PROJECT)
        self.assertIsNotNone(report)
        self.assertTrue(is_healthy(report))


class TestScanPortfolio(unittest.TestCase):
    def test_scan_portfolio_finds_both_fixture_projects(self):
        results = scan_portfolio(FIXTURES_DIR)
        self.assertEqual(set(results.keys()), {"good_project", "broken_project"})
        self.assertTrue(is_healthy(results["good_project"]))
        self.assertFalse(is_healthy(results["broken_project"]))


if __name__ == "__main__":
    unittest.main()
