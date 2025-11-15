#!/usr/bin/env python3
"""
Validate and print coverage JSON files.

Usage:
  .mcp/print_coverage.py [path] [--latest]

This script defaults to `coverage.json` but will work with `coverage-history.json` (list of runs).
It prints the latest entry (if requested) and a compact coverage summary when available.
"""
import argparse
import json
import sys
from pathlib import Path


def fail(msg: str, code: int = 1) -> None:
    print(msg, file=sys.stderr)
    sys.exit(code)


def pretty_print_coverage(obj):
    cov = obj.get("coverage") if isinstance(obj, dict) else None
    if cov and any(k in cov for k in ("line", "instruction", "branch")):
        print("Coverage:")
        for k in ("line", "instruction", "branch"):
            if k in cov:
                print(f"  {k}: {cov[k]}%")
    else:
        print(json.dumps(obj, indent=2))


def main():
    p = argparse.ArgumentParser(description="Validate and inspect a coverage JSON file.")
    p.add_argument("path", nargs="?", default="coverage.json", help="Path to coverage JSON (default: coverage.json)")
    p.add_argument("--latest", action="store_true", help="If file is a list, print only the last entry")
    args = p.parse_args()

    path = Path(args.path)
    if not path.exists():
        fail(f"{path} does not exist.")
    if path.stat().st_size == 0:
        fail(f"{path} is empty.")
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        fail(f"Failed to parse {path}: {e}")

    # If the file is a list, optionally pick the last run
    if isinstance(data, list):
        if not data:
            fail(f"{path} contains an empty list.")
        entry = data[-1] if args.latest else data
    else:
        entry = data

    if args.latest and isinstance(entry, dict):
        ts = entry.get("timestamp", "<no-timestamp>")
        runid = entry.get("run_id", "<no-run-id>")
        print(f"Latest run: {ts} (id: {runid})")

    pretty_print_coverage(entry)
    sys.exit(0)


if __name__ == "__main__":
    main()
