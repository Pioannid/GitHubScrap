#!/usr/bin/env python
"""
Entry point for the GitHub Scrapper CLI.
Author: Panagiotis Ioannidis
"""

import argparse
import sys
import os
import getpass
import requests
from urllib.parse import urlparse
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
                        help=("Path to file containing GitHub token for private repositories. "
                              "Defaults to environment variable GITHUB_TOKEN if not provided."))
    parser.add_argument("--branch", "-b", default="main",
                        help="Branch to scrape (default: main)")

    if len(sys.argv) == 1 or not sys.argv[1]:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()
    if not args.repo_path:
        parser.print_help()
        sys.exit(1)

    if args.token:
        try:
            with open(args.token, 'r', encoding='utf-8') as token_file:
                token = token_file.read().strip()
        except Exception as e:
            token = None
    else:
        token = os.getenv("GITHUB_TOKEN")

    if not token and args.repo_path.startswith("http"):
        parsed_url = urlparse(args.repo_path)
        path_parts = parsed_url.path.strip("/").split("/")
        if len(path_parts) >= 2:
            owner, repo = path_parts[0], path_parts[1]
            api_url = f"https://api.github.com/repos/{owner}/{repo}"
            response = requests.get(api_url)
            if response.status_code != 200:
                token = getpass.getpass("Enter your GitHub token: ")

    result = main(
        repo_path=args.repo_path,
        output_file=args.output,
        ignored_dirs=set(args.ignore_dirs) if args.ignore_dirs else None,
        ignored_files=set(args.ignore_files) if args.ignore_files else None,
        ignore_file=args.ignore_file,
        token=token,
        branch=args.branch,
    )
    print(result)


if __name__ == "__main__":
    cli()