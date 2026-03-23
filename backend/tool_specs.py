tools = [
    {
        "type": "function",
        "function": {
            "name": "get_repo_info",
            "description": "Fetch general metadata about a GitHub repository: language, license, stars, last activity, open issues, topics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string", "description": "Repository owner (user or organization)"},
                    "repo": {"type": "string", "description": "Repository name"}
                },
                "required": ["owner", "repo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_file_tree",
            "description": "Fetch the full file and directory structure of a repository. Returns structural signals like presence of tests, CI config, Docker, README, and dependency files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string", "description": "Repository owner"},
                    "repo": {"type": "string", "description": "Repository name"},
                    "max_files": {"type": "integer", "description": "Max number of paths to return (default: 100)", "default": 100}
                },
                "required": ["owner", "repo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_file_content",
            "description": "Read the content of a specific file in the repository. Use this to inspect README, configuration files, or source code.",
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string", "description": "Repository owner"},
                    "repo": {"type": "string", "description": "Repository name"},
                    "path": {"type": "string", "description": "File path relative to repo root (e.g. 'README.md', 'src/app.py')"}
                },
                "required": ["owner", "repo", "path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_dependencies",
            "description": "Extract the list of dependencies from the project's dependency file (requirements.txt, package.json, pyproject.toml). Detects ecosystem automatically.",
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string", "description": "Repository owner"},
                    "repo": {"type": "string", "description": "Repository name"}
                },
                "required": ["owner", "repo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_vulnerabilities",
            "description": "Check the repository's dependencies against the OSV (Open Source Vulnerabilities) database to find known CVEs. Returns vulnerable packages with severity and fix versions. Calls get_dependencies internally, so no need to call it separately.",
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string", "description": "Repository owner"},
                    "repo": {"type": "string", "description": "Repository name"}
                },
                "required": ["owner", "repo"]
            }
        }
    }
]