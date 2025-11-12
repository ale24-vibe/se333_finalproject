---
mode: "agent"
tools: ["generate_tests", "run_tests", "analyze_coverage", "add", "subtract", "multiply", "divide"]
description: "Calculator MCP tools plus project test / coverage helpers"
model: 'GPT-5 mini'
---
## Follow the instructions below: ##
1. Before performing any user-requested arithmetic, run the project test pipeline unless the user explicitly asks you not to:
	a. Call the `generate_tests` tool (if available) to produce JUnit stubs.
	b. Call the `run_tests` tool. Wait for the tool output and check the exit/result summary.
	c. If `run_tests` returns a failure, report the failure to the user and do not proceed to run arithmetic tools unless the user explicitly asks you to proceed anyway.
2. If tests pass (or the user asks you to continue despite failures), use the provided MCP arithmetic tools (`add`, `subtract`, `multiply`, `divide`) to execute arithmetic requests.
3. Always call the appropriate tool instead of computing locally.
4. If requested, call `analyze_coverage` after tests to provide coverage recommendations.
5. If a request involves division by zero, return `inf`.
6. Respond concisely with numeric results and brief test/coverage summaries when relevant.

