#!/usr/bin/env python3
"""
Parse common JaCoCo XML locations and print uncovered methods/classes.
"""
import xml.etree.ElementTree as ET
from pathlib import Path

POSSIBLE = [Path('target/site/jacoco/jacoco.xml'), Path('target/jacoco-report/jacoco.xml')]

def find_xml():
    for p in POSSIBLE:
        if p.exists():
            return p
    return None

def analyze(p):
    tree = ET.parse(p)
    root = tree.getroot()
    uncovered = []
    for package in root.findall('package'):
        pkg = package.get('name')
        for cls in package.findall('class'):
            clsn = cls.get('name')
            for m in cls.findall('method'):
                mname = m.get('name')
                for counter in m.findall('counter'):
                    missed = int(counter.get('missed'))
                    covered = int(counter.get('covered'))
                    if missed > 0:
                        uncovered.append((pkg, clsn, mname, counter.get('type'), missed, covered))
    if not uncovered:
        print('No uncovered methods found in', p)
        return 0
    print('Uncovered code segments (method-level):')
    for pkg, cls, mname, ctype, missed, covered in uncovered:
        print(f' - {pkg}.{cls}#{mname} : {ctype} missed={missed} covered={covered}')
    return 0


if __name__ == '__main__':
    p = find_xml()
    if not p:
        print('No JaCoCo XML found in expected locations. Run `mvn jacoco:report`.')
        raise SystemExit(2)
    raise SystemExit(analyze(p))
