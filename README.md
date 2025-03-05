Below is an example of a README that includes a list of available CLI options for your package:

# GitHub Scrapper

A tool to scrape code from Git repositories for LLM analysis.

## Installation

You can install the package using PyPI 

```bash
pip install github-scrapper
```

or directly from GitHub:

```bash
pip install git+https://github.com/Pioannid/GitHubScrapper.git
```

Or, if you use Poetry, add the dependency in your pyproject.toml:

`
[tool.poetry.dependencies]
github-scrapper = { git = "https://github.com/Pioannid/GitHubScrapper.git" }
`

Then run:

`poetry install`

## Usage

### Python Script

```python
from github_scrapper import GitHubCodeScraper

repo_url = "https://github.com/Pioannid/GitHubScrapper"
scraper = GitHubCodeScraper(repo_path=repo_url, branch="main")
code_contents = scraper.scrape_repository()
formatted_output = scraper.format_for_llm(code_contents)
print(formatted_output)
```

### CLI

After installation, the CLI tool is available as github-scrapper. The basic usage is:

`github-scrapper [OPTIONS] REPO_PATH`

Where REPO_PATH is the path to the Git repository or its URL.

–output, -o:
Description: Specify a file path to save the formatted output.
Example:

--output output.txt


–ignore-dirs, -id:
Description: Additional directories to ignore. Accepts one or more directory names.
Example:

--ignore-dirs venv node_modules


–ignore-files, -if:
Description: Specific files to ignore. Accepts one or more filenames.
Example:

--ignore-files README.md LICENSE


–ignore-file, -c:

Description: Path to a configuration file with ignore rules (for both files and directories).
Example:

--ignore-file .gitignore


–token, -t:
Description: GitHub token for private repositories (if REPO_PATH is a URL).
Example:

--token YOUR_GITHUB_TOKEN


–branch, -b:
Description: The branch to scrape from. Default is main.
Example:

--branch develop



Example Command

To scrape the repository on the main branch and save the output to output.txt:

github-scrapper https://github.com/Pioannid/GitHubScrapper --branch main --output output.txt

If you run github-scrapper without any arguments, the tool will display the help message listing all these options.

License

This project is licensed under the MIT License.

---

Feel free to modify the wording or examples to best match your project. This README provides clear instructions on how to install, use, and customize the tool via its available CLI options.