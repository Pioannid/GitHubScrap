import git
import os
from pathlib import Path
import logging
from typing import List, Dict, Set

class GitCodeScraper:
    def __init__(self, repo_path: str, ignored_dirs: Set[str] = None, file_extensions: Set[str] = None):
        """
        Initialize the GitCodeScraper with repository path and optional filters.
        
        Args:
            repo_path (str): Path to the Git repository
            ignored_dirs (Set[str]): Directories to ignore (e.g., {'node_modules', 'venv'})
            file_extensions (Set[str]): File extensions to include (e.g., {'.py', '.js'})
        """
        self.repo_path = repo_path
        self.ignored_dirs = ignored_dirs or {'venv', 'node_modules', '.git', '__pycache__'}
        self.file_extensions = file_extensions or {'.py', '.js', '.java', '.cpp', '.ts', '.jsx', '.tsx'}
        self.repo = None
        self.logger = self._setup_logger()

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
        
        # Check if file is in ignored directory
        for ignored_dir in self.ignored_dirs:
            if ignored_dir in path.parts:
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

def main(repo_path: str, output_file: str = None) -> str:
    """
    Main function to scrape a repository and format its contents.
    
    Args:
        repo_path (str): Path to the Git repository
        output_file (str, optional): Path to save the formatted output
    
    Returns:
        str: Formatted repository contents
    """
    # Initialize scraper
    scraper = GitCodeScraper(
        repo_path,
        ignored_dirs={'venv', 'node_modules', '.git', '__pycache__', 'dist', 'build'},
        file_extensions={'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.hpp', '.h'}
    )
    
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
    
    parser = argparse.ArgumentParser(description='Scrape code from a Git repository for LLM analysis')
    parser.add_argument('repo_path', help='Path to the Git repository')
    parser.add_argument('--output', '-o', help='Path to save the formatted output')
    
    args = parser.parse_args()
    main(args.repo_path, args.output)
