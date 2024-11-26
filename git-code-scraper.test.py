import unittest
from git_code_scraper import GitCodeScraper

class TestGitCodeScraper(unittest.TestCase):
    def setUp(self):
        self.scraper = GitCodeScraper("/path/to/repo")

if __name__ == '__main__':
    unittest.main()
