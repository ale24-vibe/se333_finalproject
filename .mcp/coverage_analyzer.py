#!/usr/bin/env python3
"""
Parse JaCoCo XML report and print uncovered classes/methods and simple recommendations.
"""
import xml.etree.ElementTree as ET
from pathlib import Path

JACOCO_XML = Path('target/jacoco-report/jacoco.xml')


def analyze():
    if not JACOCO_XML.exists():
        print(f"JaCoCo XML not found at {JACOCO_XML}. Run `mvn verify` or `mvn test` to generate it.")
        return 1
    tree = ET.parse(JACOCO_XML)
    root = tree.getroot()
    ns = ''
    uncovered = []
    # Jacoco XML structure: <report><package><class name="..."><method name="..."><counter type="INSTRUCTION" missed="0" covered="..."/></method></class></package></report>
    for package in root.findall('package'):
        pkg_name = package.get('name')
        for cls in package.findall('class'):
            cls_name = cls.get('name')
            for m in cls.findall('method'):
                mname = m.get('name')
                # find counters
                for counter in m.findall('counter'):
                    ctype = counter.get('type')
                    missed = int(counter.get('missed'))
                    covered = int(counter.get('covered'))
                    if missed > 0:
                        uncovered.append((pkg_name, cls_name, mname, ctype, missed, covered))
    if not uncovered:
        print("No uncovered methods found in JaCoCo XML (good coverage or no instrumentation).")
        return 0
    print("Uncovered code segments (method-level):")
    for pkg, cls, mname, ctype, missed, covered in uncovered:
        print(f" - {pkg}.{cls}#{mname} : {ctype} missed={missed} covered={covered}")
    print("\nRecommendations:")
    print(" - Add focused unit tests that call these methods with representative inputs.")
    print(" - For branches, add tests that exercise both true/false paths.")
    print(" - If methods are hard to test, consider extracting logic to smaller testable units.")
    return 0


if __name__ == '__main__':
    raise SystemExit(analyze())
