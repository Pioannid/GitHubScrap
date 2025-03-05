import unittest
from src.app.git_code_scraper import GitCodeScraper


class TestGitCodeScraper(unittest.TestCase):
    def setUp(self) -> None:
        self.scraper = GitCodeScraper("")

    def test_connect_to_repo(self) -> None:
        """
        Test that connecting to a local repository returns a boolean.
        """
        result = self.scraper.connect_to_repo()
        self.assertIsInstance(result, bool)


if __name__ == "__main__":
    unittest.main()
