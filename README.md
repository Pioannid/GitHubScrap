Below is an example of a README that includes a list of available CLI options for your package:

# GitHub Scrap

A tool to scrape code from Git repositories for LLM or other analysis. Below is an example output. This example assumes that your repository contains a file named hello.py with a simple function.
When you run the tool, you might see output similar to:

```python
### File: hello.py
def greet():
    print("Hello, world!")

```

## Installation

You can install the package using PyPI

```bash
pip install github-scrap
```

Or, if you use Poetry:

```bash
poetry add github-scrap
```

or directly from GitHub:

```bash
pip install git+https://github.com/Pioannid/GitHubScrap.git
```

## Usage

### Python Script

```python
from github_scrap import GitHubCodeScraper

repo_url = "https://github.com/Pioannid/GitHubScrapper"
scraper = GitHubCodeScraper(repo_path=repo_url, branch="main")
code_contents = scraper.scrape_repository()
formatted_output = scraper.format_for_llm(code_contents)
print(formatted_output)
```

### CLI

After installation, the CLI tool is available as github-scrap. The basic usage is:

`github-scrap [OPTIONS] REPO_PATH`

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

### Example Command

To scrape the repository on the main branch and save the output to output.txt:

github-scrap https://github.com/Pioannid/GitHubScrap --branch main --output output.txt

License

This project is licensed under the MIT License.

---

Feel free to modify the wording or examples to best match your project. This README provides clear instructions on how to install, use, and customize the tool via its available CLI options.