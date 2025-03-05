"""
Module: git_code_scraper
Creation Date: 2025-03-05
Author: Your Name
Summary:
    This module provides a GitCodeScraper class capable of scraping code from a Git repository.
    It supports both local repositories (using GitPython and os.walk) and remote repositories (via the GitHub API).
    Additional options include ignored directories/files, branch selection (default: main), and authentication token for private repos.
"""

import logging
import os
import base64
from pathlib import Path
from typing import Dict, Set, Optional
from urllib.parse import urlparse

import git
import requests


class GitCodeScraper:
    def __init__(
        self,
        repo_path: str,
        ignored_dirs: Optional[Set[str]] = None,
        file_extensions: Optional[Set[str]] = None,
        ignore_file: Optional[str] = None,
        token: Optional[str] = None,
        branch: str = "main",
    ):
        """
        Initialize the GitCodeScraper with repository path and optional filters.

        Args:
            repo_path (str): Path to the Git repository or a URL (e.g., https://github.com/username/repo)
            ignored_dirs (Set[str], optional): Directories to ignore (e.g., {'node_modules', 'venv'})
            file_extensions (Set[str], optional): File extensions to include (e.g., {'.py', '.js'})
            ignore_file (str, optional): Path to file containing ignored files and directories
            token (str, optional): GitHub token for private repositories (only applicable if repo_path is a URL)
            branch (str): Branch to scrape for remote repositories (default is "main")
        """
        self.repo_path = repo_path
        self.default_ignored_dirs = {'venv', 'node_modules', '.git', '__pycache__'}
        self.ignored_dirs = ignored_dirs or self.default_ignored_dirs.copy()
        self.file_extensions = file_extensions or {'.py', '.js', '.java', '.cpp', '.ts', '.jsx', '.tsx'}
        self.ignored_files: Set[str] = set()
        self.repo = None
        self.token = token
        self.branch = branch
        self.logger = self._setup_logger()

        # Determine if repo_path is a URL (remote repository) or local path.
        if repo_path.startswith("http://") or repo_path.startswith("https://"):
            self.is_remote = True
            parsed = urlparse(repo_path)
            path_parts = parsed.path.strip("/").split("/")
            if len(path_parts) < 2:
                raise ValueError("Invalid repository URL. Expected format: 'https://github.com/owner/repo'")
            self.remote_owner, self.remote_repo = path_parts[0], path_parts[1]
        else:
            self.is_remote = False

        if ignore_file:
            self._load_ignore_file(ignore_file)

    def _load_ignore_file(self, ignore_file_path: str) -> None:
        """
        Load ignored files and directories from a configuration file.

        The file should have the following format:
        [files]
        file1.txt
        file2.py

        [directories]
        dir1
        dir2/subdir

        Args:
            ignore_file_path (str): Path to the ignore configuration file
        """
        try:
            with open(ignore_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            section = None
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):  # Skip empty lines and comments
                    continue

                if line == '[files]':
                    section = 'files'
                elif line == '[directories]':
                    section = 'directories'
                elif section == 'files':
                    self.ignored_files.add(line)
                elif section == 'directories':
                    self.ignored_dirs.add(line)

            self.logger.info(f"Loaded ignore configuration from {ignore_file_path}")
            self.logger.debug(f"Ignored files: {self.ignored_files}")
            self.logger.debug(f"Ignored directories: {self.ignored_dirs}")

        except FileNotFoundError:
            self.logger.warning(f"Ignore file not found: {ignore_file_path}")
        except Exception as e:
            self.logger.error(f"Error loading ignore file: {str(e)}")

    def _setup_logger(self) -> logging.Logger:
        """Set up logging configuration."""
        logger = logging.getLogger('GitCodeScraper')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def connect_to_repo(self) -> bool:
        """Connect to the local Git repository."""
        try:
            self.repo = git.Repo(self.repo_path)
            return True
        except git.exc.InvalidGitRepositoryError:
            self.logger.error(f"Invalid Git repository at {self.repo_path}")
            return False
        except Exception as e:
            self.logger.error(f"Error connecting to repository: {str(e)}")
            return False

    def _should_process_file(self, file_path: str) -> bool:
        """
        Check if a file should be processed based on its path and extension.

        For local repositories, the check is performed relative to the repository root.
        For remote repositories, the file_path is assumed to be relative to the repo root.

        Args:
            file_path (str): Path to the file (or relative file path for remote repos)

        Returns:
            bool: True if the file should be processed, False otherwise
        """
        path = Path(file_path)

        if self.is_remote:
            # For remote files, check each part of the relative path against ignored directories.
            for part in path.parts:
                if part in self.ignored_dirs:
                    return False
        else:
            # For local files, traverse up to the repository root.
            current_path = path
            while current_path != Path(self.repo_path):
                if current_path.name in self.ignored_dirs:
                    return False
                current_path = current_path.parent

        if path.name in self.ignored_files:
            return False

        return path.suffix in self.file_extensions

    def get_file_content(self, file_path: str) -> str:
        """
        Read and return the content of a file from a local repository.

        Args:
            file_path (str): Path to the file

        Returns:
            str: Content of the file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {str(e)}")
            return ""

    def scrape_remote_repository(self) -> Dict[str, str]:
        """
        Scrape all relevant files from a remote GitHub repository using the GitHub API.

        Returns:
            Dict[str, str]: Dictionary mapping file paths to their content
        """
        code_contents = {}
        api_url = f"https://api.github.com/repos/{self.remote_owner}/{self.remote_repo}/git/trees/{self.branch}?recursive=1"
        headers = {}
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        self.logger.info(f"Fetching remote repository tree from {api_url}")
        response = requests.get(api_url, headers=headers)
        if response.status_code != 200:
            self.logger.error(f"Failed to fetch repository tree: HTTP {response.status_code}")
            return {}

        data = response.json()
        tree = data.get('tree', [])

        for item in tree:
            if item.get('type') == 'blob':  # Process file blobs only
                file_path = item.get('path')
                if self._should_process_file(file_path):
                    file_api_url = item.get('url')
                    file_resp = requests.get(file_api_url, headers=headers)
                    if file_resp.status_code == 200:
                        file_data = file_resp.json()
                        content = file_data.get('content', '')
                        encoding = file_data.get('encoding', '')
                        if encoding == 'base64':
                            try:
                                decoded_bytes = base64.b64decode(content)
                                file_content = decoded_bytes.decode('utf-8', errors='replace')
                            except Exception as e:
                                self.logger.error(f"Error decoding file {file_path}: {e}")
                                continue
                        else:
                            file_content = content
                        code_contents[file_path] = file_content
                    else:
                        self.logger.warning(f"Failed to fetch file {file_path}: HTTP {file_resp.status_code}")
        return code_contents

    def scrape_repository(self) -> Dict[str, str]:
        """
        Scrape all relevant files from the repository (local or remote).

        Returns:
            Dict[str, str]: Dictionary mapping file paths to their content
        """
        if self.is_remote:
            return self.scrape_remote_repository()
        else:
            if not self.repo:
                if not self.connect_to_repo():
                    return {}
            code_contents = {}
            for root, _, files in os.walk(self.repo_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if self._should_process_file(file_path):
                        relative_path = os.path.relpath(file_path, self.repo_path)
                        content = self.get_file_content(file_path)
                        if content:
                            code_contents[relative_path] = content
            return code_contents

    def format_for_llm(self, code_contents: Dict[str, str]) -> str:
        """
        Format the code contents for LLM input.

        Args:
            code_contents (Dict[str, str]): Dictionary mapping file paths to their content

        Returns:
            str: Formatted string containing all code content
        """
        formatted_content = []
        for file_path, content in code_contents.items():
            formatted_content.extend([
                f"\n### File: {file_path}",
                "```" + Path(file_path).suffix[1:],  # infers language from file extension
                content,
                "```\n"
            ])
        return "\n".join(formatted_content)


def main(
    repo_path: str,
    output_file: Optional[str] = None,
    ignored_dirs: Optional[Set[str]] = None,
    ignored_files: Optional[Set[str]] = None,
    ignore_file: Optional[str] = None,
    token: Optional[str] = None,
    branch: str = "main",
) -> str:
    """
    Main function to scrape a repository and format its contents.

    Args:
        repo_path (str): Path or URL to the Git repository
        output_file (str, optional): Path to save the formatted output
        ignored_dirs (Set[str], optional): Additional directories to ignore
        ignored_files (Set[str], optional): Specific files to ignore
        ignore_file (str, optional): Path to configuration file with ignored files and directories
        token (str, optional): GitHub token for private repositories (only if repo_path is a URL)
        branch (str): Branch to scrape for remote repositories (default "main")

    Returns:
        str: Formatted repository contents
    """
    scraper = GitCodeScraper(
        repo_path,
        ignored_dirs=ignored_dirs,
        file_extensions={'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.hpp', '.h'},
        ignore_file=ignore_file,
        token=token,
        branch=branch,
    )

    if ignored_files:
        scraper.ignored_files.update(ignored_files)

    code_contents = scraper.scrape_repository()
    formatted_output = scraper.format_for_llm(code_contents)

    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(formatted_output)
            scraper.logger.info(f"Output saved to {output_file}")
        except Exception as e:
            scraper.logger.error(f"Error saving output: {str(e)}")

    return formatted_output


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Scrape code from a Git repository for LLM analysis')
    parser.add_argument('repo_path', help='Path to the Git repository or its URL')
    parser.add_argument('--output', '-o', help='Path to save the formatted output')
    parser.add_argument('--ignore-dirs', '-id', nargs='+', help='Additional directories to ignore')
    parser.add_argument('--ignore-files', '-if', nargs='+', help='Specific files to ignore')
    parser.add_argument('--ignore-file', '-c', help='Path to configuration file with ignored files and directories')
    parser.add_argument('--token', '-t', help='GitHub token for private repositories (only for URL input)')
    parser.add_argument('--branch', '-b', default='main', help='Branch to scrape for remote repositories (default: main)')

    args = parser.parse_args()
    main(
        repo_path=args.repo_path,
        output_file=args.output,
        ignored_dirs=set(args.ignore_dirs) if args.ignore_dirs else None,
        ignored_files=set(args.ignore_files) if args.ignore_files else None,
        ignore_file=args.ignore_file,
        token=args.token,
        branch=args.branch,
    )