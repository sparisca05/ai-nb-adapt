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
]