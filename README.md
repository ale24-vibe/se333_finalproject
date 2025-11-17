# se333_finalproject

This repository contains two primary parts:

- A minimal Python MCP-compatible server (tools exposed via the MCP protocol). See `server.py`.
- A small Java project with tests and static analysis (Maven, JDK 17, JaCoCo, SpotBugs).

## Quick start — Python MCP server

1. Create and activate a virtualenv (recommended):

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install Python dependencies (from project root):

```bash
pip install -e .
# or explicitly:
pip install fastapi uvicorn httpx fastmcp mcp[cli]
```

3. Run the server:

```bash
python server.py
```

The server runs the MCP transport on port 8001 by default. Example discovery call:

```bash
curl -s http://127.0.0.1:8001/tools | jq
```

In VS Code: open the Command Palette → `MCP: Add Server` and paste the server URL `http://127.0.0.1:8001` (or `http://127.0.0.1:8001/mcp`).

## Build & Test — Java (Maven)

This project uses Java 17 (see `pom.xml`). Use Maven to build, run tests, and produce reports.

Common commands:

```bash
# Build, run tests, and run verify-phase plugins (Jacoco, SpotBugs bound to verify in the POM):
mvn -U -B clean verify

# Run tests only:
mvn -U test
```

Reports produced by the build:

- JaCoCo XML: `target/jacoco-report/jacoco.xml`
- JaCoCo HTML: `target/jacoco-report/index.html`
- SpotBugs (via POM): executed during the `verify` phase; configuration is in `pom.xml`.

If you need to run SpotBugs ad-hoc, use the same version that is pinned in the POM:

```bash
mvn com.github.spotbugs:spotbugs-maven-plugin:4.9.6.0:spotbugs
```

## Continuous Integration

GitHub Actions workflow `.github/workflows/ai-code-review.yml` runs the following checks on PRs and pushes to `main`:

- `mvn -U -B clean verify` (build, tests, JaCoCo, SpotBugs via POM)
- PMD: `mvn pmd:check`
- CodeQL analysis in a separate job

Note: the workflow relies on the SpotBugs plugin being declared in `pom.xml` to avoid version resolution issues.

## Notes

- Python server: `server.py` uses `fastmcp` when available, otherwise serves a FastAPI endpoint at `/mcp`.
- Java: project compiler source/target is Java 17 (see `pom.xml` properties).
- If you want CI to upload SpotBugs/JaCoCo artifacts, we can add `actions/upload-artifact` steps.

## Quick commands

```bash
# Start Python server
source .venv/bin/activate && python server.py

# Run full Java build + checks
mvn -U -B clean verify

# Run SpotBugs manually (if needed)
mvn com.github.spotbugs:spotbugs-maven-plugin:4.9.6.0:spotbugs
```

---

If you'd like, I can open a small PR with this README change on the current feature branch (`auto/add-spotbugs-plugin`) or create a separate branch. Which do you prefer?
