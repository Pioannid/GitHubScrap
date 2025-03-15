Below is the updated README with the new –xt option, along with all the other available CLI options:

⸻

GitHub Scrap

A tool to scrape code from Git repositories for LLM or other analysis. This tool reads the repository, filters files based on extension and ignore rules, and outputs a formatted version of the code. For example, if your repository contains a file named hello.py with a simple function, running the tool might produce:

### File: hello.py
def greet():
    print("Hello, world!")

Installation

You can install the package using PyPI:

pip install github-scrap

Or, if you use Poetry:

poetry add github-scrap

Or directly from GitHub:

pip install git+https://github.com/Pioannid/GitHubScrap.git

Usage

Python Script

You can use the tool as a module in your Python scripts:

from github_scrap import GitHubCodeScraper

repo_url = "https://github.com/Pioannid/GitHubScrapper"
scraper = GitHubCodeScraper(repo_path=repo_url, branch="main")
code_contents = scraper.scrape_repository()
formatted_output = scraper.format_for_llm(code_contents)
print(formatted_output)

CLI

After installation, the CLI tool is available as github-scrap. The basic usage is:

github-scrap [OPTIONS] REPO_PATH

Where REPO_PATH is the path to the Git repository or its URL.

Available CLI Options
	•	–output, -o
Description: Specify a file path to save the formatted output.
Example:
--output output.txt
	•	–ignore-dirs, -id
Description: Additional directories to ignore. Accepts one or more directory names.
Example:
--ignore-dirs venv node_modules
	•	–ignore-files, -if
Description: Specific files to ignore. Accepts one or more filenames.
Example:
--ignore-files README.md LICENSE
	•	–ignore-file, -c
Description: Path to a configuration file with ignore rules (for both files and directories).
Example:
--ignore-file .gitignore
	•	–token, -t
Description: GitHub token for private repositories (if REPO_PATH is a URL).
Example:
--token YOUR_GITHUB_TOKEN
	•	–branch, -b
Description: The branch to scrape from. Default is main.
Example:
--branch develop
	•	–xt
Description: Modify file extensions to process. This option accepts an operation and one or more file extensions.
	•	Operation: Specify add to include additional extensions or remove to exclude extensions from the default set.
	•	Usage Examples:
	•	To add extensions:

github-scrap REPO_PATH --xt add .js .txt


	•	To remove extensions:

github-scrap REPO_PATH --xt remove .cpp .hpp



Example Command

To scrape the repository on the main branch, save the output to output.txt, and add .json and .md to the default file extensions, run:

github-scrap https://github.com/Pioannid/GitHubScrap --branch main --output output.txt --xt add .json .md

License

This project is licensed under the MIT License.

⸻

Feel free to adjust the wording or examples as needed. This README now reflects the updated CLI option for modifying file extensions.