#!/usr/bin/env python3
"""
Simple MCP-style tool: scan Java sources in src/main/java and generate JUnit5 test stubs
into src/test/java. This is naive but suitable as a starter.
"""
import os
import re
from pathlib import Path

SRC_DIR = Path("src/main/java")
TEST_DIR = Path("src/test/java")


def find_java_files():
    for root, _, files in os.walk(SRC_DIR):
        for f in files:
            if f.endswith('.java'):
                yield Path(root) / f


method_re = re.compile(r"public\s+(?:static\s+)?([\w<>\[\]]+)\s+(\w+)\s*\(([^)]*)\)")
class_re = re.compile(r"public\s+class\s+(\w+)")


def parse_methods(java_text):
    methods = []
    # naive line-oriented parse: find lines with 'public' and '(' and ')' and extract name
    for line in java_text.splitlines():
        line = line.strip()
        if not line.startswith('public '):
            continue
        if '(' not in line or ')' not in line:
            continue
        # remove trailing throws clause and body start
        sig = line.split('throws')[0]
        sig = sig.split('{')[0].strip()
        try:
            before_paren, argstr = sig.split('(', 1)
            argstr = argstr.rsplit(')', 1)[0]
            parts = before_paren.split()
            if len(parts) >= 2:
                ret = parts[-2]
                name = parts[-1]
                methods.append((ret.strip(), name.strip(), argstr.strip()))
        except Exception:
            continue
    return methods


def parse_classname(java_text):
    m = class_re.search(java_text)
    return m.group(1) if m else None


def default_arg_for(param_type, param_name=''):
    # Very naive defaults. Avoid zero for parameters that look like denominators.
    if param_type in ("int", "short", "long", "byte", "float", "double"):
        # if name hints at divisor, use 1 to avoid division by zero
        if any(token in param_name.lower() for token in ("div", "denom", "b", "denominator")):
            return "1"
        return "0"
    if param_type == "boolean":
        return "false"
    return "null"


def generate_test_for(java_path: Path):
    text = java_path.read_text()
    classname = parse_classname(text)
    if not classname:
        return
    methods = parse_methods(text)
    print(f"Parsed methods for {classname}: {methods}")
    # derive package path
    rel = java_path.relative_to(SRC_DIR)
    pkg_parts = rel.parent.parts
    test_pkg = ".".join(pkg_parts) if pkg_parts else ""

    test_dir = TEST_DIR.joinpath(*pkg_parts)
    test_dir.mkdir(parents=True, exist_ok=True)
    test_classname = classname + "Test"
    out = []
    if test_pkg:
        out.append(f"package {test_pkg};\n")
    out.append("import org.junit.jupiter.api.Test;\n")
    out.append("import static org.junit.jupiter.api.Assertions.*;\n\n")
    out.append(f"public class {test_classname} {{\n\n")
    out.append(f"    @Test\n    public void generatedSmokeTest() throws Exception {{\n")
    out.append(f"        {classname} subject = new {classname}();\n")

    # create simple invocations
    for ret, name, args in methods:
        # avoid constructors/getters/setters trivial
        if name.lower().startswith("get") or name.lower().startswith("set"):
            continue
        # create argument list
        arg_vals = []
        if args:
            for p in args.split(','):
                p = p.strip()
                if not p:
                    continue
                parts = p.split()
                if len(parts) >= 2:
                    typ = parts[0]
                    param_name = parts[1]
                else:
                    typ = parts[0]
                    param_name = ''
                arg_vals.append(default_arg_for(typ, param_name))
        arglist = ", ".join(arg_vals)
        # we will call the method and, if primitive result, just ignore, else assertNotNull
        if ret in ("void", "int", "short", "long", "byte", "float", "double", "boolean"):
            out.append(f"        subject.{name}({arglist});\n")
        else:
            out.append(f"        Object r = subject.{name}({arglist});\n")
            out.append(f"        assertNotNull(r);\n")

    out.append("    }\n")
    out.append("}\n")

    (test_dir / (test_classname + ".java")).write_text("\n".join(out))
    print(f"Generated {test_classname}.java in {test_dir}")


def main():
    for java in find_java_files():
        generate_test_for(java)


if __name__ == '__main__':
    main()
