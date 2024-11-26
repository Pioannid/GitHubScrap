import logging
import os
from pathlib import Path
from typing import Dict, Set

import git


class GitCodeScraper:
    def __init__(self, repo_path: str, ignored_dirs: Set[str] = None,
                 file_extensions: Set[str] = None, ignore_file: str = None):
        """
        Initialize the GitCodeScraper with repository path and optional filters.

        Args:
            repo_path (str): Path to the Git repository
            ignored_dirs (Set[str]): Directories to ignore (e.g., {'node_modules', 'venv'})
            file_extensions (Set[str]): File extensions to include (e.g., {'.py', '.js'})
            ignore_file (str): Path to file containing ignored files and directories
        """
        self.repo_path = repo_path
        self.default_ignored_dirs = {'venv', 'node_modules', '.git', '__pycache__'}
        self.ignored_dirs = ignored_dirs or self.default_ignored_dirs.copy()
        self.file_extensions = file_extensions or {'.py', '.js', '.java', '.cpp', '.ts',
                                                   '.jsx', '.tsx'}
        self.ignored_files: Set[str] = set()
        self.repo = None
        self.logger = self._setup_logger()

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
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def connect_to_repo(self) -> bool:
        """Connect to the Git repository."""
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

        Args:
            file_path (str): Path to the file

        Returns:
            bool: True if the file should be processed, False otherwise
        """
        path = Path(file_path)

        # Check if the file or any of its parent directories should be ignored
        current_path = path
        while current_path != Path(self.repo_path):
            if current_path.name in self.ignored_dirs:
                return False
            current_path = current_path.parent

        # Check if file is in ignored files
        if path.name in self.ignored_files:
            return False

        # Check file extension
        return path.suffix in self.file_extensions

    def get_file_content(self, file_path: str) -> str:
        """
        Read and return the content of a file.

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

    def scrape_repository(self) -> Dict[str, str]:
        """
        Scrape all relevant files from the repository.

        Returns:
            Dict[str, str]: Dictionary mapping file paths to their content
        """
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
                "```" + Path(file_path).suffix[1:],  # Get language from extension
                content,
                "```\n"
            ])

        return "\n".join(formatted_content)


def main(repo_path: str, output_file: str = None, ignored_dirs: Set[str] = None,
         ignored_files: Set[str] = None, ignore_file: str = None) -> str:
    """
    Main function to scrape a repository and format its contents.

    Args:
        repo_path (str): Path to the Git repository
        output_file (str, optional): Path to save the formatted output
        ignored_dirs (Set[str], optional): Additional directories to ignore
        ignored_files (Set[str], optional): Specific files to ignore
        ignore_file (str, optional): Path to file containing ignored files and directories

    Returns:
        str: Formatted repository contents
    """
    # Initialize scraper
    scraper = GitCodeScraper(
        repo_path,
        ignored_dirs=ignored_dirs,
        file_extensions={'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.hpp',
                         '.h'},
        ignore_file=ignore_file
    )

    # Add ignored files to the scraper
    if ignored_files:
        scraper.ignored_files.update(ignored_files)

    # Scrape repository
    code_contents = scraper.scrape_repository()

    # Format contents
    formatted_output = scraper.format_for_llm(code_contents)

    # Save to file if specified
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

    parser = argparse.ArgumentParser(
        description='Scrape code from a Git repository for LLM analysis')
    parser.add_argument('repo_path', help='Path to the Git repository')
    parser.add_argument('--output', '-o', help='Path to save the formatted output')
    parser.add_argument('--ignore-dirs', '-id', nargs='+',
                        help='Additional directories to ignore')
    parser.add_argument('--ignore-files', '-if', nargs='+',
                        help='Specific files to ignore')
    parser.add_argument('--ignore-file', '-c',
                        help='Path to configuration file with ignored files and directories')

    args = parser.parse_args()
    main(
        args.repo_path,
        args.output,
        ignored_dirs=set(args.ignore_dirs) if args.ignore_dirs else None,
        ignored_files=set(args.ignore_files) if args.ignore_files else None,
        ignore_file=args.ignore_file
    )