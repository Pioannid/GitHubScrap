"""
Module: git_code_scraper
Creation Date: 2025-03-05
Author: Your Name
Summary:
    Provides the GitCodeScraper class for scraping code from a Git repository.
    Supports both local and remote repositories with configurable filtering options.
"""

import os
import base64
from pathlib import Path
from typing import Dict, Set, Optional
from urllib.parse import urlparse

import git
import requests

from config.logging_config import configure_logging


class GitCodeScraper:
    def __init__(
        self,
        repo_path: str,
        ignored_dirs: Optional[Set[str]] = None,
        file_extensions: Optional[Set[str]] = None,
        ignore_file: Optional[str] = None,
        token: Optional[str] = None,
        branch: str = "main",
    ) -> None:
        """
        Initialize the GitCodeScraper with repository path and optional filters.

        Args:
            repo_path (str): Local path or URL to the Git repository.
            ignored_dirs (Optional[Set[str]]): Directories to ignore.
            file_extensions (Optional[Set[str]]): File extensions to include.
            ignore_file (Optional[str]): Path to a configuration file for ignored files/directories.
            token (Optional[str]): GitHub token for private repositories.
            branch (str): Branch to scrape for remote repositories.
        """
        self.repo_path: str = repo_path
        self.default_ignored_dirs: Set[str] = {'venv', 'node_modules', '.git', '__pycache__'}
        self.ignored_dirs: Set[str] = ignored_dirs or self.default_ignored_dirs.copy()
        self.file_extensions: Set[str] = file_extensions or {'.py', '.js', '.java', '.cpp', '.ts', '.jsx', '.tsx'}
        self.ignored_files: Set[str] = set()
        self.repo = None
        self.token: Optional[str] = token
        self.branch: str = branch
        self.logger = configure_logging(__name__)

        # Determine if repo_path is a remote URL or a local path.
        if repo_path.startswith("http://") or repo_path.startswith("https://"):
            self.is_remote: bool = True
            parsed = urlparse(repo_path)
            path_parts = parsed.path.strip("/").split("/")
            if len(path_parts) < 2:
                raise ValueError(
                    "Invalid repository URL. Expected format: 'https://github.com/owner/repo'"
                )
            self.remote_owner: str = path_parts[0]
            self.remote_repo: str = path_parts[1]
        else:
            self.is_remote = False

        if ignore_file:
            self._load_ignore_file(ignore_file)

    def _load_ignore_file(self, ignore_file_path: str) -> None:
        """
        Load ignored files and directories from a configuration file.

        File format example:
            [files]
            file1.txt
            file2.py

            [directories]
            dir1
            dir2/subdir

        Args:
            ignore_file_path (str): Path to the ignore configuration file.
        """
        try:
            with open(ignore_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            section = None
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
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
            self.logger.error(f"Error loading ignore file: {e}")

    def connect_to_repo(self) -> bool:
        """
        Connect to the local Git repository.

        Returns:
            bool: True if the connection was successful, False otherwise.
        """
        try:
            self.repo = git.Repo(self.repo_path)
            return True
        except git.exc.InvalidGitRepositoryError:
            self.logger.error(f"Invalid Git repository at {self.repo_path}")
            return False
        except Exception as e:
            self.logger.error(f"Error connecting to repository: {e}")
            return False

    def _should_process_file(self, file_path: str) -> bool:
        """
        Check if a file should be processed based on its path and extension.

        Args:
            file_path (str): File path (or relative file path for remote repositories).

        Returns:
            bool: True if the file should be processed; False otherwise.
        """
        path = Path(file_path)

        if self.is_remote:
            for part in path.parts:
                if part in self.ignored_dirs:
                    return False
        else:
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
            file_path (str): Path to the file.

        Returns:
            str: Content of the file.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
            return ""

    def scrape_remote_repository(self) -> Dict[str, str]:
        """
        Scrape relevant files from a remote GitHub repository using the GitHub API.

        Returns:
            Dict[str, str]: Mapping of file paths to their content.
        """
        code_contents: Dict[str, str] = {}
        api_url = (
            f"https://api.github.com/repos/{self.remote_owner}/"
            f"{self.remote_repo}/git/trees/{self.branch}?recursive=1"
        )
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
            if item.get('type') == 'blob':
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
            Dict[str, str]: Mapping of file paths to their content.
        """
        if self.is_remote:
            return self.scrape_remote_repository()
        else:
            if not self.repo and not self.connect_to_repo():
                return {}
            code_contents: Dict[str, str] = {}
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
            code_contents (Dict[str, str]): Mapping of file paths to content.

        Returns:
            str: Formatted string containing all code content.
        """
        formatted_content = []
        for file_path, content in code_contents.items():
            formatted_content.extend([
                f"\n### File: {file_path}",
                f"```{Path(file_path).suffix[1:]}",
                content,
                "```"
            ])
        return "\n".join(formatted_content)
