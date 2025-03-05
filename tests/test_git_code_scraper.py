import unittest
from github_scrapper.app.git_code_scraper import GitCodeScraper

class TestGitCodeScraper(unittest.TestCase):
    def setUp(self) -> None:
        self.scraper = GitCodeScraper("path/to/local/repo")

    def test_connect_to_repo(self) -> None:
        result = self.scraper.connect_to_repo()
        self.assertIsInstance(result, bool)

if __name__ == "__main__":
    unittest.main()
