#!/usr/bin/env python3
"""
AI Code Review Agent (MCP tool)

This script orchestrates static analysis runs (SpotBugs, PMD), optional CodeQL scanning
and style enforcement (google-java-format) when available locally. It writes a JSON
summary to `.mcp/ai_review_report.json` and prints a human-readable summary to stdout.

The script is intentionally conservative: it detects installed tools and runs them
via Maven goals where possible to avoid modifying the build.
"""
import json
import os
import shlex
import shutil
import subprocess
import sys
from xml.etree import ElementTree as ET
from datetime import datetime


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
REPORT_PATH = os.path.join(os.path.dirname(__file__), 'ai_review_report.json')


def run(cmd, cwd=ROOT, capture=True):
    print(f"Running: {cmd}")
    try:
        if capture:
            completed = subprocess.run(shlex.split(cmd), cwd=cwd, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            return completed.returncode, completed.stdout
        else:
            completed = subprocess.run(shlex.split(cmd), cwd=cwd, check=False)
            return completed.returncode, ''
    except FileNotFoundError:
        return 127, ''


def detect_tool(name):
    return shutil.which(name) is not None


def run_spotbugs():
    # Try Maven plugin first (will download plugin if needed). If the plugin
    # resolution fails, prefer the SpotBugs CLI if it's installed locally.
    code, out = run('mvn -q com.github.spotbugs:spotbugs-maven-plugin:4.7.3:spotbugs')
    result = {'name': 'spotbugs', 'exit_code': code, 'output_snippet': out[:2000]}
    if code == 0:
        return result

    # Maven plugin failed. If SpotBugs CLI is available, run it against compiled classes.
    if detect_tool('spotbugs'):
        # Ensure project is compiled so target/classes exists.
        run('mvn -q -DskipTests package', capture=True)
        cli_cmd = 'spotbugs -textui -effort:max -low -xml:withMessages -output target/spotbugsXml.xml target/classes'
        cli_code, cli_out = run(cli_cmd)
        # attach CLI info to the result and parse the XML report if present
        report_path = os.path.join(ROOT, 'target', 'spotbugsXml.xml')
        cli_info = {
            'cli_used': True,
            'cli_exit_code': cli_code,
            'cli_output_snippet': cli_out[:2000],
            'cli_report': 'target/spotbugsXml.xml',
            'note': 'Maven plugin failed; fell back to SpotBugs CLI'
        }
        # Parse report for counts and sample issues
        if os.path.exists(report_path):
            try:
                tree = ET.parse(report_path)
                root = tree.getroot()
                # Count BugInstance nodes
                bug_instances = root.findall('.//BugInstance')
                bug_count = len(bug_instances)
                cli_info['cli_bug_count'] = bug_count
                # collect up to 10 sample issues
                samples = []
                for bi in bug_instances[:10]:
                    btype = bi.get('type') or ''
                    category = bi.get('category') or ''
                    priority = bi.get('priority') or ''
                    # message may be in LongMessage or ShortMessage
                    msg = ''
                    lm = bi.find('LongMessage')
                    if lm is not None and lm.text:
                        msg = lm.text.strip()
                    else:
                        sm = bi.find('ShortMessage')
                        if sm is not None and sm.text:
                            msg = sm.text.strip()
                    samples.append({'type': btype, 'category': category, 'priority': priority, 'message': msg})
                cli_info['cli_issues_sample'] = samples
            except Exception as e:
                cli_info['cli_parse_error'] = str(e)

        result.update(cli_info)
        return result

    # No CLI available; return the original plugin failure info.
    result.update({'note': 'Maven plugin failed and SpotBugs CLI not found'})
    return result


def run_pmd():
    code, out = run('mvn -q pmd:pmd')
    return {'name': 'pmd', 'exit_code': code, 'output_snippet': out[:2000]}


def run_google_java_format(apply_fixes=False):
    # If google-java-format is installed, run it. Prefer --dry-run unless apply_fixes True.
    gjf = shutil.which('google-java-format')
    if not gjf:
        return {'name': 'google-java-format', 'present': False}
    cmd = f"google-java-format {'-n' if not apply_fixes else '-i'} --replace $(git ls-files '*.java')"
    code, out = run(cmd, capture=True)
    return {'name': 'google-java-format', 'present': True, 'exit_code': code, 'output_snippet': out[:2000]}


def run_codeql():
    # Detect codeql CLI and run a simple database build + analyze if present.
    if not detect_tool('codeql'):
        return {'name': 'codeql', 'present': False}
    # CodeQL scanning is heavy; try to run in a temp dir and catch failures.
    code, out = run('codeql version')
    if code != 0:
        return {'name': 'codeql', 'present': True, 'exit_code': code, 'output_snippet': out[:2000]}
    # We won't attempt a full DB build here to avoid long-running tasks by default.
    return {'name': 'codeql', 'present': True, 'note': 'CodeQL CLI present; full scan skipped (run in CI for full results)'}


def summarize(results):
    now = datetime.now().isoformat()
    summary = {'timestamp': now, 'results': results}
    with open(REPORT_PATH, 'w') as f:
        json.dump(summary, f, indent=2)
    print('\nAI Code Review summary saved to', REPORT_PATH)
    # Print concise human summary
    for r in results:
        name = r.get('name')
        if r.get('present') is False:
            print(f"- {name}: not installed / skipped")
        else:
            code = r.get('exit_code')
            if code is None:
                print(f"- {name}: {r.get('note', 'skipped')}")
            else:
                status = 'OK' if code == 0 else f'ISSUES (exit {code})'
                print(f"- {name}: {status}")


def main():
    results = []

    # SpotBugs
    print('== SpotBugs ==')
    sb = run_spotbugs()
    results.append(sb)

    # PMD
    print('\n== PMD ==')
    pmd = run_pmd()
    results.append(pmd)

    # google-java-format (dry-run)
    print('\n== google-java-format (dry-run) ==')
    gjf = run_google_java_format(apply_fixes=False)
    results.append(gjf)

    # CodeQL
    print('\n== CodeQL detection ==')
    codeql = run_codeql()
    results.append(codeql)

    summarize(results)


if __name__ == '__main__':
    main()
