# 🔍 RepoAudit — GitHub Repository Auditor

AI agent that audits GitHub repositories in real time. Given a repository name, the agent inspects its structure, analyzes its dependencies, and detects known security vulnerabilities — producing a prioritized report of findings and recommendations.

---

## Use Case

Developers and teams often lack a quick way to assess the health of a codebase before adopting it, contributing to it, or deploying it. RepoAudit solves this by letting users ask natural language questions about any public GitHub repository and receiving a structured audit that covers:

- **Project structure** — presence of tests, CI/CD configuration, Docker setup, documentation, and security hygiene files
- **Dependency analysis** — automatic detection of the package ecosystem (Python/Node.js) and extraction of declared dependencies
- **Vulnerability scanning** — cross-referencing dependencies against the [OSV database](https://osv.dev) (Google Open Source Vulnerabilities) to surface known CVEs, severity scores, and available fix versions

---

## AI Model

**OpenAI `gpt-4o-mini`** via the Chat Completions API with tool calling enabled.

The model acts as an orchestrator: it decides which tools to invoke, in what order, and how to synthesize the results into a coherent audit report. It does not produce generic responses from training knowledge — every answer is grounded in data fetched live from the GitHub API and OSV.

---

## Improvements Over the Original Notebook

### 1. Domain Adaptation
The original notebook searched academic papers on arXiv. This project repurposes the same agentic architecture for a more practical and differentiated use case: real-time repository auditing using the GitHub API and OSV.

### 2. Agentic Tool Architecture
Five specialized tools replace the original two, each encapsulating a distinct inspection capability:

| Tool | Description |
|---|---|
| `get_repo_info` | Fetches repository metadata: language, license, stars, last activity, open issues |
| `get_file_tree` | Retrieves the full directory structure and computes structural signals (has tests, CI, Docker, README, etc.) |
| `get_file_content` | Reads specific files (README, config files, source code) for deeper inspection |
| `get_dependencies` | Parses the dependency file (`requirements.txt`, `package.json`, `pyproject.toml`) and extracts all declared packages with versions |
| `check_vulnerabilities` | Queries the OSV API in batch to find known CVEs across all detected dependencies |

The agent chains these tools autonomously — for a full audit, it may call `get_file_tree` to detect the ecosystem, then `get_dependencies` to extract packages, then `check_vulnerabilities` to scan them, all without user intervention.

### 3. Conversation Memory
Each API session maintains a conversation history keyed by `session_id`. Users can ask follow-up questions within the same audit session ("what about the test coverage?" after an initial audit) and the agent retains full context across turns.

### 4. REST API — Remotely Consumable
The notebook logic is exposed as a FastAPI microservice (`POST /chat`), making the agent consumable from any client without requiring a local Python environment. The response includes both the model's reply and a structured list of every tool call made during the turn:

```json
{
  "reply": "The repository has 3 vulnerable dependencies...",
  "session_id": "abc-123",
  "tool_calls": [
    { "tool": "get_dependencies", "args": { "owner": "psf", "repo": "requests" }, "status": "completed" },
    { "tool": "check_vulnerabilities", "args": { "owner": "psf", "repo": "requests" }, "status": "completed" }
  ]
}
```

### 5. Web Interface
A standalone HTML/CSS/JS frontend provides an intuitive chat interface with:
- Live tool-call feed showing which tools the agent is invoking in real time
- Structured rendering of vulnerability reports with severity badges and fix versions
- Clickable example queries for immediate onboarding
- Session management with a "New Audit" button to reset context

---

## Architecture

```
User (browser)
     │
     ▼
Web Interface (HTML/JS)
     │  POST /chat  { message, session_id }
     ▼
FastAPI Server (main.py)
     │
     ├── Session Store (in-memory, keyed by session_id)
     │
     └── Agent Loop (Chat Completions + tool calling)
          │
          ├── get_repo_info      ──► GitHub API
          ├── get_file_tree      ──► GitHub API
          ├── get_file_content   ──► GitHub API
          ├── get_dependencies   ──► GitHub API (reads dependency files)
          └── check_vulnerabilities ──► OSV API (osv.dev)
```