#!/usr/bin/env python
"""
Entry point for the Git Code Scraper CLI.
"""

import argparse
from typing import Optional, Set

from git_code_scraper import GitCodeScraper


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
    Scrape a repository and format its contents for LLM processing.

    Args:
        repo_path (str): Local path or URL to the repository.
        output_file (Optional[str]): File path to save the formatted output.
        ignored_dirs (Optional[Set[str]]): Additional directories to ignore.
        ignored_files (Optional[Set[str]]): Specific files to ignore.
        ignore_file (Optional[str]): Path to configuration file with ignore rules.
        token (Optional[str]): GitHub token (if repo_path is a URL).
        branch (str): Branch to scrape (default is "main").

    Returns:
        str: Formatted repository contents.
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
            scraper.logger.error(f"Error saving output: {e}")

    return formatted_output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scrape code from a Git repository for LLM analysis"
    )
    parser.add_argument("repo_path", help="Path to the Git repository or its URL")
    parser.add_argument("--output", "-o", help="Path to save the formatted output")
    parser.add_argument(
        "--ignore-dirs", "-id", nargs="+", help="Additional directories to ignore"
    )
    parser.add_argument(
        "--ignore-files", "-if", nargs="+", help="Specific files to ignore"
    )
    parser.add_argument(
        "--ignore-file", "-c", help="Path to configuration file with ignore rules"
    )
    parser.add_argument(
        "--token", "-t", help="GitHub token for private repositories (if URL provided)"
    )
    parser.add_argument(
        "--branch", "-b", default="main", help="Branch to scrape (default: main)"
    )

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
