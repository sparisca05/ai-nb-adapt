import base64
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


def get_file_content(owner: str, repo: str, path: str) -> str:
    """
    Fetch the content of a specific file in the repository.

    Args:
        owner: Repository owner
        repo: Repository name
        path: File path relative to repo root (e.g. 'README.md', 'src/main.py')

    Returns:
        File content as plain text (truncated to 8000 chars if large)
    """
    url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
    response = requests.get(url, headers=GITHUB_HEADERS)

    if response.status_code == 404:
        return f"File not found: {path}"

    response.raise_for_status()
    data = response.json()

    if data.get("encoding") == "base64":
        content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
    else:
        content = data.get("content", "")

    if len(content) > 8000:
        content = content[:8000] + f"\n\n[... truncated — full file is {len(content)} chars]"

    return content


def get_dependencies(owner: str, repo: str) -> str:
    """
    Extract project dependencies by reading dependency files found in the repository tree.
    Supports Python (requirements.txt, requirements-dev.txt, pyproject.toml),
    Node.js (package.json), and Java (pom.xml).

    Args:
        owner: Repository owner
        repo: Repository name

    Returns:
        JSON string with detected ecosystems and list of dependencies with versions
    """
    file_tree = json.loads(get_file_tree(owner, repo))
    dependency_files = file_tree.get("signals", {}).get("dependency_files_found", [])
    ecosystems = {}

    for filepath in dependency_files:
        content = get_file_content(owner, repo, filepath)
        if content.startswith("File not found"):
            continue

        if "requirements.txt" in filepath or "requirements-dev.txt" in filepath:
            ecosystems.setdefault("python", {"source_file": filepath, "dependencies": []})
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("-"):
                    # Normalize: 'requests==2.28.0' or 'requests>=2.0'
                    for sep in ("==", ">=", "<=", "~=", "!=", ">", "<", "["):
                        if sep in line:
                            name, version = line.split(sep, 1)[0].strip(), line.split(sep, 1)[1].strip().split(";")[0]
                            ecosystems["python"]["dependencies"].append({"name": name, "version": version.split(",")[0]})
                            break
                    else:
                        ecosystems["python"]["dependencies"].append({"name": line, "version": None})

        elif "package.json" in filepath:
            ecosystems.setdefault("npm", {"source_file": filepath, "dependencies": []})
            try:
                pkg = json.loads(content)
                for name, version in {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}.items():
                    ecosystems["npm"]["dependencies"].append({"name": name, "version": version.lstrip("^~><=!")})
            except json.JSONDecodeError:
                return f"Could not parse {filepath}"

        elif "pyproject.toml" in filepath:
            ecosystems.setdefault("python", {"source_file": filepath, "dependencies": []})
            # Basic extraction — looks for lines under [tool.poetry.dependencies] or [project]
            in_deps = False
            for line in content.splitlines():
                if "[tool.poetry.dependencies]" in line or "[project]" in line:
                    in_deps = True
                    continue
                if in_deps and line.startswith("["):
                    in_deps = False
                if in_deps and "=" in line and not line.startswith("#"):
                    name, version = line.split("=", 1)
                    ecosystems["python"]["dependencies"].append({"name": name.strip(), "version": version.strip().strip('"\' ')})

        elif "pom.xml" in filepath:
            ecosystems.setdefault("maven", {"source_file": filepath, "dependencies": []})
            # Basic extraction of dependencies from pom.xml
            in_deps = False
            current_dep = {}
            for line in content.splitlines():
                if "<dependencies>" in line:
                    in_deps = True
                    continue
                if "</dependencies>" in line:
                    in_deps = False
                if in_deps and "<dependency>" in line:
                    current_dep = {}
                if in_deps and "</dependency>" in line and current_dep.get("name"):
                    ecosystems["maven"]["dependencies"].append(current_dep)
                if in_deps and "<groupId>" in line:
                    current_dep["group"] = line.strip().replace("<groupId>", "").replace("</groupId>", "")
                if in_deps and "<artifactId>" in line:
                    current_dep["name"] = line.strip().replace("<artifactId>", "").replace("</artifactId>", "")
                if in_deps and "<version>" in line:
                    current_dep["version"] = line.strip().replace("<version>", "").replace("</version>", "")

    if ecosystems:
        return json.dumps({
            "ecosystems": [
                {
                    "ecosystem": ecosystem,
                    "source_file": data["source_file"],
                    "total": len(data["dependencies"]),
                    "dependencies": data["dependencies"]
                }
                for ecosystem, data in ecosystems.items()
            ]
        }, indent=2)

    return json.dumps({"error": "No supported dependency file found (requirements.txt, package.json, pyproject.toml, pom.xml)"})


