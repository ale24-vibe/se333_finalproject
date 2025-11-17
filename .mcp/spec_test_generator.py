"""
Specification-Based Testing Generator

Generates test cases using:
- Equivalence Class Partitioning
- Boundary Value Analysis (BVA)

Input: a JSON-like dict specification describing the method under test and
its parameters. See README section for schema.

Outputs: a dict containing generated cases and, optionally, a rendered
JUnit 4 test class written to the workspace.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import math
import os
import ast


@dataclass
class ParamSpec:
    name: str
    type: str
    domain: Optional[Dict[str, Any]] = None  # e.g., {"min": -10, "max": 10}
    equivalence_classes: Optional[List[Dict[str, Any]]] = None  # [{name, values|range}]
    boundaries: Optional[List[Any]] = None


def _midpoint(min_v: int, max_v: int) -> int:
    try:
        return int(min_v + (max_v - min_v) // 2)
    except Exception:
        return min_v


def _derive_default_equivalence_classes(p: ParamSpec) -> List[Dict[str, Any]]:
    ecs: List[Dict[str, Any]] = []
    if p.type in {"int", "long", "short", "byte"} and p.domain and "min" in p.domain and "max" in p.domain:
        min_v = int(p.domain["min"])
        max_v = int(p.domain["max"])
        zero_in = (min_v <= 0 <= max_v)
        if min_v < 0:
            ecs.append({"name": "negative", "range": [min_v, -1]})
        if zero_in:
            ecs.append({"name": "zero", "values": [0]})
        if max_v > 0:
            ecs.append({"name": "positive", "range": [1, max_v]})
    elif p.type in {"float", "double"} and p.domain and "min" in p.domain and "max" in p.domain:
        min_v = float(p.domain["min"]) 
        max_v = float(p.domain["max"]) 
        ecs.append({"name": "low", "range": [min_v, (min_v + max_v) / 2.0]})
        ecs.append({"name": "high", "range": [(min_v + max_v) / 2.0, max_v]})
    elif p.domain and "values" in p.domain:
        # Enumerated set
        vals = list(p.domain["values"])[:3]
        for i, v in enumerate(vals):
            ecs.append({"name": f"value_{i}", "values": [v]})
    else:
        # Fallback nominal-only
        ecs.append({"name": "nominal", "values": [0] if p.type in {"int","long","short","byte"} else [None]})
    return ecs


def _derive_default_boundaries(p: ParamSpec) -> List[Any]:
    b: List[Any] = []
    if p.type in {"int", "long", "short", "byte"} and p.domain and "min" in p.domain and "max" in p.domain:
        min_v = int(p.domain["min"])
        max_v = int(p.domain["max"])
        candidates = [min_v, min_v + 1, max_v - 1, max_v]
        for c in candidates:
            if min_v <= c <= max_v and c not in b:
                b.append(c)
        # include near zero if within domain
        for z in (-1, 0, 1):
            if min_v <= z <= max_v and z not in b:
                b.append(z)
    elif p.type in {"float", "double"} and p.domain and "min" in p.domain and "max" in p.domain:
        min_v = float(p.domain["min"]) 
        max_v = float(p.domain["max"]) 
        mid = (min_v + max_v) / 2.0
        b = [min_v, math.nextafter(min_v, math.inf), math.nextafter(max_v, -math.inf), max_v, mid]
    else:
        # Not numeric or unknown domain
        b = []
    return b


def _nominal_value(p: ParamSpec) -> Any:
    if p.equivalence_classes:
        ec = p.equivalence_classes[0]
        if "values" in ec and len(ec["values"]) > 0:
            return ec["values"][0]
        if "range" in ec:
            lo, hi = ec["range"]
            if isinstance(lo, float) or isinstance(hi, float):
                return (float(lo) + float(hi)) / 2.0
            return _midpoint(int(lo), int(hi))
    if p.domain:
        if "values" in p.domain and p.domain["values"]:
            return p.domain["values"][0]
        if "min" in p.domain and "max" in p.domain:
            lo = p.domain["min"]
            hi = p.domain["max"]
            if p.type in {"int","long","short","byte"}:
                return _midpoint(int(lo), int(hi))
            if p.type in {"float","double"}:
                return (float(lo) + float(hi)) / 2.0
    # defaults
    return 0 if p.type in {"int","long","short","byte"} else 0.0 if p.type in {"float","double"} else None


def _representative_from_ec(ec: Dict[str, Any], p: ParamSpec) -> Any:
    if "values" in ec and ec["values"]:
        return ec["values"][0]
    if "range" in ec:
        lo, hi = ec["range"]
        if p.type in {"int","long","short","byte"}:
            return _midpoint(int(lo), int(hi))
        else:
            return (float(lo) + float(hi)) / 2.0
    return _nominal_value(p)


class SafeExprEvaluator(ast.NodeVisitor):
    allowed_nodes = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Num, ast.Load,
                     ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod,
                     ast.Pow, ast.USub, ast.UAdd, ast.Name, ast.Call)

    allowed_funcs = {"abs": abs, "min": min, "max": max, "round": round}

    def __init__(self, env: Dict[str, Any]):
        self.env = env

    def visit(self, node):
        if not isinstance(node, self.allowed_nodes):
            raise ValueError("Disallowed expression element")
        return super().visit(node)

    def visit_Expression(self, node):
        return self.visit(node.body)

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        return self._apply_op(node.op, left, right)

    def visit_UnaryOp(self, node):
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.USub):
            return -operand
        if isinstance(node.op, ast.UAdd):
            return +operand
        raise ValueError("Unsupported unary op")

    def visit_Num(self, node):
        return node.n

    def visit_Name(self, node):
        if node.id in self.env:
            return self.env[node.id]
        raise ValueError(f"Unknown variable {node.id}")

    def visit_Call(self, node):
        if not isinstance(node.func, ast.Name) or node.func.id not in self.allowed_funcs:
            raise ValueError("Unsupported function call")
        func = self.allowed_funcs[node.func.id]
        args = [self.visit(a) for a in node.args]
        return func(*args)

    @staticmethod
    def _apply_op(op, a, b):
        if isinstance(op, ast.Add):
            return a + b
        if isinstance(op, ast.Sub):
            return a - b
        if isinstance(op, ast.Mult):
            return a * b
        if isinstance(op, ast.Div):
            return a / b
        if isinstance(op, ast.FloorDiv):
            return a // b
        if isinstance(op, ast.Mod):
            return a % b
        if isinstance(op, ast.Pow):
            return a ** b
        raise ValueError("Unsupported binary op")


def _eval_oracle(expr: str, inputs: Dict[str, Any]) -> Any:
    try:
        tree = ast.parse(expr, mode="eval")
        return SafeExprEvaluator(inputs).visit(tree)
    except Exception:
        return None


def normalize_spec(spec: Dict[str, Any]) -> Dict[str, Any]:
    params: List[ParamSpec] = []
    for p in spec.get("params", []):
        ps = ParamSpec(
            name=p["name"],
            type=p.get("type", "int"),
            domain=p.get("domain"),
            equivalence_classes=p.get("equivalence_classes"),
            boundaries=p.get("boundaries"),
        )
        if ps.equivalence_classes is None:
            ps.equivalence_classes = _derive_default_equivalence_classes(ps)
        if ps.boundaries is None:
            ps.boundaries = _derive_default_boundaries(ps)
        params.append(ps)
    new_spec = dict(spec)
    new_spec["_params_obj"] = params
    return new_spec


def generate_cases(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Produce equivalence class and boundary value test cases.

    Returns a dict with keys: cases (list), counts, metadata.
    """
    spec = normalize_spec(spec)
    params: List[ParamSpec] = spec["_params_obj"]
    cases: List[Dict[str, Any]] = []

    # Nominal baseline inputs
    nominal: Dict[str, Any] = {p.name: _nominal_value(p) for p in params}

    # Equivalence class tests: one-at-a-time variation
    for p in params:
        for ec in p.equivalence_classes or []:
            rep = _representative_from_ec(ec, p)
            inputs = dict(nominal)
            inputs[p.name] = rep
            cases.append({
                "type": "equivalence",
                "param": p.name,
                "class": ec.get("name", "anon"),
                "inputs": inputs,
            })

    # Boundary value tests: one-at-a-time plus all-min/all-max when available
    all_min: Dict[str, Any] = {}
    all_max: Dict[str, Any] = {}
    have_all_min_max = True
    for p in params:
        if p.boundaries and len(p.boundaries) >= 1:
            # Attempt to infer min/max from domain
            if p.domain and "min" in p.domain and "max" in p.domain:
                all_min[p.name] = p.domain["min"]
                all_max[p.name] = p.domain["max"]
            else:
                have_all_min_max = False
        else:
            have_all_min_max = False

    for p in params:
        for b in p.boundaries or []:
            inputs = dict(nominal)
            inputs[p.name] = b
            cases.append({
                "type": "boundary",
                "param": p.name,
                "boundary": b,
                "inputs": inputs,
            })

    if have_all_min_max and all_min and all_max:
        cases.append({"type": "boundary-combo", "label": "all-min", "inputs": all_min})
        cases.append({"type": "boundary-combo", "label": "all-max", "inputs": all_max})

    return {
        "counts": {"total": len(cases), "equivalence": sum(1 for c in cases if c["type"]=="equivalence"),
                    "boundary": sum(1 for c in cases if c["type"].startswith("boundary"))},
        "cases": cases,
        "nominal": nominal,
        "spec": {k: v for k, v in spec.items() if k != "_params_obj"}
    }


