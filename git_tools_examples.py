"""
Direct-import examples that call the git tools via `server`.
Non-destructive by default.
"""
from pprint import pprint

import server

if __name__ == '__main__':
    print("Calling git_status()... (using .fn to invoke underlying function)")
    try:
        status = server.git_status.fn()
        pprint(status)
    except Exception as e:
        print("git_status() raised:", e)

    print("\nCalling git_add_all() (non-destructive default)...")
    try:
        res = server.git_add_all.fn()
        pprint(res)
    except Exception as e:
        print("git_add_all() raised:", e)

    print("\nCalling git_commit() (will fail if nothing staged)...")
    try:
        commit = server.git_commit.fn("feat: example commit", coverage_stats={"line_coverage": "0%"})
        pprint(commit)
    except Exception as e:
        print("git_commit() raised:", e)

    print("\nCalling automated_workflow() (create_pr=False to avoid PRs)")
    try:
        wf = server.automated_workflow.fn(
            commit_message="chore: automated test",
            push_remote="origin",
            create_pr=False,
            coverage_stats={"line_coverage": "0%"}
        )
        pprint(wf)
    except Exception as e:
        print("automated_workflow() raised:", e)
