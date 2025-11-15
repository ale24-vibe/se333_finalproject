#!/usr/bin/env python3
"""
Parse JaCoCo XML report and print uncovered classes/methods and simple recommendations.

This script now supports a --json flag to emit machine-readable JSON suitable for
redirecting into a file (for example: `.mcp/coverage_analyzer.py --json > coverage.json`).
"""
import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime


JACOCO_XML = Path('target/jacoco-report/jacoco.xml')


def parse_jacoco(xml_path: Path):
    """Return a tuple (coverage_dict, uncovered_methods_list).

    coverage_dict maps counter types (LINE, INSTRUCTION, BRANCH) to a dict with
    missed and covered counts and percentage.
    uncovered_methods_list is a list of dicts with pkg, class, method, type, missed, covered.
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # collect report-level counters first
    counters = {}
    for counter in root.findall('counter'):
        ctype = counter.get('type')
        missed = int(counter.get('missed'))
        covered = int(counter.get('covered'))
        counters[ctype] = {'missed': missed, 'covered': covered}

    # fallback: if report-level counters missing, aggregate from packages
    if not counters:
        for package in root.findall('package'):
            for counter in package.findall('counter'):
                ctype = counter.get('type')
                missed = int(counter.get('missed'))
                covered = int(counter.get('covered'))
                if ctype not in counters:
                    counters[ctype] = {'missed': 0, 'covered': 0}
                counters[ctype]['missed'] += missed
                counters[ctype]['covered'] += covered

    # compute percentages
    coverage = {}
    for ctype, vals in counters.items():
        total = vals['missed'] + vals['covered']
        pct = 100.0 * vals['covered'] / total if total > 0 else 0.0
        coverage[ctype.lower()] = {
            'missed': vals['missed'],
            'covered': vals['covered'],
            'percent': round(pct, 2),
        }

    # find uncovered methods
    uncovered = []
    for package in root.findall('package'):
        pkg_name = package.get('name')
        for cls in package.findall('class'):
            cls_name = cls.get('name')
            for m in cls.findall('method'):
                mname = m.get('name')
                for counter in m.findall('counter'):
                    ctype = counter.get('type')
                    missed = int(counter.get('missed'))
                    covered = int(counter.get('covered'))
                    if missed > 0:
                        uncovered.append({
                            'package': pkg_name,
                            'class': cls_name,
                            'method': mname,
                            'type': ctype,
                            'missed': missed,
                            'covered': covered,
                        })

    return coverage, uncovered


def analyze(json_out: bool = False):
    if not JACOCO_XML.exists():
        msg = f"JaCoCo XML not found at {JACOCO_XML}. Run `mvn verify` or `mvn test` to generate it."
        if json_out:
            print(json.dumps({'error': msg}))
            return 1
        print(msg)
        return 1

    coverage, uncovered = parse_jacoco(JACOCO_XML)

    if json_out:
        payload = {
            'timestamp': datetime.now().isoformat(),
            'report_path': str(JACOCO_XML),
            'coverage': {k: v['percent'] for k, v in coverage.items()},
            'coverage_detail': coverage,
            'uncovered': uncovered,
        }
        print(json.dumps(payload, indent=2))
        return 0

    # human-friendly output
    if not uncovered:
        print("No uncovered methods found in JaCoCo XML (good coverage or no instrumentation).")
        # also print a short coverage summary
        if coverage:
            print('\nCoverage summary:')
            for k, v in coverage.items():
                print(f" - {k}: {v['percent']}% ({v['covered']}/{v['missed'] + v['covered']})")
        return 0

    print("Uncovered code segments (method-level):")
    for e in uncovered:
        print(f" - {e['package']}.{e['class']}#{e['method']} : {e['type']} missed={e['missed']} covered={e['covered']}")
    print("\nRecommendations:")
    print(" - Add focused unit tests that call these methods with representative inputs.")
    print(" - For branches, add tests that exercise both true/false paths.")
    print(" - If methods are hard to test, consider extracting logic to smaller testable units.")
    return 0


def main():
    p = argparse.ArgumentParser(description='Parse JaCoCo XML and emit coverage information.')
    p.add_argument('--json', action='store_true', help='Emit JSON output (machine-readable)')
    args = p.parse_args()
    return analyze(json_out=args.json)


if __name__ == '__main__':
    raise SystemExit(main())
