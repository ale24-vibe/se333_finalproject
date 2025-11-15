#!/usr/bin/env python3
"""
automation_runner.py - non-interactive git automation helper

Usage examples (PowerShell):
    python .\tools\automation_runner.py --file .autocommit --message "chore: automated" --push --branch auto/runner
    python .\tools\automation_runner.py --file README.md --message "docs: touch" 

This script appends content (or a timestamped line) to a file, stages, commits,
and optionally pushes to a remote branch non-interactively.
"""

import argparse
import subprocess
import sys
import os
import datetime
import json


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return {"rc": p.returncode, "out": p.stdout, "err": p.stderr}


def get_current_branch():
    p = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True)
    return p.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description="Non-interactive git commit/push helper")
    parser.add_argument("--file", dest="file", required=True, help="File to create/append")
    parser.add_argument("--message", dest="message", required=True, help="Commit message")
    parser.add_argument("--content", dest="content", default=None, help="Content to append (default: timestamp line)")
    parser.add_argument("--push", dest="push", action="store_true", help="Push after commit (sets upstream if needed)")
    parser.add_argument("--branch", dest="branch", default=None, help="Branch to create/checkout before changes")
    parser.add_argument("--remote", dest="remote", default="origin", help="Remote name for push (default: origin)")
    args = parser.parse_args()

    # Optionally create or checkout branch
    if args.branch:
        rc = run(["git", "checkout", "-b", args.branch])
        if rc["rc"] != 0:
            rc = run(["git", "checkout", args.branch])
            if rc["rc"] != 0:
                print(json.dumps({"success": False, "step": "checkout", "detail": rc}))
                sys.exit(1)

    # Prepare content
    if args.content is None:
        args.content = f"autocommit: {datetime.datetime.utcnow().isoformat()}\n"

    # Ensure directory exists
    file_dir = os.path.dirname(args.file)
    if file_dir:
        os.makedirs(file_dir, exist_ok=True)

    # Append to file
    try:
        with open(args.file, "a", encoding="utf-8") as f:
            f.write(args.content)
    except Exception as e:
        print(json.dumps({"success": False, "step": "write", "error": str(e)}))
        sys.exit(1)

    # Stage
    st = run(["git", "add", args.file])
    if st["rc"] != 0:
        print(json.dumps({"success": False, "step": "add", "detail": st}))
        sys.exit(1)

    # Commit
    cm = run(["git", "commit", "-m", args.message])
    if cm["rc"] != 0:
        print(json.dumps({"success": False, "step": "commit", "detail": cm}))
        sys.exit(1)

    result = {"success": True, "commit": cm}

    # Push if requested
    if args.push:
        branch = args.branch or get_current_branch()
        psh = run(["git", "push", "-u", args.remote, branch])
        result["push"] = psh
        if psh["rc"] != 0:
            result["push_failed"] = True

    print(json.dumps(result))


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
automation_runner.py - non-interactive git automation helper

Usage examples (PowerShell):
    python .\tools\automation_runner.py --file .autocommit --message "chore: automated" --push --branch auto/runner
    python .\tools\automation_runner.py --file README.md --message "docs: touch" 

This script appends content (or a timestamped line) to a file, stages, commits,
and optionally pushes to a remote branch non-interactively.
"""

import argparse
import subprocess
import sys
import os
import datetime
import json


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return {"rc": p.returncode, "out": p.stdout, "err": p.stderr}


def get_current_branch():
    p = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True)
    return p.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description="Non-interactive git commit/push helper")
    parser.add_argument("--file", dest="file", required=True, help="File to create/append")
    parser.add_argument("--message", dest="message", required=True, help="Commit message")
    parser.add_argument("--content", dest="content", default=None, help="Content to append (default: timestamp line)")
    parser.add_argument("--push", dest="push", action="store_true", help="Push after commit (sets upstream if needed)")
    parser.add_argument("--branch", dest="branch", default=None, help="Branch to create/checkout before changes")
    parser.add_argument("--remote", dest="remote", default="origin", help="Remote name for push (default: origin)")
    args = parser.parse_args()

    # Optionally create or checkout branch
    if args.branch:
        rc = run(["git", "checkout", "-b", args.branch])
        if rc["rc"] != 0:
            rc = run(["git", "checkout", args.branch])
            if rc["rc"] != 0:
                print(json.dumps({"success": False, "step": "checkout", "detail": rc}))
                sys.exit(1)

    # Prepare content
    if args.content is None:
        args.content = f"autocommit: {datetime.datetime.utcnow().isoformat()}\n"

    # Ensure directory exists
    file_dir = os.path.dirname(args.file)
    if file_dir:
        os.makedirs(file_dir, exist_ok=True)

    # Append to file
    try:
        with open(args.file, "a", encoding="utf-8") as f:
            f.write(args.content)
    except Exception as e:
        print(json.dumps({"success": False, "step": "write", "error": str(e)}))
        sys.exit(1)

    # Stage
    st = run(["git", "add", args.file])
    if st["rc"] != 0:
        print(json.dumps({"success": False, "step": "add", "detail": st}))
        sys.exit(1)

    # Commit
    cm = run(["git", "commit", "-m", args.message])
    if cm["rc"] != 0:
        print(json.dumps({"success": False, "step": "commit", "detail": cm}))
        sys.exit(1)

    result = {"success": True, "commit": cm}

    # Push if requested
    if args.push:
        branch = args.branch or get_current_branch()
        psh = run(["git", "push", "-u", args.remote, branch])
        result["push"] = psh
        if psh["rc"] != 0:
            result["push_failed"] = True

    print(json.dumps(result))


if __name__ == "__main__":
    main()