def render_junit(spec: Dict[str, Any], cases: List[Dict[str, Any]]) -> str:
    package = spec.get("testPackage") or spec.get("package") or ""
    class_under_test = spec.get("classUnderTest")
    method = spec.get("method")
    test_class = spec.get("testClassName") or f"{class_under_test.split('.')[-1]}SpecTests"
    oracle_expr = None
    if isinstance(spec.get("output"), dict):
        oracle_expr = spec["output"].get("oracle")

    pkg_line = f"package {package};\n\n" if package else ""
    junit_version = str(spec.get("junitVersion", "5")).strip()
    if junit_version == "4":
        imports = """import org.junit.Test;\nimport static org.junit.Assert.*;\n\n"""
    else:  # default JUnit 5
        imports = """import org.junit.jupiter.api.Test;\nimport static org.junit.jupiter.api.Assertions.*;\n\n"""

    # Determine simple class name and constructor
    cls_simple = class_under_test.split(".")[-1] if class_under_test else "Calculator"
    methodsig_comment = f"// Method under test: {method}\n" if method else ""

    sb = []
    sb.append(pkg_line)
    sb.append(imports)
    sb.append(f"public class {test_class} {{\n")
    sb.append(f"    {methodsig_comment}")

    for idx, case in enumerate(cases):
        name_parts = ["spec", case["type"].replace("-", "_")]
        if case["type"] == "equivalence":
            name_parts.append(case.get("param", "p"))
            name_parts.append(case.get("class", "cls"))
        elif case["type"].startswith("boundary"):
            name_parts.append(case.get("param", case.get("label", "combo")))
        mname = "test_" + "_".join(name_parts) + f"_{idx}"
        sb.append("    @Test\n")
        sb.append(f"    public void {mname}() {{\n")
        sb.append(f"        {cls_simple} obj = new {cls_simple}();\n")
        # Build invocation
        inputs = case["inputs"]
        param_order = [p["name"] for p in spec.get("params", [])]
        args = ", ".join(_java_literal(inputs.get(n)) for n in param_order)
        if method:
            call = f"obj.{method}({args})"
        else:
            call = f"obj.underTest({args})"  # fallback

        if oracle_expr:
            expected = _eval_oracle(oracle_expr, inputs)
            if expected is not None:
                sb.append(f"        assertEquals({_java_literal(expected)}, {call});\n")
            else:
                sb.append(f"        // TODO: Provide oracle; auto-eval failed\n        {call};\n")
        else:
            sb.append(f"        // TODO: Add assertions for expected behavior\n        {call};\n")
        sb.append("    }\n\n")

    sb.append("}\n")
    return "".join(sb)


def _java_literal(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        # keep simple formatting
        return ("%g" % v)
    if v is None:
        return "null"
    return repr(v)


def write_junit_file(spec: Dict[str, Any], content: str) -> str:
    out_dir = spec.get("outputDir") or "src/test/java"
    package = spec.get("testPackage") or spec.get("package") or ""
    test_class = spec.get("testClassName") or "GeneratedSpecTests"
    pkg_path = package.replace(".", "/") if package else ""
    dest_dir = Path(out_dir) / pkg_path
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / f"{test_class}.java"
    path.write_text(content, encoding="utf-8")
    return str(path)


def generate_and_render(spec: Dict[str, Any], write_files: bool = True) -> Dict[str, Any]:
    cases_info = generate_cases(spec)
    junit_src = render_junit(cases_info["spec"], cases_info["cases"])
    out_file = None
    if write_files:
        out_file = write_junit_file(cases_info["spec"], junit_src)
    return {"summary": cases_info["counts"], "file": out_file, "nominal": cases_info["nominal"], "cases": cases_info["cases"]}
