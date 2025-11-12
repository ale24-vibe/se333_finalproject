#!/usr/bin/env python3
"""
Small helper to run Maven tests and report status. Intended to be run from project root.
"""
import subprocess
import sys

def main():
    cmd = ["mvn", "-U", "clean", "test"]
    print("Running: ", " ".join(cmd))
    p = subprocess.run(cmd)
    sys.exit(p.returncode)

if __name__ == '__main__':
    main()