def check_vulnerabilities(owner: str, repo: str) -> str:
    """
    Check project dependencies against the OSV (Open Source Vulnerabilities) database.
    Calls get_dependencies internally, then queries osv.dev for known CVEs.

    Args:
        owner: Repository owner
        repo: Repository name

    Returns:
        JSON string with list of vulnerable packages and their CVE details
    """
    def get_vuln_details(vuln_id: str) -> dict:
        response = requests.get(f"{OSV_API}/vulns/{vuln_id}")
        if response.status_code == 200:
            return response.json()
        return {"id": vuln_id, "error": "Details not found"}

    ecosystems = {}

    # Step 1: get dependencies
    deps = json.loads(get_dependencies(owner, repo))

    for d in deps["ecosystems"]:

        if "error" in d:
            return json.dumps({"error": d["error"]})

        if d["ecosystem"] == "python":
            ecosystem = "PyPI"
        elif d["ecosystem"] == "npm":
            ecosystem = "npm"
        elif d["ecosystem"] == "java":
            ecosystem = "Maven"
        else:
            ecosystem = "unknown"
        dependencies = d["dependencies"]

        # Step 2: build OSV batch query
        queries = []
        for dep in dependencies:
            query = {"package": {"name": dep["name"], "ecosystem": ecosystem}}
            if dep.get("version"):
                query["version"] = dep["version"]
            queries.append(query)

        if not queries:
            return json.dumps({"message": "No dependencies to check."})

        # OSV batch endpoint accepts up to 1000 queries
        osv_response = requests.post(
            f"{OSV_API}/querybatch",
            json={"queries": queries},
            headers={"Content-Type": "application/json"}
        )

        osv_response.raise_for_status()
        osv_results = osv_response.json().get("results", [])

        # Step 3: collect vulnerable packages
        vulnerabilities = []
        for dep, result in zip(dependencies, osv_results):
            vulns = result.get("vulns", [])
            if vulns:
                for v in vulns:
                    details = get_vuln_details(v["id"])
                    v.update(details)  # enrich with details for severity, summary, etc.
                    vulnerabilities.append({
                        "package": dep["name"],
                        "version": dep.get("version"),
                        "vulnerability_count": len(vulns),
                        "vulnerabilities": [
                            {
                                "id": v["id"],
                                "summary": v.get("summary") or v.get("details", "No summary available")[:200],
                                "severity": v.get("database_specific", {}).get("severity", "unknown"),
                                "fixed_in": [
                                    event["fixed"]
                                    for affected in v.get("affected", [])
                                    for rng in affected.get("ranges", [])
                                    if rng.get("type") == "ECOSYSTEM"
                                    for event in rng.get("events", [])
                                    if "fixed" in event
                                ]
                            }
                            for v in vulns[:5]  # cap at 5 CVEs per package
                        ]
                    })
        
        ecosystems.setdefault(
            ecosystem, {
                "dependencies": dependencies,
                "packages_checked": len(dependencies),
                "vulnerabilities": len(vulnerabilities),
                "results": vulnerabilities
            }
        )

    return json.dumps({
        "results": [
            {
                "ecosystem": eco,
                "packages_checked": data["packages_checked"],
                "vulnerabilities_found": data["vulnerabilities"],
                "vulnerable_packages": data["results"]
            }
            for eco, data in ecosystems.items()
        ]
    }, indent=2)