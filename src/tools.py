import json
import os
from dotenv import load_dotenv
import requests

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_API = "https://api.github.com"
OSV_API = "https://api.osv.dev/v1"

GITHUB_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}

def get_repo_info(owner: str, repo: str) -> str:
    """
    Fetch general metadata about a GitHub repository.

    Args:
        owner: Repository owner (user or organization)
        repo: Repository name

    Returns:
        JSON string with repo metadata
    """
    url = f"{GITHUB_API}/repos/{owner}/{repo}"
    response = requests.get(url, headers=GITHUB_HEADERS)
    response.raise_for_status()
    data = response.json()

    return json.dumps({
        "name": data["full_name"],
        "description": data.get("description"),
        "language": data.get("language"),
        "languages_url": data.get("languages_url"),
        "license": data["license"]["name"] if data.get("license") else None,
        "stars": data["stargazers_count"],
        "forks": data["forks_count"],
        "open_issues": data["open_issues_count"],
        "default_branch": data["default_branch"],
        "created_at": data["created_at"][:10],
        "last_push": data["pushed_at"][:10],
        "size_kb": data["size"],
        "has_wiki": data["has_wiki"],
        "has_issues": data["has_issues"],
        "topics": data.get("topics", [])
    }, indent=2)


def get_file_tree(owner: str, repo: str, max_files: int = 100) -> str:
    """
    Fetch the full file/directory tree of a repository.

    Args:
        owner: Repository owner
        repo: Repository name
        max_files: Maximum number of file paths to return (default: 100)

    Returns:
        JSON string with file tree and structural analysis
    """
    url = f"{GITHUB_API}/repos/{owner}/{repo}/git/trees/HEAD"
    response = requests.get(url, headers=GITHUB_HEADERS, params={"recursive": "1"})
    response.raise_for_status()
    data = response.json()

    all_paths = [item["path"] for item in data.get("tree", [])]
    truncated = data.get("truncated", False)

    # Structural signals useful for the agent to reason about
    has_tests = any(
        p.startswith(("test", "tests", "__tests__", "spec", "specs"))
        or "/test" in p or "_test." in p or ".test." in p or ".spec." in p
        for p in all_paths
    )
    has_ci = any(
        p.startswith(".github/workflows") or p in (".travis.yml", "Jenkinsfile", ".circleci/config.yml")
        for p in all_paths
    )
    has_docker = any(p in ("Dockerfile", "docker-compose.yml", "docker-compose.yaml") for p in all_paths)
    has_readme = any(p.lower().startswith("readme") for p in all_paths)
    has_contributing = any("contributing" in p.lower() for p in all_paths)
    has_env_example = any(".env.example" in p or ".env.sample" in p for p in all_paths)
    has_gitignore = ".gitignore" in all_paths

    dependency_files = [
        p for p in all_paths
        if p in (
            "requirements.txt", "requirements-dev.txt", "Pipfile", "pyproject.toml",
            "package.json", "package-lock.json", "yarn.lock",
            "pom.xml", "build.gradle", "Gemfile"
        )
    ]

    return json.dumps({
        "total_files": len(all_paths),
        "truncated": truncated,
        "paths": all_paths[:max_files],
        "signals": {
            "has_tests": has_tests,
            "has_ci": has_ci,
            "has_docker": has_docker,
            "has_readme": has_readme,
            "has_contributing_guide": has_contributing,
            "has_env_example": has_env_example,
            "has_gitignore": has_gitignore,
            "dependency_files_found": dependency_files
        }
    }, indent=2)