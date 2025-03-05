#!/usr/bin/env python
"""
Entry point for the GitHub Scrapper CLI.
Author: Panagiotis Ioannidis
"""

import argparse
import sys
from typing import Optional, Set

from github_scrap.app.git_code_scrap import GitHubCodeScraper


def main(
        repo_path: str,
        output_file: Optional[str] = None,
        ignored_dirs: Optional[Set[str]] = None,
        ignored_files: Optional[Set[str]] = None,
        ignore_file: Optional[str] = None,
        token: Optional[str] = None,
        branch: str = "main",
) -> str:
    scraper = GitHubCodeScraper(
        repo_path,
        ignored_dirs=ignored_dirs,
        file_extensions={'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.hpp',
                         '.h'},
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


def cli() -> None:
    """
    Command-line interface that parses arguments and calls the main function.
    If no arguments are provided, prints the help message.
    """
    parser = argparse.ArgumentParser(
        description="Scrape code from a Git repository for LLM analysis"
    )
    # Make repo_path optional so we can check it manually
    parser.add_argument("repo_path", nargs="?",
                        help="Path to the Git repository or its URL")
    parser.add_argument("--output", "-o", help="Path to save the formatted output")
    parser.add_argument("--ignore-dirs", "-id", nargs="+",
                        help="Additional directories to ignore")
    parser.add_argument("--ignore-files", "-if", nargs="+",
                        help="Specific files to ignore")
    parser.add_argument("--ignore-file", "-c",
                        help="Path to configuration file with ignore rules")
    parser.add_argument("--token", "-t",
                        help="GitHub token for private repositories (if URL provided)")
    parser.add_argument("--branch", "-b", default="main",
                        help="Branch to scrape (default: main)")

    if len(sys.argv) == 1 or not sys.argv[1]:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()
    if not args.repo_path:
        parser.print_help()
        sys.exit(1)

    result = main(
        repo_path=args.repo_path,
        output_file=args.output,
        ignored_dirs=set(args.ignore_dirs) if args.ignore_dirs else None,
        ignored_files=set(args.ignore_files) if args.ignore_files else None,
        ignore_file=args.ignore_file,
        token=args.token,
        branch=args.branch,
    )
    print(result)


if __name__ == "__main__":
    cli()
