# Specification-Based Testing Generator (MCP Tool)

Tool: `spec_generate_tests(spec: dict, write_files: bool = True)`

Purpose: Generate Equivalence Class Partitioning and Boundary Value Analysis test cases from a structured specification and optionally render a JUnit 4 test class.

## Input Schema

- `package` (string): Java package of class under test (CUT)
- `testPackage` (string, optional): package for generated tests (defaults to `package`)
- `classUnderTest` (string): fully qualified class name (e.g., `example.Calculator`)
- `method` (string): method name (e.g., `add`)
- `testClassName` (string, optional): output test class name
- `outputDir` (string, optional): defaults to `src/test/java`
- `output.oracle` (string, optional): arithmetic expression over parameter names to compute expected value (e.g., `a + b`)
- `params` (array): list of parameter specs:
  - `name` (string)
  - `type` (string): `int|long|short|byte|float|double|...`
  - `domain` (object): either `{min, max}` for numeric or `{values: [...]}` for enum-like
  - `equivalence_classes` (optional): list of `{name, values|range}` (auto-derived if omitted)
  - `boundaries` (optional): list of explicit boundary values (auto-derived from `domain` if omitted)

## Generation Strategy

- Equivalence class tests: vary one parameter per test using class representatives, others set to nominal.
- Boundary value tests: vary one parameter per test using derived boundaries; add all-min/all-max combo if available.

## Example

Request (via MCP):

```
{
  "package": "example",
  "testPackage": "example",
  "classUnderTest": "example.Calculator",
  "method": "add",
  "testClassName": "CalculatorSpecTests",
  "output": {"type": "int", "oracle": "a + b"},
  "params": [
    {"name": "a", "type": "int", "domain": {"min": -10, "max": 10}},
    {"name": "b", "type": "int", "domain": {"min": -10, "max": 10}}
  ]
}
```

Response:
- JSON summary of generated cases and (if `write_files=true`) path to `src/test/java/example/CalculatorSpecTests.java`.

## Measurable Value

- Accelerates creation of edge-case tests aligned with specs
- Standardizes boundary coverage for numeric parameters
- Optional oracle evaluation precomputes expected values for simple arithmetic behaviors
