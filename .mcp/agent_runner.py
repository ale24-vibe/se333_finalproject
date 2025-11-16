#!/usr/bin/env python3
"""Run tests and collect coverage & quality metrics for the codebase project.

Generates/updates:
 - codebase/coverage-history.json (append entry)
 - codebase/coverage-dashboard.md (summary table)

Metrics captured per run:
 - timestamp
 - total_tests / failures / errors / skipped
 - assertions_estimate (count of 'assert' in test sources)
 - coverage (line/instruction/branch %) if JaCoCo report available
 - uncovered_methods count
"""
from __future__ import annotations
import subprocess, json, re, datetime
from pathlib import Path
import shutil, sys

ROOT = Path(__file__).resolve().parent.parent
CODEBASE = ROOT / 'codebase'
HISTORY = CODEBASE / 'coverage-history.json'
DASHBOARD = CODEBASE / 'coverage-dashboard.md'

PARSE_JACOCO = ROOT / '.mcp' / 'parse_jacoco.py'

def run_maven_tests():
    mvn = shutil.which('mvn') or shutil.which('mvn.cmd') or 'mvn'
    cmd = [mvn, '-f', str(CODEBASE / 'pom.xml'), '-U', 'test']
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr

def extract_surefire_stats(output: str):
    # Surefire summary line pattern: Tests run: 2300, Failures: 34, Errors: 14, Skipped: 4
    m = re.search(r'Tests run:\s*(\d+),\s*Failures:\s*(\d+),\s*Errors:\s*(\d+),\s*Skipped:\s*(\d+)', output)
    if not m:
        return None
    return {
        'total_tests': int(m.group(1)),
        'failures': int(m.group(2)),
        'errors': int(m.group(3)),
        'skipped': int(m.group(4)),
    }

def count_assertions():
    count = 0
    for p in (CODEBASE / 'src' / 'test' / 'java').rglob('*.java'):
        try:
            txt = p.read_text(encoding='ISO-8859-1', errors='ignore')
        except Exception:
            continue
        count += txt.count('assert')
    return count

def parse_jacoco():
    if not PARSE_JACOCO.exists():
        return None
    py = sys.executable or 'python'
    proc = subprocess.run([py, str(PARSE_JACOCO)], capture_output=True, text=True)
    out = proc.stdout
    coverage = None
    uncovered_count = None
    # Try to infer counts from output lines
    if 'No uncovered methods' in out:
        uncovered_count = 0
    else:
        uc_lines = [l for l in out.splitlines() if l.strip().startswith('- ') and '#'
                    in l and 'missed=' in l]
        uncovered_count = len(uc_lines) if uc_lines else None
    # We don't have detailed percentages here; could extend later by importing coverage_analyzer
    return {
        'uncovered_methods': uncovered_count,
    }

def load_history():
    if HISTORY.exists():
        try:
            return json.loads(HISTORY.read_text(encoding='utf-8'))
        except Exception:
            return []
    return []

def save_history(data):
    HISTORY.write_text(json.dumps(data, indent=2), encoding='utf-8')

def render_dashboard(history):
    lines = ["# Coverage & Quality Dashboard", '',
             '| Run | Timestamp | Tests | Fail | Err | Skip | Assertions | Uncovered Methods |',
             '| --- | --------- | ----- | ---- | --- | ---- | ---------- | ----------------- |']
    for i, entry in enumerate(history, 1):
        lines.append(f"| {i} | {entry['timestamp']} | {entry.get('total_tests','')} | {entry.get('failures','')} | "
                     f"{entry.get('errors','')} | {entry.get('skipped','')} | {entry.get('assertions_estimate','')} | "
                     f"{entry.get('uncovered_methods','')} |")
    DASHBOARD.write_text('\n'.join(lines) + '\n', encoding='utf-8')

def main():
    rc, output = run_maven_tests()
    stats = extract_surefire_stats(output) or {}
    assertions = count_assertions()
    jacoco = parse_jacoco() or {}
    entry = {
        'timestamp': datetime.datetime.utcnow().isoformat(),
        **stats,
        'assertions_estimate': assertions,
        **jacoco,
        'build_success': rc == 0,
    }
    history = load_history()
    history.append(entry)
    save_history(history)
    render_dashboard(history)
    print(json.dumps(entry, indent=2))
    return 0 if rc == 0 else 1

if __name__ == '__main__':
    raise SystemExit(main())
